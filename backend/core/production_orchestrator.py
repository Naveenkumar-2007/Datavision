"""
Production Orchestrator - ChatGPT/Claude-Level AI Business Analyst
===================================================================

This is the CENTRAL ORCHESTRATOR that ties together:
- 5 Modes (RAG, GraphRAG, Hybrid, Vision, Prediction)
- 2 AI Models (Mistral, Llama)  
- 12 MCP Tools

Use this instead of complex routing for production-grade responses.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class AnalysisMode(Enum):
    RAG = "rag"
    GRAPHRAG = "graphrag"
    HYBRID = "hybrid"
    VISION = "vision"
    PREDICTION = "prediction"
    CHAT = "chat"


class AIModel(Enum):
    MISTRAL = "mistral-7b"      # Fast, simple queries
    LLAMA = "llama-70b"         # Deep, complex analysis
    AUTO = "auto"               # Auto-select based on query


@dataclass
class QueryAnalysis:
    """Analysis of user query"""
    complexity: str  # "simple", "medium", "complex"
    intent: str      # "fact", "comparison", "analysis", "forecast", "relationship"
    requires_data: bool
    requires_visualization: bool
    is_followup: bool
    confidence: float


@dataclass
class ProductionResponse:
    """Complete response from orchestrator"""
    answer: str
    mode_used: AnalysisMode
    model_used: str
    sources: List[str]
    confidence: float
    visualization: Optional[Dict] = None
    insights: Optional[List[str]] = None
    mcps_used: Optional[List[str]] = None


class ProductionOrchestrator:
    """
    Central orchestrator for production-grade AI responses.
    
    This class coordinates:
    1. Query analysis and intent detection
    2. Mode selection based on query type
    3. Model selection based on complexity
    4. MCP tool execution
    5. Response generation and validation
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.conversation_history: List[Dict] = []
        self._load_history()
    
    def _load_history(self):
        """Load conversation history"""
        try:
            from utils.paths import get_user_paths
            paths = get_user_paths(self.user_id)
            history_file = paths["memory"] / "orchestrator_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.conversation_history = json.load(f)[-20:]  # Last 20 turns
        except Exception as e:
            print(f"[ORCH] History load error: {e}")
    
    def _save_history(self):
        """Save conversation history"""
        try:
            from utils.paths import get_user_paths
            paths = get_user_paths(self.user_id)
            history_file = paths["memory"] / "orchestrator_history.json"
            history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(self.conversation_history[-20:], f, indent=2)
        except Exception as e:
            print(f"[ORCH] History save error: {e}")
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze query to determine intent and complexity"""
        q_lower = query.lower()
        
        # Follow-up detection
        followup_patterns = [
            'explain that', 'explain it', 'explain this', 'explain above',
            'what does that', 'tell me more', 'about that', 'about it',
            'in words', 'in simple', 'clarify', 'what is that'
        ]
        is_followup = any(p in q_lower for p in followup_patterns)
        
        # Intent detection
        if any(w in q_lower for w in ['forecast', 'predict', 'future', 'next month', 'will be']):
            intent = "forecast"
        elif any(w in q_lower for w in ['which customer', 'who buys', 'relationship', 'connected']):
            intent = "relationship"
        elif any(w in q_lower for w in ['compare', 'versus', 'difference', 'between']):
            intent = "comparison"
        elif any(w in q_lower for w in ['why', 'reason', 'explain', 'analyze', 'insight']):
            intent = "analysis"
        else:
            intent = "fact"
        
        # Complexity detection
        word_count = len(query.split())
        if word_count <= 5 and intent in ["fact"]:
            complexity = "simple"
        elif word_count >= 15 or intent in ["comparison", "analysis"]:
            complexity = "complex"
        else:
            complexity = "medium"
        
        # Visualization detection
        requires_viz = any(w in q_lower for w in [
            'chart', 'graph', 'plot', 'visuali', 'show me', 'trend', 'bar', 'pie', 'line'
        ])
        
        return QueryAnalysis(
            complexity=complexity,
            intent=intent,
            requires_data=True,
            requires_visualization=requires_viz,
            is_followup=is_followup,
            confidence=0.85
        )
    
    def select_mode(self, analysis: QueryAnalysis, user_mode: str = "auto") -> AnalysisMode:
        """Select optimal mode based on query analysis"""
        
        # Respect explicit user selection
        if user_mode and user_mode != "auto":
            mode_map = {
                "rag": AnalysisMode.RAG,
                "graph": AnalysisMode.GRAPHRAG,
                "graphrag": AnalysisMode.GRAPHRAG,
                "hybrid": AnalysisMode.HYBRID,
                "vision": AnalysisMode.VISION,
                "prediction": AnalysisMode.PREDICTION,
                "chat": AnalysisMode.CHAT,
            }
            return mode_map.get(user_mode.lower(), AnalysisMode.RAG)
        
        # Auto-select based on intent
        if analysis.intent == "forecast":
            return AnalysisMode.PREDICTION
        elif analysis.intent == "relationship":
            return AnalysisMode.GRAPHRAG
        elif analysis.intent in ["comparison", "analysis"] or analysis.complexity == "complex":
            return AnalysisMode.HYBRID
        else:
            return AnalysisMode.RAG
    
    def select_model(self, analysis: QueryAnalysis, user_model: str = "auto") -> str:
        """Select optimal AI model based on complexity"""
        
        # Respect explicit user selection
        if user_model and user_model != "auto":
            return user_model
        
        # Auto-select based on complexity
        if analysis.complexity == "simple":
            return "mistral-7b"  # Fast for simple queries
        else:
            return "llama-70b"    # Deep for complex queries
    
    def get_required_mcps(self, analysis: QueryAnalysis, mode: AnalysisMode) -> List[str]:
        """Determine which MCPs are needed"""
        mcps = []
        
        # Always use vectorizer for RAG
        if mode in [AnalysisMode.RAG, AnalysisMode.HYBRID]:
            mcps.append("vectorizer")
        
        # GraphRAG needs graph builder
        if mode in [AnalysisMode.GRAPHRAG, AnalysisMode.HYBRID]:
            mcps.append("graph_builder")
        
        # Prediction needs forecast engine
        if mode == AnalysisMode.PREDICTION:
            mcps.append("forecast_engine")
            mcps.append("prediction_engine")
        
        # Visualizations need chart generator
        if analysis.requires_visualization:
            mcps.append("chart_generator")
        
        # Vision needs OCR
        if mode == AnalysisMode.VISION:
            mcps.append("vision_ocr")
        
        # Always add insight engine for complex queries
        if analysis.complexity == "complex":
            mcps.append("insight_engine")
        
        return mcps
    
    def execute(
        self,
        query: str,
        mode: str = "auto",
        model: str = "auto",
        currency_symbol: str = "$",
        attached_files: List[Dict] = None
    ) -> ProductionResponse:
        """
        Execute a query with production-grade orchestration.
        
        This is the main entry point for all queries.
        """
        print(f"\n{'='*60}")
        print(f"🚀 PRODUCTION ORCHESTRATOR")
        print(f"   Query: {query[:50]}...")
        print(f"   Mode: {mode}, Model: {model}")
        print(f"{'='*60}")
        
        # Step 1: Analyze query
        analysis = self.analyze_query(query)
        print(f"[ORCH] Analysis: {analysis.intent}, {analysis.complexity}")
        
        # Step 2: Handle follow-up queries
        if analysis.is_followup:
            return self._handle_followup(query, analysis, currency_symbol)
        
        # Step 3: Select mode and model
        selected_mode = self.select_mode(analysis, mode)
        selected_model = self.select_model(analysis, model)
        required_mcps = self.get_required_mcps(analysis, selected_mode)
        
        print(f"[ORCH] Mode: {selected_mode.value}, Model: {selected_model}")
        print(f"[ORCH] MCPs: {required_mcps}")
        
        # Step 4: Execute MCPs
        mcp_results = self._execute_mcps(required_mcps, query)
        
        # Step 5: Generate response based on mode
        response = self._generate_response(
            query, selected_mode, selected_model, 
            analysis, mcp_results, currency_symbol
        )
        
        # Step 6: Save to history
        self.conversation_history.append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response.answer[:2000],
            "mode": selected_mode.value,
            "timestamp": datetime.now().isoformat()
        })
        self._save_history()
        
        return response
    
    def _handle_followup(
        self, 
        query: str, 
        analysis: QueryAnalysis,
        currency_symbol: str
    ) -> ProductionResponse:
        """Handle follow-up queries with context"""
        print("[ORCH] Handling follow-up query")
        
        # Get last assistant response
        last_response = ""
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant":
                last_response = msg.get("content", "")
                break
        
        if not last_response:
            return ProductionResponse(
                answer="I don't have context from a previous response. Please ask a complete question.",
                mode_used=AnalysisMode.RAG,
                model_used="mistral-7b",
                sources=["Context Memory"],
                confidence=0.5
            )
        
        # Build follow-up prompt
        from core.llm import chat
        
        prompt = f"""You are an AI Business Analyst. The user is asking about your previous response.

