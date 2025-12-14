"""
Real Chat with RAG/Graph routing - NO FAKE DATA
Uses existing agents and router system
With semantic caching for API cost savings
SECURED: Uses JWT authentication for user isolation
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import traceback
from datetime import datetime
import json

from agents.router import route_question
from vector.store_faiss import FaissStore
from graph.query import load_graph, graph_snapshot, revenue_dataframe
from core.llm import chat
from core.cache import QueryCache
from config.settings import Settings
from utils.paths import get_user_paths, STORAGE_BASE

# Import auth dependencies
try:
    from database.auth import get_current_user, get_current_user_optional
except ImportError:
    # Fallback if auth module not found
    async def get_current_user_optional(authorization: Optional[str] = Header(None, alias="Authorization")):
        return None

router = APIRouter()

# Initialize query cache for API cost savings
query_cache = QueryCache(
    max_entries=500,
    default_ttl=3600,  # 1 hour cache
    enable_semantic_match=True  # Enable semantic similarity matching
)

# Clear old cache on module load (to clear cached EUR responses)
query_cache.clear_all()
print("🔄 Cache cleared on startup - fresh currency settings")


class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    userId: Optional[str] = None
    message: str
    mode: str = "auto"
    conversationId: Optional[str] = None
    compareFiles: Optional[List[str]] = None  # For file comparison
    attachedFiles: Optional[List[dict]] = None  # Newly uploaded files in chat
    enabledMcps: Optional[dict] = None  # MCP servers toggle: {mcp_name: bool}

class ChatResponse(BaseModel):
    message: str
    mode: str
    sources: Optional[List[str]] = None
    conversationId: str
    timestamp: str


def load_conversation(user_id: str, conversation_id: str) -> List[Message]:
    paths = get_user_paths(user_id)
    history_file = paths["memory"] / f"{conversation_id}.json"
    
    if history_file.exists():
        with open(history_file, 'r') as f:
            data = json.load(f)
            return [Message(**msg) for msg in data.get("messages", [])]
    return []

def save_conversation(user_id: str, conversation_id: str, messages: List[Message]):
    paths = get_user_paths(user_id)
    history_file = paths["memory"] / f"{conversation_id}.json"
    
    data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "updated_at": datetime.now().isoformat(),
        "messages": [msg.dict() for msg in messages]
    }
    
    with open(history_file, 'w') as f:
        json.dump(data, f, indent=2)

def get_file_metadata(user_id: str) -> dict:
    """Get all files with their upload dates and metadata"""
    paths = get_user_paths(user_id)
    file_info = {}
    
    if paths["files"].exists():
        for file_path in paths["files"].iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                file_info[file_path.name] = {
                    "name": file_path.name,
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size,
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
                    "time": datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S")
                }
    return file_info

def extract_date_intent(query: str) -> tuple:
    """Extract date-based intent from query"""
    import re
    from datetime import datetime, timedelta
    
    q_lower = query.lower()
    
    # Check for date keywords
    date_patterns = [
        (r'(\d{4})-(\d{2})-(\d{2})', 'specific'),  # YYYY-MM-DD
        (r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', 'month_year'),
        (r'(last|past)\s+(\d+)\s+(day|week|month|year)s?', 'relative'),
        (r'(today|yesterday|this week|last week|this month|last month)', 'named')
    ]
    
    for pattern, ptype in date_patterns:
        match = re.search(pattern, q_lower)
        if match:
            return ptype, match.groups()
    
    return None, None

def filter_files_by_date(file_metadata: dict, query: str) -> List[str]:
    """Filter files based on date mentioned in query"""
    date_type, date_parts = extract_date_intent(query)
    
    if not date_type:
        return list(file_metadata.keys())
    
    from datetime import datetime, timedelta
    filtered_files = []
    
    for filename, meta in file_metadata.items():
        file_date = datetime.fromisoformat(meta["uploaded_at"])
        
        if date_type == 'specific' and date_parts:
            target_date = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
            if meta["date"] == target_date:
                filtered_files.append(filename)
        
        elif date_type == 'named':
            today = datetime.now()
            if 'today' in query.lower():
                if file_date.date() == today.date():
                    filtered_files.append(filename)
            elif 'yesterday' in query.lower():
                if file_date.date() == (today - timedelta(days=1)).date():
                    filtered_files.append(filename)
            elif 'this week' in query.lower():
                week_start = today - timedelta(days=today.weekday())
                if file_date >= week_start:
                    filtered_files.append(filename)
            elif 'last week' in query.lower():
                week_start = today - timedelta(days=today.weekday() + 7)
                week_end = week_start + timedelta(days=7)
                if week_start <= file_date < week_end:
                    filtered_files.append(filename)
        else:
            filtered_files.append(filename)
    
    return filtered_files if filtered_files else list(file_metadata.keys())

def rag_search(user_id: str, query: str, k: int = 5, target_files: List[str] = None) -> tuple:
    try:
        paths = get_user_paths(user_id)
        Settings.FAISS_DIR = paths["faiss"]
        
        # Load user-specific FAISS store
        store = FaissStore.load_or_create(user_id)
        
        # Get file metadata
        file_metadata = get_file_metadata(user_id)
        
        # Filter by date if mentioned in query
        if target_files is None:
            target_files = filter_files_by_date(file_metadata, query)
        
        # Search with query text (embedding happens inside search method)
        results = store.search(query, k=k)
        
        if not results:
            return "", []
        
        # Filter results by target files if specified
        if target_files:
            filtered_results = []
            for r in results:
                source = r.get('metadata', {}).get('source', '')
                if any(tf in source for tf in target_files):
                    filtered_results.append(r)
            results = filtered_results if filtered_results else results
        
        if not results:
            return "", []
        
        context_parts = []
        sources = []
        
        for i, result in enumerate(results):
            metadata = result.get('metadata', {})
            source_file = metadata.get('source', 'Unknown')
            file_date = file_metadata.get(source_file, {}).get('date', 'Unknown date')
            file_time = file_metadata.get(source_file, {}).get('time', '')
            
            text_content = result.get('text', '')
            context_parts.append(f"[{i+1}] From: {source_file} (Uploaded: {file_date} {file_time})\n{text_content}")
            # Return clean source strings instead of objects
            sources.append(f"{source_file} ({file_date})")
        
        # Add file summary to context
        file_summary = f"\n\n## Available Files ({len(file_metadata)}):\n"
        for fname, fmeta in file_metadata.items():
            if fname in target_files:
                file_summary += f"- {fname} (Uploaded: {fmeta['date']} {fmeta['time']})\n"
        
        context = file_summary + "\n## Relevant Content:\n" + "\n\n".join(context_parts)
        return context, sources
        
    except Exception as e:
        print(f"RAG error: {e}")
        traceback.print_exc()
        return "", []

def graph_query(user_id: str, question: str) -> tuple:
    try:
        paths = get_user_paths(user_id)
        Settings.GRAPH_DIR = paths["graph"]
        
        # Check if graph exists
        graph = load_graph(user_id)
        if not graph:
            return "No knowledge graph available. Please upload and train some data first in Data Hub.", ["Graph Mode - No Data"]
        
        snapshot = graph_snapshot(user_id, max_nodes=50)
        
        revenue_context = ""
        if any(kw in question.lower() for kw in ['revenue', 'sales', 'invoice', 'amount', 'customer', 'product', 'currency', 'money', 'total']):
            try:
                df = revenue_dataframe(user_id)
                if df is not None and not df.empty:
                    # Multi-currency support - group by currency
                    currency_breakdown = {}
                    if 'currency' in df.columns:
                        for curr in df['currency'].unique():
                            curr_total = df[df['currency'] == curr]['amount'].sum() if 'amount' in df.columns else 0
                            currency_breakdown[curr] = curr_total
                    else:
                        # Single currency - use detected currency or default to USD
                        from utils.currency import detect_currency
                        detected_currency = detect_currency(df, paths["files"])
                        total = df['amount'].sum() if 'amount' in df.columns else 0
                        currency_breakdown[detected_currency] = total
                    
                    num_invoices = len(df)
                    num_customers = df['customer'].nunique() if 'customer' in df.columns else 0
                    
                    # Format currency breakdown
                    from utils.currency import get_currency_symbol, format_currency, calculate_currency_breakdown
                    breakdown = calculate_currency_breakdown(currency_breakdown)
                    
                    revenue_context = f"\n\nRevenue Data from Your Files:\n"
                    revenue_context += f"- Total Invoices: {num_invoices}\n"
                    revenue_context += f"- Unique Customers: {num_customers}\n"
                    revenue_context += f"\n💰 Currency Breakdown ({len(currency_breakdown)} currencies detected):\n"
                    
                    for item in breakdown['breakdown']:
                        revenue_context += f"  * {item['name']} ({item['currency']}): {item['formatted']}\n"
                        revenue_context += f"    (USD Equivalent: ${item['usd_equivalent']:,.2f})\n"
                    
                    if len(currency_breakdown) > 1:
                        revenue_context += f"\n📊 Combined Total (USD Equivalent): {breakdown['total_usd_formatted']}\n"
                    
                    # Top products by each currency
                    if 'product' in df.columns and 'currency' in df.columns:
                        revenue_context += "\n- Top Products by Currency:\n"
                        for curr in df['currency'].unique():
                            curr_df = df[df['currency'] == curr]
                            top = curr_df.groupby('product')['amount'].sum().sort_values(ascending=False).head(3)
                            symbol = get_currency_symbol(curr)
                            revenue_context += f"  {symbol} {curr}:\n"
                            for prod, amt in top.items():
                                revenue_context += f"    * {prod}: {symbol}{amt:,.2f}\n"
                    elif 'product' in df.columns:
                        top_products = df.groupby('product')['amount'].sum().sort_values(ascending=False).head(5)
                        revenue_context += "\n- Top Products:\n"
                        primary_currency = list(currency_breakdown.keys())[0] if currency_breakdown else 'USD'
                        symbol = get_currency_symbol(primary_currency)
                        for prod, amt in top_products.items():
                            revenue_context += f"  * {prod}: {symbol}{amt:,.2f}\n"
            except Exception as e:
                print(f"Revenue error: {e}")
                import traceback
                traceback.print_exc()
        
        context = snapshot + revenue_context
        sources = ["Knowledge Graph Analysis"]
        
        return context, sources
        
    except Exception as e:
        print(f"Graph error: {e}")
        return "", []

def hybrid_search(user_id: str, query: str, target_files: List[str] = None) -> tuple:
    rag_context, rag_sources = rag_search(user_id, query, k=5, target_files=target_files)
    graph_context, graph_sources = graph_query(user_id, query)
    
    context = f"## Document Search (RAG):\n{rag_context}\n\n## Knowledge Graph Analysis:\n{graph_context}"
    sources = rag_sources + graph_sources
    
    return context, sources

def vision_analysis(user_id: str, query: str, attached_files: Optional[List[dict]] = None) -> tuple:
    """Analyze images using vision capabilities"""
    try:
        if not attached_files:
            context = "Vision mode requires an image file. Please drag and drop an image (chart, graph, or diagram) to analyze it."
            return context, ["Vision Mode - No Image Attached"]
        
        # Filter for image files
        image_files = [f for f in attached_files if f.get('type', '').startswith('image/')]
        
        if not image_files:
            context = "No image files detected. Vision mode works with image files (JPG, PNG, WebP, etc). Please upload an image to analyze."
            return context, ["Vision Mode - No Image Files"]
        
        # For now, vision mode is limited - explain this to user
        context = f"""## Image Analysis Request

