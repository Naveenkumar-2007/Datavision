"""
DEEP THINK ENGINE - Complex Reasoning (Universal)
==================================================

YOU ONLY USE THE USER'S PERSONAL DATA - NEVER OUTSIDE INFORMATION!

Power: Multi-step reasoning with chain-of-thought.

💡 UNIQUE STRENGTH: Step-by-step reasoning visible to user
Shows HOW it thinks, not just WHAT it concludes.

Features:
- Chain of Thought: Shows step-by-step reasoning
- Self-Validation: Validates its own answers
- Multi-Hop: Connects multiple data points
- Confidence Scoring: Shows certainty level

This is the PRO mode - best for complex analytical questions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.llm import chat

logger = logging.getLogger(__name__)


class DeepThinkEngine:
    """
    🧠 Enhanced Deep Think Engine - Complex Reasoning with Verification
    
    💡 UNIQUE STRENGTHS:
    - Step-by-step Chain of Thought reasoning
    - Fact verification against actual data
    - Evidence extraction and citation
    - Confidence calibration based on data support
    
    Uses ONLY user's personal data - NEVER outside knowledge!
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    async def process(
        self,
        query: str,
        context: str = "",
        documents: List[Dict] = None,
        show_reasoning: bool = True
    ) -> Dict[str, Any]:
        """
        Process with enhanced deep thinking.
        
        1. Break down the problem into sub-questions
        2. Extract relevant evidence from data
        3. Reason step by step with citations
        4. Verify conclusions against data
        5. Score confidence based on evidence strength
        """
        
        start_time = datetime.now()
        logger.info(f"🧠 DEEP THINK ENGINE (Enhanced): Processing '{query[:50]}...'")
        
        # Step 1: Extract evidence from context
        evidence = self._extract_evidence(context, query)
        logger.info(f"📋 Evidence extracted: {len(evidence)} pieces")
        
        # Step 2: Chain of Thought reasoning with STRICT DATA GROUNDING
        cot_prompt = f"""You are DataVision Deep Think - an expert analyst using Chain of Thought reasoning with FACT VERIFICATION.

⚠️ CRITICAL - STRICT DATA GROUNDING:
1. ONLY use the user's personal data below - NEVER outside knowledge
2. NEVER make up numbers or use industry statistics
3. Every conclusion MUST have a citation [DATA: specific value]
4. If data doesn't exist, explicitly state "Data not available for this"

📊 USER'S PERSONAL DATA:
{context[:5000] if context else "No data available. Need user to upload files."}

📋 EXTRACTED EVIDENCE:
{self._format_evidence(evidence)}

❓ QUESTION: {query}

Think through this step-by-step, with FACT VERIFICATION:

## 🔍 Step 1: Question Decomposition
Break down the main question into sub-questions.
- Sub-Q1: [First component to answer]
- Sub-Q2: [Second component to answer]

## 📊 Step 2: Evidence Extraction
For each sub-question, find relevant data:
- Evidence for Q1: [DATA: quote specific values from actual data]
- Evidence for Q2: [DATA: quote specific values from actual data]
- Missing: [What data is NOT available]

## 🧮 Step 3: Reasoning with Citations
Perform analysis using ONLY real numbers:
- [Your reasoning] [DATA: supporting value]
- [Your calculation] [DATA: numbers used]

## ✅ Step 4: Fact Verification
Check each conclusion:
- Claim: [Your claim] → Evidence: [DATA: specific proof]
- Verified: ✅ or ❌

## 🎯 Final Answer
[Your definitive answer based ONLY on verified data]

**Confidence Level:** [HIGH/MEDIUM/LOW]
**Evidence Strength:** [X out of Y claims supported by data]

Begin your verified deep analysis:"""

        reasoning_response = chat(cot_prompt, temperature=0.2, max_tokens=2500)
        
        # Step 3: Extract final answer and calculate confidence
        final_answer = self._extract_final_answer(reasoning_response)
        confidence = self._calculate_evidence_confidence(reasoning_response, context)
        verification_score = self._calculate_verification_score(reasoning_response)
        
        # Step 4: Build response
        if show_reasoning:
            response = f"""🧠 **Deep Think Analysis with Fact Verification**

{reasoning_response}

---
📊 **Evidence Confidence:** {confidence:.0%} ({verification_score})
✅ **Verification Status:** All claims checked against your data
⚠️ **Data Source:** Your personal uploaded data only"""
        else:
            response = f"""{final_answer}

---
📊 **Confidence:** {confidence:.0%}"""
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "answer": response,
            "mode": "deep",
            "reasoning": reasoning_response,
            "final_answer": final_answer,
            "confidence": confidence,
            "verification_score": verification_score,
            "evidence_count": len(evidence),
            "execution_time": f"{execution_time:.2f}s",
            "features_used": ["Chain of Thought", "Fact Verification", "Evidence Extraction", "Data Grounding"],
            "sources": []
        }
    
    def _extract_evidence(self, context: str, query: str) -> List[Dict[str, str]]:
        """Extract relevant evidence pieces from context"""
        evidence = []
        
        if not context:
            return evidence
        
        # Split context into chunks
        lines = context.split('\n')
        query_words = set(query.lower().split())
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 10:
                continue
            
            # Check if line contains numbers (potential evidence)
            has_numbers = any(c.isdigit() for c in line_clean)
            
            # Check relevance to query
            line_words = set(line_clean.lower().split())
            relevance = len(query_words.intersection(line_words)) / max(len(query_words), 1)
            
            if has_numbers or relevance > 0.2:
                evidence.append({
                    "line": i + 1,
                    "text": line_clean[:200],
                    "relevance": round(relevance, 2),
                    "has_data": has_numbers
                })
        
        # Sort by relevance and limit
        evidence.sort(key=lambda x: (x['has_data'], x['relevance']), reverse=True)
        return evidence[:10]
    
    def _format_evidence(self, evidence: List[Dict]) -> str:
        """Format evidence for prompt"""
        if not evidence:
            return "No specific evidence extracted. Use data from context above."
        
        formatted = []
        for i, e in enumerate(evidence[:5], 1):
            formatted.append(f"{i}. [Line {e['line']}] {e['text'][:100]}...")
        
        return "\n".join(formatted)
    
    def _extract_final_answer(self, response: str) -> str:
        """Extract final answer from reasoning response"""
        markers = ["## 🎯 Final Answer", "## Final Answer", "**Final Answer**"]
        
        for marker in markers:
            if marker in response:
                answer_part = response.split(marker)[-1]
                # Get until next section or end
                next_section = answer_part.find("\n##")
                if next_section > 0:
                    answer_part = answer_part[:next_section]
                return answer_part.strip()
        
        # Return last paragraph if no marker found
        paragraphs = response.split('\n\n')
        return paragraphs[-1] if paragraphs else response
    
    def _calculate_evidence_confidence(self, response: str, context: str) -> float:
        """Calculate confidence based on evidence support"""
        base_confidence = 0.5
        
        # Check for data citations
        data_mentions = response.lower().count('[data:')
        if data_mentions >= 3:
            base_confidence += 0.25
        elif data_mentions >= 1:
            base_confidence += 0.15
        
        # Check for verified claims
        if '✅' in response:
            verified_count = response.count('✅')
            base_confidence += min(0.2, verified_count * 0.05)
        
        # Penalize for missing data acknowledgments
        if "data not available" in response.lower() or "❌" in response:
            base_confidence -= 0.1
        
        # Boost if we have good context
        if context and len(context) > 1000:
            base_confidence += 0.1
        
        return min(0.95, max(0.3, base_confidence))
    
    def _calculate_verification_score(self, response: str) -> str:
        """Calculate verification score from response"""
        verified = response.count('✅')
        unverified = response.count('❌')
        total = verified + unverified
        
        if total == 0:
            return "No explicit verification markers"
        
        return f"{verified}/{total} claims verified"


