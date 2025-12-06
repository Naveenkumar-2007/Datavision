# Enterprise Agent Nodes - Clean Output Design
"""
4 Analysis Modes: RAG, GraphRAG, Hybrid, Vision

Clean, focused outputs based on trained data.
No verbose metadata - just actionable insights.
"""
from core.llm import chat
from vector.retriever import retrieve
from graph.query import query_graph, revenue_dataframe
from agents.state import AgentState
import time


def _get_user_context(user_id: str) -> str:
    """Get personalized context for user"""
    try:
        from core.memory import get_user_context
        return get_user_context(user_id)
    except ImportError:
        return ""
    except Exception as e:
        return ""


def rag_answer(state: AgentState) -> AgentState:
    """
    🟦 RAG MODE - Clean Document-Based Answers
    
    Returns: Direct answers from documents, no verbose metadata
    """
    start_time = time.time()
    question = state.question
    user_id = state.company_id
    
    # Retrieve using hybrid search
    docs = retrieve(question, k=5, user_id=user_id, use_hybrid=True)
    
    if not docs or len(docs) == 0:
        state.answer = """**No Data Found**

Please upload your business files first:
• CSV, Excel, PDF supported
• Include columns: Customer, Product, Sales, Date"""
        state.route = "rag"
        state.sources = []
        return state
    
    # Build context from documents
    context_parts = []
    sources = []
    
    for i, doc in enumerate(docs[:4]):
        doc_text = doc.get('text', str(doc))[:800]
        source = doc.get('source', doc.get('metadata', {}).get('source', ''))
        if source and source not in sources:
            sources.append(source)
        context_parts.append(doc_text)
    
    context = "\n\n".join(context_parts)
    user_context = _get_user_context(user_id)
    
    system_prompt = """You are a business analyst. Answer questions directly using the provided data.

Rules:
- Use ONLY the data provided
- Be specific with numbers and dates
- Use bullet points for clarity
- Keep answers concise and actionable
- If data is insufficient, say so briefly"""
    
    prompt = f"""Question: {question}

Data:
{context}

{user_context}

Provide a clear, direct answer based on the data."""

    answer = chat(prompt, system=system_prompt, max_tokens=1000)
    
    elapsed = time.time() - start_time
    source_text = f"\n\n📄 *Source: {', '.join(sources[:2])}*" if sources else ""
    
    state.answer = f"{answer}{source_text}"
    state.route = "rag"
    state.sources = sources
    
    return state


def graph_answer(state: AgentState) -> AgentState:
    """
    🟧 GRAPHRAG MODE - Clean Graph-Based Analysis
    
    Returns: Insights derived from knowledge graph relationships
    """
    start_time = time.time()
    question = state.question
    user_id = state.company_id
    
    try:
        from graph.query import get_graph_stats, load_graph, get_graph_analysis, revenue_dataframe
        
        graph = load_graph(user_id)
        
        if not graph or graph.number_of_nodes() == 0:
            state.answer = """**No Knowledge Graph Available**

Upload business files to build the graph:
• CSV/Excel with Customer, Product, Amount, Date columns
• Graph will be built automatically"""
            state.route = "graph"
            return state
        
        # Get graph data
        stats = get_graph_stats(user_id)
        graph_data = get_graph_analysis(user_id, question)
        
        # Get revenue data for context
        df = revenue_dataframe(user_id)
        data_summary = ""
        if df is not None and not df.empty:
            amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
            data_summary = f"""
**Data Overview:**
• Total Revenue: ${df[amount_col].sum():,.2f}
• Transactions: {len(df)}
• Customers: {df['customer'].nunique() if 'customer' in df.columns else 'N/A'}
• Products: {df['product'].nunique() if 'product' in df.columns else 'N/A'}"""
        
        # Use LLM to explain the graph analysis
        system_prompt = """You are a business analyst. Explain the data insights clearly and concisely.

Rules:
- Focus on the specific question asked
- Use the provided graph data to answer
- Include specific numbers and percentages
- Format with bullet points for clarity
- Be concise - no fluff"""
        
        prompt = f"""Question: {question}

{graph_data if graph_data else data_summary}

**Graph Structure:**
• Nodes: {stats.get('total_nodes', 0)}
• Relationships: {stats.get('total_edges', 0)}
• Customers: {stats.get('customers', 0)}
• Products: {stats.get('products', 0)}

Provide a clear, data-driven answer based on the knowledge graph."""
        
        answer = chat(prompt, system=system_prompt, max_tokens=800)
        
        # Add graph summary footer
        footer = f"\n\n📊 *Knowledge Graph: {stats.get('total_nodes', 0)} entities, {stats.get('total_edges', 0)} relationships*"
        
        state.answer = f"{answer}{footer}"
        state.route = "graph"
        state.sources = ["Knowledge Graph Analysis"]
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        state.answer = f"**Analysis Error**\n\nCould not analyze graph: {str(e)}"
        state.route = "graph"
    
    return state


