"""
Production-Grade Chat Handler for AI Business Analyst
======================================================

This is a SIMPLIFIED, ROBUST implementation that:
1. Always includes conversation history
2. Always references user's data
3. Works like ChatGPT

Replace complex routing with this clean handler.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class ProductionChatHandler:
    """
    Single, clean handler for all AI chat interactions.
    
    This replaces the complex multi-layer system with something simple
    that actually works.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.history_file = self._get_history_file()
        self.conversation: List[Dict] = self._load_history()
    
    def _get_history_file(self) -> Path:
        """Get the conversation history file path"""
        try:
            from utils.paths import get_user_paths
            paths = get_user_paths(self.user_id)
            return paths["memory"] / "production_chat_history.json"
        except:
            return Path(f"storage/users/{self.user_id}/memory/production_chat_history.json")
    
    def _load_history(self) -> List[Dict]:
        """Load conversation history"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[CHAT] Could not load history: {e}")
        return []
    
    def _save_history(self):
        """Save conversation history"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                # Keep last 50 messages
                json.dump(self.conversation[-50:], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CHAT] Could not save history: {e}")
    
    def add_user_message(self, content: str):
        """Add user message to history"""
        self.conversation.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._save_history()
    
    def add_assistant_message(self, content: str):
        """Add assistant message to history"""
        self.conversation.append({
            "role": "assistant",
            "content": content[:3000],  # Save up to 3000 chars
            "timestamp": datetime.now().isoformat()
        })
        self._save_history()
    
    def get_last_assistant_response(self) -> str:
        """Get the last thing the AI said"""
        for msg in reversed(self.conversation):
            if msg["role"] == "assistant":
                return msg["content"]
        return ""
    
    def get_conversation_for_llm(self, limit: int = 10) -> List[Dict]:
        """Get conversation history formatted for LLM"""
        messages = []
        for msg in self.conversation[-limit:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"][:1000]  # Truncate for token limits
            })
        return messages
    
    def is_followup_query(self, query: str) -> bool:
        """Check if this is a follow-up query"""
        q_lower = query.lower()
        followup_patterns = [
            'explain that', 'explain it', 'explain this', 'explain above',
            'what does that', 'what does it', 'what does this', 'what is that',
            'tell me more', 'more about', 'elaborate', 'clarify',
            'in words', 'in simple', 'in detail', 'meaning of',
            'why is that', 'how is that', 'what about',
            # NEW: Patterns for "explain in one line" type queries
            'in one line', 'in one sentence', 'in two lines', 'in two sentences',
            'shorter version', 'short version', 'summarize above', 'summarize that',
            'one liner', 'one-liner', 'simple terms', 'simpler',
            'layman terms', 'briefly', 'brief version'
        ]
        return any(p in q_lower for p in followup_patterns)
    
    def build_prompt(
        self, 
        query: str, 
        data_context: str,
        currency_symbol: str = "$"
    ) -> str:
        """
        Build the complete prompt for the LLM.
        
        This is the KEY function - it ensures:
        1. Previous conversation is included
        2. Data context is included
        3. Follow-up queries work correctly
        """
        
        # Check if this is a follow-up
        is_followup = self.is_followup_query(query)
        last_response = self.get_last_assistant_response() if is_followup else ""
        
        # Build conversation context
        conv_context = ""
        if self.conversation:
            conv_context = "\n\n## CONVERSATION HISTORY:\n"
            for msg in self.conversation[-6:]:  # Last 6 messages
                role_label = "USER" if msg["role"] == "user" else "AI"
                content = msg["content"][:500]  # Truncate
                conv_context += f"{role_label}: {content}\n\n"
        
        # Build follow-up context - CRITICAL for "explain above" queries
        followup_context = ""
        if is_followup and last_response:
            followup_context = f"""
## ⚠️ CRITICAL - USER IS ASKING ABOUT YOUR PREVIOUS RESPONSE:

The user just said: "{query}"

This refers to YOUR PREVIOUS RESPONSE which was:
---
{last_response[:2000]}
---

INSTRUCTION: 
- The user wants you to explain or simplify what you said above
- Do NOT generate new data or charts
- Do NOT talk about heatmaps, invoices, or revenue unless that was in your previous response
- ONLY explain/rephrase/simplify YOUR PREVIOUS RESPONSE shown above
"""
        
        # Build the complete prompt - UNIVERSAL (no hardcoded domain)
        prompt = f"""You are an AI Data Analyst. Answer questions based on the user's uploaded data.

## USER'S DATA:
{data_context}

{conv_context}

{followup_context}

## RULES:
1. Use ONLY data from USER'S DATA section
2. Use {currency_symbol} for currency values
3. If user says "that/above/it/this" - refer to CONVERSATION HISTORY or YOUR PREVIOUS RESPONSE
4. Be direct and accurate - no filler text
5. Never make up numbers - only use data provided

## CURRENT QUESTION:
{query}

## YOUR RESPONSE:"""
        
        return prompt
    
    def get_response(
        self,
        query: str,
        data_context: str,
        currency_symbol: str = "$"
    ) -> str:
        """
        Get AI response for a query.
        
        This is the main function to call.
        """
        from core.llm import chat
        
        # Add user message to history
        self.add_user_message(query)
        
        # Build prompt with full context
        prompt = self.build_prompt(query, data_context, currency_symbol)
        
        # Log for debugging
        is_followup = self.is_followup_query(query)
        print(f"[CHAT] Query: {query[:50]}...")
        print(f"[CHAT] Is followup: {is_followup}")
        print(f"[CHAT] History size: {len(self.conversation)}")
        
        try:
            # Call LLM with the complete prompt
            response = chat(prompt, temperature=0.3, max_tokens=4000)
            
            # Add response to history
            self.add_assistant_message(response)
            
            print(f"[CHAT] Response length: {len(response)}")
            return response
            
        except Exception as e:
            error_msg = f"I couldn't process that request. Error: {str(e)[:100]}"
            print(f"[CHAT] Error: {e}")
            return error_msg