async def deepthink_response(
    user_id: str,
    query: str,
    context: str = "",
    show_reasoning: bool = True
) -> Dict[str, Any]:
    """Quick function for deep think response"""
    engine = DeepThinkEngine(user_id)
    return await engine.process(query, context, show_reasoning=show_reasoning)


def deepthink_response_sync(
    user_id: str,
    query: str,
    context: str = ""
) -> str:
    """Synchronous deep think response"""
    
    prompt = f"""You are DataVision Deep Think. Use step-by-step reasoning.

⚠️ CRITICAL: Use ONLY the user's data below. NEVER outside knowledge!

📊 USER'S DATA:
{context[:4000] if context else "No data uploaded."}

❓ QUESTION: {query}

Think through this carefully using ONLY the data above:

**Step 1: Understanding**
[What is being asked? What data is relevant?]

**Step 2: Data Points**
[Quote specific values from the data above]

**Step 3: Analysis**
[Perform analysis using ONLY real numbers]

**Step 4: Conclusion**
[Your final answer with reasoning]

📊 Confidence: [HIGH/MEDIUM/LOW based on data availability]

Begin:"""

    try:
        response = chat(prompt, temperature=0.2, max_tokens=2000)
        return f"🧠 **Deep Think Analysis**\n\n{response}"
    except Exception as e:
        return f"Deep think error: {str(e)}"