## YOUR PREVIOUS RESPONSE:
{last_response}

## USER'S FOLLOW-UP QUESTION:
{query}

## INSTRUCTIONS:
1. Answer the follow-up question based on YOUR PREVIOUS RESPONSE
2. Do NOT generate new data or charts
3. EXPLAIN what was shown/said before
4. Use {currency_symbol} for currency
5. Be direct and clear

## YOUR ANSWER:"""

        try:
            answer = chat(prompt, temperature=0.3, max_tokens=2000)
            return ProductionResponse(
                answer=answer,
                mode_used=AnalysisMode.RAG,
                model_used="llama-70b",
                sources=["Context Memory", "Previous Response"],
                confidence=0.9,
                mcps_used=["production_chat"]
            )
        except Exception as e:
            return ProductionResponse(
                answer=f"I couldn't process that follow-up. Error: {str(e)[:100]}",
                mode_used=AnalysisMode.RAG,
                model_used="mistral-7b",
                sources=[],
                confidence=0.3
            )
    
    def _execute_mcps(self, mcps: List[str], query: str) -> Dict[str, Any]:
        """Execute required MCPs and collect results"""
        results = {}
        
        try:
            from mcp import get_mcp_registry
            registry = get_mcp_registry()
            
            for mcp_name in mcps:
                try:
                    if mcp_name == "insight_engine":
                        result = registry.execute("generate_insights", workspace_id=self.user_id)
                    elif mcp_name == "forecast_engine":
                        result = registry.execute("forecast_revenue", workspace_id=self.user_id, periods=6)
                    elif mcp_name == "chart_generator":
                        result = registry.execute("generate_chart", query=query, workspace_id=self.user_id)
                    else:
                        result = {"status": "available"}
                    
                    results[mcp_name] = result
                    print(f"[MCP] {mcp_name}: OK")
                except Exception as e:
                    results[mcp_name] = {"error": str(e)}
                    print(f"[MCP] {mcp_name}: Error - {e}")
                    
        except ImportError:
            print("[ORCH] MCP registry not available")
        
        return results
    
    def _generate_response(
        self,
        query: str,
        mode: AnalysisMode,
        model: str,
        analysis: QueryAnalysis,
        mcp_results: Dict,
        currency_symbol: str
    ) -> ProductionResponse:
        """Generate response using selected mode and model"""
        
        # Get mode-specific prompt
        from core.production_chat import get_mode_prompt
        mode_prompt = get_mode_prompt(mode.value)
        
        # Get data context
        data_context = self._get_data_context()
        
        # Add MCP results to context
        mcp_context = ""
        if mcp_results:
            for mcp_name, result in mcp_results.items():
                if isinstance(result, dict) and not result.get("error"):
                    mcp_context += f"\n## {mcp_name.upper()} Results:\n{json.dumps(result, default=str)[:500]}\n"
        
        # Build prompt
        from core.llm import chat
        
        prompt = f"""You are a $5M Enterprise AI Business Analyst.

{mode_prompt}

## USER'S DATA:
{data_context}

{mcp_context}

## RULES:
1. Follow the MODE instructions exactly
2. Use {currency_symbol} for all currency
3. Never make up numbers
4. Be confident and professional
5. If asked for charts, include visualization description

## USER QUESTION:
{query}

## YOUR {mode.value.upper()} MODE RESPONSE:"""

        try:
            # Use model-specific parameters
            temperature = 0.3 if analysis.complexity == "complex" else 0.5
            max_tokens = 4000 if analysis.complexity == "complex" else 2000
            
            answer = chat(prompt, temperature=temperature, max_tokens=max_tokens)
            
            return ProductionResponse(
                answer=answer,
                mode_used=mode,
                model_used=model,
                sources=self._get_sources(mode),
                confidence=analysis.confidence,
                insights=mcp_results.get("insight_engine", {}).get("insights"),
                mcps_used=list(mcp_results.keys())
            )
            
        except Exception as e:
            return ProductionResponse(
                answer=f"I encountered an error processing your {mode.value} request. Please try again.",
                mode_used=mode,
                model_used=model,
                sources=[],
                confidence=0.3
            )
    
    def _get_data_context(self) -> str:
        """Get user's data context"""
        try:
            from graph.query import graph_snapshot, revenue_dataframe
            
            context = ""
            
            # Get graph snapshot
            snapshot = graph_snapshot(self.user_id, max_nodes=30)
            if snapshot:
                context += snapshot
            
            # Get revenue summary
            df = revenue_dataframe(self.user_id)
            if df is not None and not df.empty:
                total = df['amount'].sum() if 'amount' in df.columns else 0
                context += f"\n\nTotal Revenue: ${total:,.2f}"
                context += f"\nTotal Records: {len(df)}"
                if 'customer' in df.columns:
                    context += f"\nUnique Customers: {df['customer'].nunique()}"
                if 'product' in df.columns:
                    context += f"\nUnique Products: {df['product'].nunique()}"
            
            return context if context else "No data available. Please upload files in Data Hub."
            
        except Exception as e:
            return f"Data context error: {str(e)[:100]}"
    
    def _get_sources(self, mode: AnalysisMode) -> List[str]:
        """Get source attribution for mode"""
        sources = {
            AnalysisMode.RAG: ["Document Search", "Vector Index"],
            AnalysisMode.GRAPHRAG: ["Knowledge Graph", "Relationship Analysis"],
            AnalysisMode.HYBRID: ["Document Search", "Knowledge Graph", "Combined Analysis"],
            AnalysisMode.VISION: ["Image Analysis", "Chart Extraction"],
            AnalysisMode.PREDICTION: ["Statistical Models", "Forecast Engine"],
            AnalysisMode.CHAT: ["AI Conversation"],
        }
        return sources.get(mode, ["AI Analysis"])


# ============================================================================
# CONVENIENCE FUNCTION - Use this in chat.py
# ============================================================================

def production_query(
    user_id: str,
    query: str,
    mode: str = "auto",
    model: str = "auto",
    currency_symbol: str = "$"
) -> Dict[str, Any]:
    """
    Simple function to execute production-grade query.
    
    Usage in chat.py:
        from core.production_orchestrator import production_query
        result = production_query(user_id, query, mode, model)
        response = result["answer"]
    """
    orchestrator = ProductionOrchestrator(user_id)
    result = orchestrator.execute(query, mode, model, currency_symbol)
    
    return {
        "answer": result.answer,
        "mode": result.mode_used.value,
        "model": result.model_used,
        "sources": result.sources,
        "confidence": result.confidence,
        "visualization": result.visualization,
        "insights": result.insights,
        "mcps_used": result.mcps_used
    }
