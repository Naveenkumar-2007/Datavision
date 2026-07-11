import json
import logging
from typing import Dict
from core.llm import chat

logger = logging.getLogger(__name__)

def route_query(query: str, active_modes: list = None) -> Dict:
    """
    Agentic Orchestrator: Uses a fast LLM to decide the exact route for the user's query.
    Returns a dictionary with routing decision.
    """
    if active_modes is None:
        active_modes = ["chat", "rag", "graph", "vision", "prediction", "hybrid", "chart", "image", "ml_pipeline"]
        
    prompt = f"""You are the Master Orchestrator for an AI Data Analysis Platform.
Your job is to read the user's query and route it to the CORRECT specialized agent.

AVAILABLE ROUTES:
- "chat": For simple greetings, thanking, small talk ("hi", "who are you", "thanks").
- "rag": For specific questions about the data documents ("what is the revenue in Q1?", "who are the top customers?").
- "chart": If the user explicitly asks for a chart, graph, visualization, or plot.
- "image": If the user explicitly asks for an image, img, png, or picture of a dashboard.
- "vision": If the user says something like "look at this image" or "what is in this picture".
- "prediction": If the user asks for a forecast, prediction, or future trend.
- "ml_pipeline": If the user asks to "train a model", "build a model", "predict churn", "run machine learning", etc.
- "etl": If the user asks to "clean data", "generate etl", "fix missing values", or "write python script to clean".

USER QUERY: "{query}"

Determine the best route.
Output ONLY a valid JSON object in this exact format:
{{
    "route": "one_of_the_routes_above",
    "confidence": 95,
    "reason": "Brief explanation why"
}}
"""
    try:
        # Use a fast, reliable model for orchestration (e.g., Llama 3 8B)
        # Using temperature=0.1 for deterministic routing
        response = chat(prompt, temperature=0.1, max_tokens=150)
        
        # Parse JSON
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
            
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            response = response[start:end]
            
        decision = json.loads(response)
        
        # Validate route
        valid_routes = ["chat", "rag", "graph", "vision", "prediction", "hybrid", "chart", "image", "etl", "ml_pipeline"]
        if decision.get("route") not in valid_routes:
            decision["route"] = "rag"  # fallback
            
        logger.info(f"Orchestrator routed '{query}' -> {decision['route']} (Confidence: {decision.get('confidence')}%)")
        return decision
        
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        # Fallback logic if LLM routing fails
        query_lower = query.lower()
        if any(kw in query_lower for kw in ['img', 'image', 'picture', 'dashboard']):
            return {"route": "image", "confidence": 50, "reason": "Fallback: Keyword match"}
        if any(kw in query_lower for kw in ['chart', 'graph', 'plot', 'visualize', 'trend']):
            return {"route": "chart", "confidence": 50, "reason": "Fallback: Keyword match"}
        if any(kw in query_lower for kw in ['predict', 'forecast', 'future']):
            return {"route": "prediction", "confidence": 50, "reason": "Fallback: Keyword match"}
        if any(kw in query_lower for kw in ['clean', 'fix', 'etl', 'python script to clean']):
            return {"route": "etl", "confidence": 50, "reason": "Fallback: Keyword match"}
        if any(kw in query_lower for kw in ['hi', 'hello', 'hey', 'thanks', 'bye']):
            return {"route": "chat", "confidence": 50, "reason": "Fallback: Keyword match"}
            
        return {"route": "rag", "confidence": 50, "reason": "Fallback: Default route"}
