"""
Master Query Pipeline - Unified Entry Point
============================================

The Master Pipeline orchestrates ALL the advanced features:
1. RAG Routing - Selects best RAG strategy
2. Self-RAG - Self-reflective retrieval
3. Meta-Cognition - Validates response quality
4. Orchestrator - Coordinates agents
5. Visualization - Smart chart selection

This is the SINGLE entry point for processing user queries.
Integrates everything we've built with FREE APIs.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from core.llm import chat, embed_text
from core.rag_router import route_query, RAGStrategy
from core.self_rag import SelfRAG
from agents.meta_cognition import MetaCognitionAgent
from agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Complete result from the master pipeline"""
    answer: str
    confidence: float
    chart: Optional[Dict[str, Any]]
    sources: List[str]
    rag_strategy: str
    validation: Dict[str, Any]
    execution_time: float
    metadata: Dict[str, Any]


class MasterQueryPipeline:
    """
    The unified query processing pipeline.
    
    Brings together all advanced features:
    - Intelligent RAG routing
    - Self-reflective generation
    - Quality validation
    - Smart visualization
    
    All using FREE APIs (Groq/Gemini).
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.self_rag = SelfRAG()
        self.meta_cognition = MetaCognitionAgent()
        self.orchestrator = OrchestratorAgent()
    
    async def process(
        self,
        query: str,
        context: str = "",
        documents: List[Dict[str, Any]] = None,
        retrieval_fn = None,
        df = None,
        prefer_speed: bool = False,
        prefer_quality: bool = False,
        generate_chart: bool = True
    ) -> QueryResult:
        """
        Process a query through the full pipeline.
        
        Args:
            query: User's question
            context: Pre-existing context (optional)
            documents: Pre-retrieved documents (optional)
            retrieval_fn: Function to retrieve more docs (optional)
            df: DataFrame for visualization (optional)
            prefer_speed: Optimize for speed
            prefer_quality: Optimize for quality
            generate_chart: Whether to generate visualizations
            
        Returns:
            QueryResult with answer, confidence, chart, and metadata
        """
        
        start_time = datetime.now()
        logger.info(f"Master Pipeline: Processing query: {query[:50]}...")
        
        # Step 1: Route to best RAG strategy
        routing = route_query(
            query,
            context_available=bool(context or documents),
            prefer_speed=prefer_speed,
            prefer_quality=prefer_quality
        )
        
        logger.info(f"Master Pipeline: Selected strategy: {routing.strategy.value}")
        
        # Step 2: Execute based on strategy
        if routing.strategy == RAGStrategy.SELF_RAG or prefer_quality:
            # Use Self-RAG for high-quality responses
            rag_result = await self.self_rag.run(
                query=query,
                documents=documents,
                retrieval_fn=retrieval_fn,
                existing_context=context
            )
            answer = rag_result.answer
            sources = [str(d.get("text", ""))[:100] for d in rag_result.documents_used]
            initial_confidence = rag_result.confidence
            
        elif routing.strategy == RAGStrategy.AGENTIC:
            # Use orchestrator for complex tasks
            result = await self.orchestrator.run(query, context)
            answer = result["response"]
            sources = []
            initial_confidence = 0.8
            
        else:
            # Basic RAG for simple queries
            answer = await self._basic_rag(query, context, documents)
            sources = []
            initial_confidence = 0.7
        
        # Step 3: Validate response with Meta-Cognition
        validation = await self.meta_cognition.validate(
            response=answer,
            context=context,
            query=query
        )
        
        # Adjust confidence based on validation
        final_confidence = validation.overall_quality
        
        # Step 4: Refine if needed
        if self.meta_cognition.should_refine(validation):
            logger.info("Master Pipeline: Refining response based on validation")
            answer = await self._refine_response(
                answer, 
                validation.suggestions, 
                query, 
                context
            )
            # Re-validate
            validation = await self.meta_cognition.validate(answer, context, query)
            final_confidence = validation.overall_quality
        
        # Step 5: Generate visualization if requested
        chart = None
        if generate_chart and df is not None:
            chart = await self._generate_chart(query, df)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResult(
            answer=answer,
            confidence=final_confidence,
            chart=chart,
            sources=sources,
            rag_strategy=routing.strategy.value,
            validation={
                "quality": validation.overall_quality,
                "hallucinations": validation.hallucination_severity.value,
                "summary": self.meta_cognition.get_validation_summary(validation)
            },
            execution_time=execution_time,
            metadata={
                "routing_confidence": routing.confidence,
                "routing_reasoning": routing.reasoning,
                "iterations": getattr(validation, 'iterations', 1),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _basic_rag(
        self,
        query: str,
        context: str,
        documents: List[Dict[str, Any]] = None
    ) -> str:
        """Simple RAG for basic queries"""
        
        doc_context = ""
        if documents:
            doc_context = "\n\n".join([
                d.get("text", str(d))[:1000] 
                for d in documents[:3]
            ])
        
        full_context = f"{context}\n\n{doc_context}".strip()
        
        prompt = f"""Answer this question using the provided context.
