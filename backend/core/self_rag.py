"""
Self-RAG: Self-Reflective Retrieval-Augmented Generation
==========================================================

The most advanced RAG technique that enables the LLM to:
1. DECIDE if retrieval is needed (not always!)
2. EVALUATE retrieved documents for relevance
3. GENERATE response with self-reflection
4. CRITIQUE its own answer for accuracy
5. REFINE if quality is insufficient

Based on: "Self-RAG: Learning to Retrieve, Generate, and Critique" (Asai et al., 2023)

This implementation uses FREE APIs (Groq/Gemini) for all LLM calls.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Use the existing LLM module (free Groq/Gemini)
from core.llm import chat

logger = logging.getLogger(__name__)


class RetrievalDecision(Enum):
    """Whether retrieval is needed"""
    RETRIEVE = "retrieve"      # Need to retrieve documents
    NO_RETRIEVE = "no_retrieve"  # Can answer from knowledge
    UNCERTAIN = "uncertain"    # Maybe retrieve


class DocumentRelevance(Enum):
    """Relevance of retrieved document"""
    RELEVANT = "relevant"
    PARTIALLY_RELEVANT = "partially_relevant"
    IRRELEVANT = "irrelevant"


class ResponseQuality(Enum):
    """Quality of generated response"""
    FULLY_SUPPORTED = "fully_supported"      # All claims verified
    PARTIALLY_SUPPORTED = "partially_supported"  # Some claims verified
    NOT_SUPPORTED = "not_supported"          # Claims not in context


@dataclass
class SelfRAGResult:
    """Result from Self-RAG pipeline"""
    answer: str
    retrieval_decision: RetrievalDecision
    documents_used: List[Dict[str, Any]]
    relevance_scores: List[float]
    response_quality: ResponseQuality
    confidence: float
    critique: str
    iterations: int
    

class SelfRAG:
    """
    Self-RAG: The AI decides when to retrieve, evaluates quality,
    and self-corrects its responses.
    
    Uses FREE APIs only (Groq/Gemini via core.llm).
    """
    
    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
        
    async def should_retrieve(self, query: str, context: str = "") -> Tuple[RetrievalDecision, str]:
        """
        Step 1: Decide if retrieval is needed.
        
        The LLM decides whether it can answer from existing context
        or needs to retrieve more information.
        """
        
        prompt = f"""You are a retrieval decision system. Analyze if retrieval is needed.

QUERY: {query}

EXISTING CONTEXT: {context[:2000] if context else "None"}

Decide if retrieval from the knowledge base is needed:
- "retrieve": If the query needs specific data/facts not in context
- "no_retrieve": If the question can be answered from the context or is general
- "uncertain": If you're not sure

Respond with JSON only:
{{"decision": "retrieve" | "no_retrieve" | "uncertain", "reason": "brief explanation"}}"""

        try:
            response = chat(prompt, temperature=0.1)
            
            # Parse JSON response
            response_clean = response.strip()
            if response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1]
                if response_clean.startswith("json"):
                    response_clean = response_clean[4:]
            
            result = json.loads(response_clean)
            decision = RetrievalDecision(result.get("decision", "retrieve"))
            reason = result.get("reason", "")
            
            logger.info(f"Self-RAG retrieval decision: {decision.value} - {reason}")
            return decision, reason
            
        except Exception as e:
            logger.warning(f"Error in retrieval decision: {e}, defaulting to retrieve")
            return RetrievalDecision.RETRIEVE, "Error in decision, defaulting to retrieve"
    
    async def evaluate_relevance(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], DocumentRelevance, float]]:
        """
        Step 2: Evaluate relevance of each retrieved document.
        
        Returns documents with their relevance scores.
        """
        
        if not documents:
            return []
        
        evaluated = []
        
        for doc in documents[:5]:  # Limit to top 5 for efficiency
            doc_text = doc.get("text", doc.get("content", str(doc)))[:1000]
            
            prompt = f"""Evaluate if this document is relevant to the query.

QUERY: {query}

DOCUMENT:
{doc_text}

Rate relevance:
- "relevant": Directly answers or contains key information for the query
- "partially_relevant": Contains some useful information
- "irrelevant": Not useful for answering the query