def hybrid_answer(state: AgentState) -> AgentState:
    """
    🟪 HYBRID MODE - Combined Document + Graph Analysis
    
    Returns: Comprehensive analysis using both sources
    """
    start_time = time.time()
    question = state.question
    user_id = state.company_id
    
    # Get document context
    docs = retrieve(question, k=3, user_id=user_id, use_hybrid=True)
    doc_context = ""
    sources = []
    
    if docs:
        for doc in docs[:2]:
            doc_context += doc.get('text', '')[:500] + "\n"
            source = doc.get('source', doc.get('metadata', {}).get('source', ''))
            if source and source not in sources:
                sources.append(source)
    
    # Get graph insights
    graph_data = ""
    try:
        from graph.query import get_graph_summary
        graph_data = get_graph_summary(user_id)
    except:
        pass
    
    system_prompt = """You are a senior business analyst. Provide comprehensive analysis combining document facts and data patterns.

Format:
📊 **Key Facts** - Direct data points
📈 **Analysis** - Patterns and trends
💡 **Insights** - Actionable takeaways

Be concise but thorough."""
    
    prompt = f"""Question: {question}

Document Data:
{doc_context if doc_context else "No document data available"}

Business Metrics:
{graph_data if graph_data else "No graph data available"}

Provide a unified analysis."""

    answer = chat(prompt, system=system_prompt, max_tokens=1200)
    
    source_text = f"\n\n📄 *Sources: {', '.join(sources[:2])}*" if sources else ""
    
    state.answer = f"{answer}{source_text}"
    state.route = "hybrid"
    state.sources = sources
    
    return state


def vision_answer(state: AgentState) -> AgentState:
    """
    🟩 VISION MODE - Image Analysis
    
    Returns: Extracted data from images (charts, invoices, etc.)
    """
    start_time = time.time()
    question = state.question
    attached_files = state.context.get("attached_files", [])
    user_id = state.company_id
    
    if not attached_files:
        state.answer = """**No Image Attached**

Drag and drop an image to analyze:
• Charts and graphs
• Invoices and receipts
• Screenshots and documents"""
        state.route = "vision"
        return state
    
    image_files = [f for f in attached_files if f.get('type', '').startswith('image/')]
    
    if not image_files:
        state.answer = """**No Image Files Found**

Please attach image files (JPG, PNG, WebP)."""
        state.route = "vision"
        return state
    
    try:
        from core.vision import analyze_image
        
        image_file = image_files[0]
        image_path = image_file.get('path', '')
        
        analysis = analyze_image(image_path, question)
        
        state.answer = analysis
        state.route = "vision"
        state.sources = [image_file.get('name', 'image')]
        
    except Exception as e:
        state.answer = f"""**Vision Analysis Error**

Could not process image: {str(e)}

Ensure:
• Image is valid (PNG, JPG, WebP)
• Google API key is configured"""
        state.route = "vision"
    
    return state


def fallback_answer(state: AgentState) -> AgentState:
    """Fallback when no data available"""
    state.answer = """**No Data Available**

To get started:
1. Go to **Data Hub**
2. Upload your files (CSV, Excel, PDF)
3. Come back and ask your question

Supported questions:
• "What were total sales?"
• "Who are the top customers?"
• "Show revenue trends" """
    state.route = "fallback"
    return state