Be concise and data-driven. Only use facts from the context.

CONTEXT:
{full_context[:4000]}

QUESTION: {query}

ANSWER:"""

        try:
            answer = chat(prompt, temperature=0.3)
            return answer.strip()
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    async def _refine_response(
        self,
        response: str,
        suggestions: List[str],
        query: str,
        context: str
    ) -> str:
        """Refine response based on validation suggestions"""
        
        prompt = f"""Improve this response based on the suggestions.

ORIGINAL QUERY: {query}

CURRENT RESPONSE: {response}

SUGGESTIONS FOR IMPROVEMENT:
{chr(10).join(f"- {s}" for s in suggestions)}

CONTEXT FOR VERIFICATION:
{context[:2000]}

IMPROVED RESPONSE:"""

        try:
            refined = chat(prompt, temperature=0.2)
            return refined.strip()
        except Exception as e:
            logger.warning(f"Error refining: {e}")
            return response
    
    async def _generate_chart(
        self,
        query: str,
        df
    ) -> Optional[Dict[str, Any]]:
        """Generate appropriate visualization"""
        
        try:
            # Import here to avoid circular dependency
            from agents.smart_chart import smart_chart
            
            result = smart_chart(query, df)
            if result and not result.get("error"):
                return result
            
        except Exception as e:
            logger.warning(f"Chart generation error: {e}")
        
        return None


# Global pipeline instance
_pipeline = None

def get_pipeline(user_id: str = "default") -> MasterQueryPipeline:
    """Get or create the pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = MasterQueryPipeline(user_id)
    return _pipeline


async def process_query(
    query: str,
    context: str = "",
    documents: List[Dict] = None,
    df = None,
    quick: bool = False
) -> Dict[str, Any]:
    """
    Simple interface to process a query.
    
    Returns dict with answer, confidence, chart, etc.
    """
    
    pipeline = get_pipeline()
    
    result = await pipeline.process(
        query=query,
        context=context,
        documents=documents,
        df=df,
        prefer_speed=quick,
        generate_chart=df is not None
    )
    
    return {
        "answer": result.answer,
        "confidence": result.confidence,
        "chart": result.chart,
        "sources": result.sources,
        "strategy": result.rag_strategy,
        "validation": result.validation,
        "execution_time": f"{result.execution_time:.2f}s"
    }


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        context = """
        Q4 2024 Financial Report
        Revenue: $2.5 million (up 15% from Q3)
        Expenses: $1.8 million
        Net Profit: $700,000
        Customers: 1,250
        Churn Rate: 3.2%
        """
        
        documents = [
            {"text": "Q4 revenue was $2.5M, a 15% increase from Q3."},
            {"text": "Customer count grew to 1,250 with 3.2% churn rate."},
        ]
        
        result = await process_query(
            query="What was the Q4 revenue and how did it compare to Q3?",
            context=context,
            documents=documents
        )
        
        print("=== RESULT ===")
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Strategy: {result['strategy']}")
        print(f"Time: {result['execution_time']}")
        print(f"\nValidation:\n{result['validation']['summary']}")
    
    asyncio.run(test())