# ============================================================================
# SIMPLE API FUNCTION - Use this instead of complex routing
# ============================================================================

def simple_chat_response(
    user_id: str,
    query: str,
    data_context: str = "",
    currency_symbol: str = "$"
) -> str:
    """
    Simple, one-function API for getting AI responses.
    
    Usage:
        response = simple_chat_response(
            user_id="user123",
            query="What is total revenue?",
            data_context="Revenue: $629B, Customers: 10",
            currency_symbol="$"
        )
    """
    handler = ProductionChatHandler(user_id)
    return handler.get_response(query, data_context, currency_symbol)


def get_chat_handler(user_id: str) -> ProductionChatHandler:
    """Get a chat handler instance for a user"""
    return ProductionChatHandler(user_id)


# ============================================================================
# MODE-SPECIFIC SYSTEM PROMPTS - Each mode behaves differently
# ============================================================================

MODE_PROMPTS = {
    "rag": """## MODE: RAG (Direct Document Search)
    
BEHAVIOR:
- Give DIRECT answers from the uploaded documents
- Quote specific sources when possible
- Keep responses concise and fact-focused
- Best for: Simple facts, totals, lookups

RESPONSE STYLE:
- Start with the direct answer (bolded)
- Include supporting data in table format
- Cite sources: "According to [filename]..."
""",

    "graph": """## MODE: GraphRAG (Relationship Analysis)
    
BEHAVIOR:
- Analyze RELATIONSHIPS between entities
- Show connections: Customer → Product → Revenue
- Explain patterns across the knowledge graph
- Best for: "Which customers buy X?", comparisons

RESPONSE STYLE:
- Describe relationships and connections
- Use language like "connected to", "linked through", "related via"
- Show multi-hop insights
""",

    "graphrag": """## MODE: GraphRAG (Relationship Analysis)
    
BEHAVIOR:
- Analyze RELATIONSHIPS between entities
- Show connections: Customer → Product → Revenue
- Explain patterns across the knowledge graph

RESPONSE STYLE:
- Describe relationships and connections
- Use language like "connected to", "linked through"
""",

    "hybrid": """## MODE: Hybrid (Deep Comprehensive Analysis)
    
BEHAVIOR:
- Combine document search WITH relationship analysis
- Provide DEEP, multi-perspective insights
- Show both the "what" and the "why"
- Best for: Complex questions, root cause analysis

RESPONSE STYLE:
- Comprehensive, detailed response
- Multiple perspectives on the data
- Include evidence from both sources and graph
""",

    "vision": """## MODE: Vision (Image & Chart Analysis)
    
BEHAVIOR:
- Analyze images, charts, and visualizations
- Extract data points from visual content
- Describe what you see in the image

RESPONSE STYLE:
- Describe visual elements clearly
- Extract numeric data from charts
- Explain trends shown in visuals
""",

    "prediction": """## MODE: Prediction (Forecasting & Scenarios)
    
BEHAVIOR:
- Generate forecasts based on historical data
- Use 3 accuracy tiers: Historical, Statistical, Scenario-based
- Include confidence levels and assumptions

RESPONSE STYLE:
- State predictions with confidence percentages
- List key assumptions
- Show historical basis for forecast
- Include uncertainty ranges
"""
}


def get_mode_prompt(mode: str) -> str:
    """Get the system prompt for a specific mode"""
    return MODE_PROMPTS.get(mode.lower(), MODE_PROMPTS["rag"])


def mode_aware_response(
    user_id: str,
    query: str,
    mode: str,
    data_context: str,
    currency_symbol: str = "$"
) -> str:
    """
    Get AI response with mode-specific behavior.
    
    This ensures each mode behaves according to its specific power:
    - RAG: Direct from sources
    - GraphRAG: Relationships
    - Hybrid: Deep analysis
    - Vision: Images
    - Prediction: Forecasts
    """
    from core.llm import chat
    
    # Get mode-specific prompt
    mode_prompt = get_mode_prompt(mode)
    
    # Build complete prompt
    prompt = f"""You are an AI Data Analyst.

{mode_prompt}

## USER'S DATA:
{data_context}

## RULES:
1. Behave EXACTLY according to the MODE instructions above
2. Use {currency_symbol} for currency
3. Never make up numbers - use only data provided
4. Be confident and professional

## USER QUESTION:
{query}

## YOUR {mode.upper()} MODE RESPONSE:"""

    try:
        response = chat(prompt, temperature=0.3, max_tokens=4000)
        return response
    except Exception as e:
        return f"Error processing {mode} mode request: {str(e)[:100]}"