Respond with JSON:
{{"relevance": "relevant" | "partially_relevant" | "irrelevant", "score": 0.0-1.0, "reason": "brief"}}"""

            try:
                response = chat(prompt, temperature=0.1)
                response_clean = response.strip()
                if response_clean.startswith("```"):
                    response_clean = response_clean.split("```")[1]
                    if response_clean.startswith("json"):
                        response_clean = response_clean[4:]
                
                result = json.loads(response_clean)
                relevance = DocumentRelevance(result.get("relevance", "partially_relevant"))
                score = float(result.get("score", 0.5))
                
                evaluated.append((doc, relevance, score))
                
            except Exception as e:
                logger.warning(f"Error evaluating document: {e}")
                evaluated.append((doc, DocumentRelevance.PARTIALLY_RELEVANT, 0.5))
        
        # Sort by score descending
        evaluated.sort(key=lambda x: x[2], reverse=True)
        
        logger.info(f"Self-RAG evaluated {len(evaluated)} documents")
        return evaluated
    
    async def generate_with_reflection(
        self,
        query: str,
        relevant_docs: List[Tuple[Dict[str, Any], DocumentRelevance, float]]
    ) -> Tuple[str, ResponseQuality, str]:
        """
        Step 3: Generate response with self-reflection.
        
        The LLM generates an answer AND evaluates if its response
        is supported by the documents.
        """
        
        # Build context from relevant documents
        context_parts = []
        for doc, relevance, score in relevant_docs:
            if relevance != DocumentRelevance.IRRELEVANT:
                doc_text = doc.get("text", doc.get("content", str(doc)))[:1500]
                context_parts.append(f"[Score: {score:.2f}] {doc_text}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""You are a professional analyst. Answer the query using ONLY the provided context.

CONTEXT (retrieved documents):
{context[:6000]}

QUERY: {query}

INSTRUCTIONS:
1. Answer the query using ONLY information from the context
2. Be concise and data-driven
3. If the context doesn't contain enough information, say so honestly
4. Do NOT make up any numbers or facts

After your answer, provide a self-assessment:
- Are all your claims supported by the context?
- What is your confidence level?

Format your response:
ANSWER:
[Your concise answer here]

SELF-ASSESSMENT:
{{"quality": "fully_supported" | "partially_supported" | "not_supported", "confidence": 0.0-1.0, "critique": "brief self-critique"}}"""

        try:
            response = chat(prompt, temperature=0.3)
            
            # Parse answer and self-assessment
            if "SELF-ASSESSMENT:" in response:
                parts = response.split("SELF-ASSESSMENT:")
                answer = parts[0].replace("ANSWER:", "").strip()
                assessment_str = parts[1].strip()
                
                # Try to parse JSON assessment
                try:
                    # Find JSON in assessment
                    json_start = assessment_str.find("{")
                    json_end = assessment_str.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        assessment = json.loads(assessment_str[json_start:json_end])
                        quality = ResponseQuality(assessment.get("quality", "partially_supported"))
                        critique = assessment.get("critique", "")
                    else:
                        quality = ResponseQuality.PARTIALLY_SUPPORTED
                        critique = assessment_str
                except:
                    quality = ResponseQuality.PARTIALLY_SUPPORTED
                    critique = assessment_str
            else:
                answer = response.strip()
                quality = ResponseQuality.PARTIALLY_SUPPORTED
                critique = "No self-assessment provided"
            
            return answer, quality, critique
            
        except Exception as e:
            logger.error(f"Error in generation: {e}")
            return "I encountered an error processing your query.", ResponseQuality.NOT_SUPPORTED, str(e)
    
    async def refine_answer(
        self,
        query: str,
        original_answer: str,
        critique: str,
        documents: List[Dict[str, Any]]
    ) -> str:
        """
        Step 4: Refine answer based on self-critique.
        
        If the original answer had issues, try to improve it.
        """
        
        context = "\n".join([
            doc.get("text", doc.get("content", str(doc)))[:1000] 
            for doc in documents[:3]
        ])
        
        prompt = f"""Improve this answer based on the critique.

ORIGINAL QUERY: {query}

ORIGINAL ANSWER: {original_answer}

CRITIQUE: {critique}

AVAILABLE CONTEXT:
{context[:4000]}

Provide an improved, more accurate answer. Be concise and data-driven.
Use ONLY facts from the context. Don't make up information."""

        try:
            refined = chat(prompt, temperature=0.2)
            return refined.strip()
        except Exception as e:
            logger.warning(f"Error refining: {e}")
            return original_answer
    
    async def run(
        self,
        query: str,
        documents: List[Dict[str, Any]] = None,
        retrieval_fn = None,
        existing_context: str = ""
    ) -> SelfRAGResult:
        """
        Main Self-RAG pipeline.
        
        Args:
            query: User's question
            documents: Pre-retrieved documents (optional)
            retrieval_fn: Function to retrieve documents if needed
            existing_context: Any existing context
            
        Returns:
            SelfRAGResult with answer, quality metrics, and metadata
        """
        
        iteration = 0
        
        # Step 1: Decide if retrieval is needed
        decision, decision_reason = await self.should_retrieve(query, existing_context)
        logger.info(f"Self-RAG decision: {decision.value}")
        
        # Step 2: Get documents if needed
        if decision == RetrievalDecision.RETRIEVE or decision == RetrievalDecision.UNCERTAIN:
            if documents is None and retrieval_fn:
                try:
                    documents = await retrieval_fn(query)
                except:
                    documents = retrieval_fn(query)  # Try sync if async fails
            documents = documents or []
        else:
            documents = []
        
        # Step 3: Evaluate document relevance
        evaluated_docs = await self.evaluate_relevance(query, documents)
        
        # Filter to relevant documents only
        relevant_docs = [
            (doc, rel, score) for doc, rel, score in evaluated_docs 
            if rel != DocumentRelevance.IRRELEVANT and score > 0.3
        ]
        
        # Step 4: Generate with self-reflection
        answer, quality, critique = await self.generate_with_reflection(query, relevant_docs)
        iteration += 1
        
        # Step 5: Refine if quality is low
        while quality == ResponseQuality.NOT_SUPPORTED and iteration < self.max_iterations:
            logger.info(f"Self-RAG iteration {iteration + 1}: refining answer")
            answer = await self.refine_answer(
                query, answer, critique, 
                [doc for doc, _, _ in relevant_docs]
            )
            
            # Re-evaluate
            _, quality, critique = await self.generate_with_reflection(
                query, 
                relevant_docs
            )
            iteration += 1
        
        # Calculate confidence
        relevance_scores = [score for _, _, score in evaluated_docs]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.5
        
        quality_multiplier = {
            ResponseQuality.FULLY_SUPPORTED: 1.0,
            ResponseQuality.PARTIALLY_SUPPORTED: 0.7,
            ResponseQuality.NOT_SUPPORTED: 0.3
        }.get(quality, 0.5)
        
        confidence = min(avg_relevance * quality_multiplier, 1.0)
        
        return SelfRAGResult(
            answer=answer,
            retrieval_decision=decision,
            documents_used=[doc for doc, _, _ in relevant_docs],
            relevance_scores=relevance_scores,
            response_quality=quality,
            confidence=confidence,
            critique=critique,
            iterations=iteration
        )


# Convenience function for easy integration
async def self_rag_query(
    query: str,
    documents: List[Dict[str, Any]] = None,
    retrieval_fn = None,
    context: str = ""
) -> Dict[str, Any]:
    """
    Simple interface to Self-RAG.
    
    Returns dict with answer and metadata.
    """
    
    self_rag = SelfRAG()
    result = await self_rag.run(query, documents, retrieval_fn, context)
    
    return {
        "answer": result.answer,
        "confidence": result.confidence,
        "quality": result.response_quality.value,
        "documents_used": len(result.documents_used),
        "iterations": result.iterations,
        "retrieval_needed": result.retrieval_decision.value,
        "critique": result.critique
    }


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with mock documents
        test_docs = [
            {"text": "Total revenue for Q4 was $2.5 million, up 15% from Q3.", "score": 0.9},
            {"text": "The company has 150 employees across 3 offices.", "score": 0.7},
            {"text": "Customer churn rate decreased to 3.2% in December.", "score": 0.85},
        ]
        
        result = await self_rag_query(
            query="What was the Q4 revenue?",
            documents=test_docs
        )
        
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Quality: {result['quality']}")
        print(f"Iterations: {result['iterations']}")
    
    asyncio.run(test())