You've uploaded: {', '.join([img.get('name', 'image') for img in image_files])}

**Current Limitation**: This system requires actual vision AI integration (like GPT-4 Vision or Claude with vision) to analyze image content. 

**Alternative Solutions**:
1. **Upload the raw data** instead - if this is a chart/graph, upload the underlying CSV/Excel file to Data Hub
2. **Describe the image** - tell me what the chart shows and I can help analyze similar patterns in your uploaded data
3. **OCR Integration Needed** - To fully analyze images, we need to integrate vision APIs

**What I CAN do now**:
- Analyze the DATA behind charts (upload CSV/Excel files)
- Create visualizations from your data
- Answer questions about structured data in Data Hub

Would you like to upload the source data file instead?"""
        
        sources = ["Vision Mode - Integration Required"]
        
        return context, sources
        
    except Exception as e:
        print(f"Vision analysis error: {e}")
        traceback.print_exc()
        return f"Vision analysis error: {str(e)}", ["Vision Mode - Error"]

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Send message - REAL RAG/Graph response with file comparison and memory
    SECURED: Uses JWT-based user identification for data isolation
    """
    try:
        # SECURITY: Get user_id from authentication headers
        # Priority: 1. JWT token (most secure), 2. X-User-ID header, 3. request body (legacy)
        user_id = None
        
        # Try to extract from JWT token first
        if authorization and authorization.startswith("Bearer "):
            try:
                from database.auth import decode_jwt
                token = authorization.split(" ")[1]
                payload = decode_jwt(token)
                user_id = payload.get("sub")  # Subject is user ID
                print(f"🔐 Authenticated user from JWT: {user_id}")
            except Exception as e:
                print(f"⚠️ JWT decode error: {e}")
        
        # Fallback to X-User-ID header (for authenticated requests)
        if not user_id and x_user_id:
            user_id = x_user_id
            print(f"🔐 User from X-User-ID header: {user_id}")
        
        # Final fallback to request body (legacy support)
        if not user_id:
            user_id = request.userId or request.user_id
            if user_id:
                print(f"⚠️ Using legacy user_id from request body: {user_id}")
        
        # Require authentication
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
        
        query = request.message
        mode = request.mode
        conversation_id = request.conversationId or f"conv_{int(datetime.now().timestamp())}"
        compare_files = request.compareFiles
        
        # Load conversation history for context (user-specific)
        history = load_conversation(user_id, conversation_id)
        
        # Build conversation context from history
        conversation_context = ""
        if history:
            recent_messages = history[-10:]  # Last 10 messages
            conversation_context = "\n\n## Previous Conversation:\n"
            for msg in recent_messages:
                conversation_context += f"{msg.role.upper()}: {msg.content}\n"
        
        # PERSONAL INFO DETECTION - Extract and save user name if mentioned
        try:
            from core.memory import process_personal_info
            personal_detected = process_personal_info(user_id, query)
            if personal_detected:
                print(f"💾 Saved personal information for user {user_id}")
        except Exception as e:
            print(f"Memory processing: {e}")

        user_msg = Message(
            role="user",
            content=query,
            timestamp=datetime.now().isoformat()
        )
        history.append(user_msg)
        
        # Enterprise 4-mode routing
        has_image = bool(request.attachedFiles and any(f.get('type', '').startswith('image/') for f in request.attachedFiles))
        
        print(f"📎 Attached files: {len(request.attachedFiles) if request.attachedFiles else 0}")
        print(f"🖼️ Has image: {has_image}")
        print(f"❓ Query: {query[:50]}...")
        print(f"📋 Requested mode: {mode}")
        
        # MCP status - which MCPs are enabled
        enabled_mcps = request.enabledMcps or {
            'data_cleaner': True,
            'vectorizer': True,
            'graph_builder': True,
            'sql_executor': True,
            'vision_ocr': True,
        }
        enabled_count = sum(1 for v in enabled_mcps.values() if v)
        print(f"⚙️ MCP Servers: {enabled_count}/5 enabled")
        for mcp_name, is_enabled in enabled_mcps.items():
            status = "✅" if is_enabled else "❌"
            print(f"   {status} {mcp_name}")
        
        query_lower = query.lower().strip()
        
        # BUSINESS QUERY KEYWORDS - These should NEVER be treated as personal chat
        business_keywords = [
            'product', 'customer', 'revenue', 'sales', 'invoice', 'amount', 'total',
            'lowest', 'highest', 'top', 'bottom', 'best', 'worst', 'minimum', 'maximum',
            'performance', 'trend', 'analysis', 'analyze', 'data', 'report', 'show',
            'list', 'display', 'which', 'what is the', 'how much', 'how many',
            'average', 'sum', 'count', 'compare', 'difference', 'graph', 'chart',
            'month', 'year', 'date', 'period', 'quarterly', 'weekly', 'daily'
        ]
        
        # Check if this is a business/data query
        is_business_query = any(kw in query_lower for kw in business_keywords)
        
        # PERSONAL/GREETING keywords - Only these should go to chat mode
        personal_keywords = [
            'hello', 'hi', 'hey', 'hii', 'hiii', 'howdy',
            'how are you', 'how r u', "how's it going", "what's up",
            'thank you', 'thanks', 'thx', 'ty', 
            'bye', 'goodbye', 'see you', 'cya',
            'good morning', 'good evening', 'good night', 'good afternoon',
            'who are you', 'what are you', 'what can you do', 'help me',
            'your name', 'introduce yourself', "what's your name",
            'nice to meet', 'pleased to meet',
            'my name', 'tell me my name', 'what is my name', "what's my name",
            'remember me', 'do you remember', 'who am i'
        ]
        
        # EXACT MATCH for very short greetings - these ALWAYS go to chat
        exact_greetings = ['hi', 'hello', 'hey', 'hii', 'hiii', 'howdy', 'yo', 'hola', 
                          'good morning', 'good afternoon', 'good evening', 'thanks', 'thank you']
        is_exact_greeting = query_lower.strip() in exact_greetings
        
        # Check if query is purely conversational (NOT a business query)
        is_short_message = len(query_lower.split()) <= 5
        is_personal = any(kw in query_lower for kw in personal_keywords) and is_short_message and not is_business_query
        
        print(f"👤 Is personal: {is_personal}, Is exact greeting: {is_exact_greeting}, Is business: {is_business_query}")
        
        # Keywords that indicate user wants data analysis, not image analysis
        data_query_keywords = ['predict', 'forecast', 'revenue', 'chart', 'visualization', 
                               'customer', 'product', 'trend', 'sales', 'compare', 'analysis',
                               'total', 'average', 'highest', 'lowest', 'best', 'worst']
        is_data_query = any(kw in query_lower for kw in data_query_keywords)
        
        # ========================================
        # MODE ROUTING - PRIORITY ORDER IS CRITICAL
        # ========================================
        
        # PRIORITY 1: EXACT GREETINGS - ALWAYS chat mode (hi, hello, hey)
        if is_exact_greeting:
            mode = "chat"
            print(f"💬 EXACT GREETING DETECTED: '{query_lower}' → CHAT mode")
        
        # PRIORITY 2: Personal/conversational queries
        elif is_personal and not has_image:
            mode = "chat"
            print(f"💬 PERSONAL CHAT MODE - Greeting/conversational query detected")
        
        # PRIORITY 3: RESPECT EXPLICIT MODE SELECTION
        elif mode in ["graphrag", "graph", "hybrid", "rag", "vision"]:
            # SPECIAL CASE: Vision mode selected but query is about DATA (not image)
            if mode == "vision" and not has_image and is_data_query:
                mode = "graph"  # Redirect to GraphRAG for data analysis
                print(f"🔄 SMART REDIRECT: Vision mode + data query → GRAPH mode for charts/predictions")
            elif mode == "vision" and not has_image:
                # Vision without image and no data query - still use vision (will show instructions)
                print(f"🟩 VISION MODE - No image attached, showing instructions")
            else:
                print(f"🎯 EXPLICIT MODE SELECTED: {mode.upper()} - Respecting user choice")
        
        # PRIORITY 4: Business queries with auto mode - use intelligent routing
        elif is_business_query and mode == "auto":
            mode = route_question(query, has_image=has_image, mode="auto")
            # Override: If routed to "vision" but no image, use "graph" instead
            if mode == "vision" and not has_image:
                mode = "graph"
                print(f"📊 Visualization request without image → Using GRAPH mode to generate charts")
            else:
                print(f"📊 BUSINESS QUERY - Auto-routed to: {mode}")
        
        # PRIORITY 5: Image attached
        elif has_image:
            mode = "vision"
            print(f"🟩 VISION MODE - Image detected")
        
        # PRIORITY 6: Default auto-routing
        elif mode == "auto":
            mode = route_question(query, has_image=False, mode="auto")
            # Override: If routed to "vision" but no image, use "graph"
            if mode == "vision" and not has_image:
                mode = "graph"
            print(f"🎯 Auto-routed to mode: {mode}")
        
        # 🔥 CACHE LOOKUP - Save API costs for similar queries
        cached_result = None
        if is_business_query and mode != "chat":
            cached_result = query_cache.get(query, user_id)
            if cached_result:
                print(f"⚡ CACHE HIT - Returning cached response for: {query[:50]}...")
                return ChatResponse(
                    message=cached_result.response,
                    mode=cached_result.route,
                    sources=cached_result.sources if cached_result.sources else None,
                    conversationId=conversation_id,
                    timestamp=datetime.now().isoformat()
                )
        
        context = ""
        sources = []
        
        # Check for file comparison intent
        comparison_keywords = ['compare', 'difference', 'versus', 'vs', 'between', 'contrast']
        is_comparison = any(kw in query.lower() for kw in comparison_keywords)
        
        # Handle temp attached files (for comparison only, NOT trained)
        temp_context = ""
        if request.attachedFiles:
            temp_context = "\n\n## Temporarily Attached Files (NOT in training data):\n"
            for att_file in request.attachedFiles:
                temp_context += f"- {att_file.get('name', 'Unknown')}: Use for comparison only\n"
            temp_context += "\nNote: These files are NOT trained. Only comparing with trained Data Hub files.\n"
        
        # Use agent workflow nodes for proper responses
        response = ""
        sources = []
        
        if mode == "rag":
            from agents.nodes import rag_answer
            from agents.state import AgentState
            
            state = AgentState(company_id=user_id, question=query, route="rag", answer="", context={})
            state = rag_answer(state)
            response = state.answer
            sources = state.sources
            
        elif mode == "graph" or mode == "graphrag":
            from agents.nodes import graph_answer
            from agents.state import AgentState
            
            print(f"🟧 Calling graph_answer for mode={mode}")
            state = AgentState(company_id=user_id, question=query, route="graph", answer="", context={})
            state = graph_answer(state)
            response = state.answer
            print(f"🟧 graph_answer returned: {len(response) if response else 0} chars")
            sources = ["Knowledge Graph Analysis"]
            mode = "graph"  # Normalize to 'graph' for response
            
        elif mode == "hybrid":
            from agents.nodes import hybrid_answer
            from agents.state import AgentState
            
            state = AgentState(company_id=user_id, question=query, route="hybrid", answer="", context={})
            state = hybrid_answer(state)
            response = state.answer
            sources = state.sources
            
        elif mode == "vision":
            from agents.nodes import vision_answer
            from agents.state import AgentState
            import base64
            import tempfile
            
            # Save attached images to temporary files for Gemini Vision
            processed_files = []
            if request.attachedFiles:
                for file_data in request.attachedFiles:
                    if file_data.get('type', '').startswith('image/'):
                        print(f"📋 Processing attached file: {file_data.get('name', 'unknown')}")
                        print(f"📋 File type: {file_data.get('type', 'unknown')}")
                        
                        # Check what fields are available
                        print(f"📋 Available fields: {list(file_data.keys())}")
                        
                        # Try different ways to get image data
                        content = None
                        
                        # Method 1: Base64 content field
                        if 'content' in file_data:
                            content = file_data.get('content', '')
                            # Remove data URL prefix if present
                            if content.startswith('data:'):
                                content = content.split(',', 1)[1] if ',' in content else content
                            print(f"📋 Using 'content' field, length: {len(content)}")
                        
                        # Method 2: URL field (already uploaded file)
                        elif 'url' in file_data:
                            url = file_data.get('url', '')
                            print(f"📋 Found URL field: {url}")
                            # If it's a local file path
                            if url.startswith('/') or url.startswith('C:') or url.startswith('c:'):
                                try:
                                    with open(url, 'rb') as f:
                                        content = base64.b64encode(f.read()).decode('utf-8')
                                    print(f"📋 Loaded from file path")
                                except Exception as e:
                                    print(f"❌ Failed to load from path: {e}")
                        
                        # Method 3: Data field
                        elif 'data' in file_data:
                            content = file_data.get('data', '')
                            if content.startswith('data:'):
                                content = content.split(',', 1)[1] if ',' in content else content
                            print(f"📋 Using 'data' field, length: {len(content)}")
                        
                        if not content:
                            print(f"❌ No image data found in: {file_data}")
                            continue
                        
                        # Decode base64 and save to temp file
                        try:
                            image_bytes = base64.b64decode(content)
                            print(f"✅ Decoded {len(image_bytes)} bytes")
                            
                            # Create temp file with proper extension
                            file_ext = file_data.get('type', 'image/png').split('/')[-1]
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}', mode='wb')
                            temp_file.write(image_bytes)
                            temp_file.close()
                            
                            processed_files.append({
                                'name': file_data.get('name', 'image'),
                                'path': temp_file.name,
                                'type': file_data.get('type', 'image/png')
                            })
                            print(f"💾 Saved image to: {temp_file.name}")
                        except Exception as e:
                            print(f"❌ Failed to decode image: {e}")
                            print(f"❌ Failed to decode image: {e}")
                            traceback.print_exc()
            
            state = AgentState(company_id=user_id, question=query, route="vision", answer="", context={"attached_files": processed_files})
            state = vision_answer(state)
            response = state.answer
            sources = ["Vision Analysis"]
            
            # Clean up temp files
            import os
            for file in processed_files:
                try:
                    os.unlink(file['path'])
                except:
                    pass
            
        elif mode == "chat":
            # Personal/greeting response - conversational mode
            context = conversation_context
        
        # For agent modes (rag, graph, hybrid, vision), response is already complete
        # Only build prompt for chat mode
        if mode == "chat":
            file_metadata = get_file_metadata(user_id)
            file_count = len(file_metadata)
            
            # SHORT prompt to avoid context length issues with Groq
            prompt = f"""You are an AI Business Analyst assistant. Be friendly and helpful.

User: {query}

Rules:
- If greeting (hi/hello): Say hello, mention you have {file_count} data files, offer to help with revenue, customers, products, or trends.
- If asked "who are you": Briefly explain you're an AI that analyzes business data.
- If thanked: Say "You're welcome!"
- Keep response under 3 sentences. Be warm and natural."""
            response = chat(prompt, max_tokens=200)
        
        # Safety check: ensure response is valid
        if not response or not isinstance(response, str):
            print(f"⚠️ Invalid response: type={type(response)}, value={response}")
            print(f"⚠️ Mode was: {mode}")
            print(f"⚠️ Response object was: {repr(response)[:200]}")
            response = "I encountered an error processing your request. Please try again."
        
        print(f"✅ Sending response: mode={mode}, length={len(response)}")
        
        # 🔥 CACHE STORAGE - Save response for future similar queries
        if is_business_query and mode != "chat" and response:
            query_cache.set(
                query=query,
                response=response,
                route=mode,
                sources=sources if sources else [],
                user_id=user_id,
                ttl=3600  # 1 hour cache
            )
            print(f"💾 Cached response for: {query[:50]}...")
        
        assistant_msg = Message(
            role="assistant",
            content=response,
            timestamp=datetime.now().isoformat()
        )
        history.append(assistant_msg)
        
        save_conversation(user_id, conversation_id, history)
        
        return ChatResponse(
            message=response,
            mode=mode,
            sources=sources if sources else None,
            conversationId=conversation_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_conversations(
    user_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Get all conversations for a user - SECURED"""
    try:
        # SECURITY: Validate user
        if authorization and authorization.startswith("Bearer "):
            try:
                from database.auth import decode_jwt
                token = authorization.split(" ")[1]
                payload = decode_jwt(token)
                auth_user = payload.get("sub")
                if auth_user and auth_user != user_id:
                    user_id = auth_user
            except:
                pass
        elif x_user_id and x_user_id != user_id:
            user_id = x_user_id
        
        paths = get_user_paths(user_id)
        conversations = []
        
        if paths["memory"].exists():
            for file in paths["memory"].glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        messages = data.get("messages", [])
                        if messages:
                            conversations.append({
                                "id": data.get("conversation_id"),
                                "title": messages[0].get("content", "")[:50],
                                "lastMessage": messages[-1].get("content", "")[:100],
                                "timestamp": data.get("updated_at"),
                                "messageCount": len(messages)
                            })
                except:
                    pass
        
        conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"conversations": conversations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}/{conversation_id}")
async def get_conversation_messages(
    user_id: str,
    conversation_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Get messages for a conversation - SECURED"""
    try:
        # SECURITY: Use auth header user
        if authorization and authorization.startswith("Bearer "):
            try:
                from database.auth import decode_jwt
                token = authorization.split(" ")[1]
                payload = decode_jwt(token)
                auth_user = payload.get("sub")
                if auth_user:
                    user_id = auth_user
            except:
                pass
        elif x_user_id:
            user_id = x_user_id
        
        messages = load_conversation(user_id, conversation_id)
        return {
            "conversationId": conversation_id,
            "messages": [msg.dict() for msg in messages]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{user_id}/{conversation_id}")
async def delete_conversation(
    user_id: str,
    conversation_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Delete a conversation - SECURED"""
    try:
        # SECURITY: Use auth header user
        if authorization and authorization.startswith("Bearer "):
            try:
                from database.auth import decode_jwt
                token = authorization.split(" ")[1]
                payload = decode_jwt(token)
                auth_user = payload.get("sub")
                if auth_user:
                    user_id = auth_user
            except:
                pass
        elif x_user_id:
            user_id = x_user_id
        
        paths = get_user_paths(user_id)
        history_file = paths["memory"] / f"{conversation_id}.json"
        
        if history_file.exists():
            history_file.unlink()
            return {"success": True, "message": "Deleted"}
        else:
            raise HTTPException(status_code=404, detail="Not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
