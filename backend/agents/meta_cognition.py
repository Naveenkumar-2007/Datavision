"""
Meta-Cognition Agent: Self-Awareness and Validation
====================================================

The Meta-Cognition Agent is responsible for:
1. CONFIDENCE SCORING - How confident is the AI in its response?
2. HALLUCINATION DETECTION - Are there claims not supported by evidence?
3. FACTUALITY CHECK - Do the numbers/facts match the source data?
4. SELF-REFLECTION - What could be improved?
5. UNCERTAINTY QUANTIFICATION - What don't we know?

This is the "inner critic" that ensures response quality.

Uses FREE APIs only (Groq/Gemini).
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from core.llm import chat

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence in the response"""
    VERY_HIGH = "very_high"    # 90-100% - All facts verified
    HIGH = "high"              # 70-89% - Most facts verified
    MEDIUM = "medium"          # 50-69% - Some uncertainty
    LOW = "low"                # 30-49% - Significant uncertainty
    VERY_LOW = "very_low"      # <30% - Largely speculative


class HallucinationSeverity(Enum):
    """Severity of detected hallucination"""
    NONE = "none"              # No hallucination detected
    MINOR = "minor"            # Small inaccuracies
    MODERATE = "moderate"      # Some claims unverified
    SEVERE = "severe"          # Major fabrications


@dataclass
class ValidationResult:
    """Complete validation result from Meta-Cognition"""
    confidence: float
    confidence_level: ConfidenceLevel
    hallucination_severity: HallucinationSeverity
    unsupported_claims: List[str]
    verified_claims: List[str]
    factual_errors: List[Dict[str, Any]]
    suggestions: List[str]
    overall_quality: float  # 0-1 score
    reasoning: str


class MetaCognitionAgent:
    """
    The AI's inner critic - validates responses before delivery.
    
    Ensures high-quality, factual, non-hallucinated outputs.
    Uses FREE APIs (Groq/Gemini).
    """
    
    def __init__(self):
        self.validation_cache: Dict[str, ValidationResult] = {}
    
    async def score_confidence(
        self,
        response: str,
        context: str,
        query: str
    ) -> Tuple[float, ConfidenceLevel, str]:
        """
        Score the confidence level of a response.
        
        Returns (score 0-1, level, reasoning)
        """
        
        prompt = f"""You are a response quality evaluator. Score the confidence level of this AI response.

ORIGINAL QUERY: {query}

AVAILABLE CONTEXT (source data):
{context[:3000]}

AI RESPONSE TO EVALUATE:
{response}

Score confidence based on:
1. Are all claims in the response supported by the context?
2. Are numbers/statistics accurate and from the context?
3. Does the response directly answer the query?
4. Is there any speculation or uncertainty?

Respond with JSON:
{{
    "confidence_score": 0.0-1.0,
    "level": "very_high" | "high" | "medium" | "low" | "very_low",
    "reasoning": "brief explanation of the score"
}}"""

        try:
            result = chat(prompt, temperature=0.1)
            
            # Parse JSON
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                score = float(data.get("confidence_score", 0.5))
                level = ConfidenceLevel(data.get("level", "medium"))
                reasoning = data.get("reasoning", "")
                return score, level, reasoning
            
        except Exception as e:
            logger.warning(f"Error scoring confidence: {e}")
        
        return 0.5, ConfidenceLevel.MEDIUM, "Unable to evaluate confidence"
    
    async def detect_hallucinations(
        self,
        response: str,
        context: str
    ) -> Tuple[HallucinationSeverity, List[str], List[str]]:
        """
        Detect claims in the response not supported by context.
        
        Returns (severity, unsupported_claims, verified_claims)
        """
        
        prompt = f"""You are a hallucination detector. Identify claims in the AI response that are NOT supported by the source context.

SOURCE CONTEXT (the only valid source of truth):
{context[:3000]}

AI RESPONSE TO CHECK:
{response}

For each factual claim in the response:
1. Check if it appears in or can be derived from the context
2. Mark as "verified" if supported, "unsupported" if not

Respond with JSON:
{{
    "severity": "none" | "minor" | "moderate" | "severe",
    "unsupported_claims": ["list of claims not in context"],
    "verified_claims": ["list of claims verified in context"],
    "analysis": "brief explanation"
}}"""

        try:
            result = chat(prompt, temperature=0.1)
            
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                severity = HallucinationSeverity(data.get("severity", "none"))
                unsupported = data.get("unsupported_claims", [])
                verified = data.get("verified_claims", [])
                return severity, unsupported, verified
            
        except Exception as e:
            logger.warning(f"Error detecting hallucinations: {e}")
        
        return HallucinationSeverity.NONE, [], []
    
    async def check_factual_accuracy(
        self,
        response: str,
        context: str
    ) -> List[Dict[str, Any]]:
        """
        Check if numbers and facts in the response match the context.
        
        Returns list of factual errors found.
        """
        
        prompt = f"""You are a fact-checker. Verify that all numbers, statistics, and specific facts in the AI response match the source context.

SOURCE CONTEXT:
{context[:3000]}

AI RESPONSE:
{response}

Check each number and specific fact. Report any ERRORS where the response differs from the context.

Respond with JSON:
{{
    "errors": [
        {{
            "claim": "what the response says",
            "actual": "what the context says",
            "type": "number" | "fact" | "date" | "name"
        }}
    ],
    "all_facts_correct": true | false
}}"""

        try:
            result = chat(prompt, temperature=0.1)
            
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("errors", [])
            
        except Exception as e:
            logger.warning(f"Error checking facts: {e}")
        
        return []
    
    async def generate_suggestions(
        self,
        response: str,
        query: str,
        issues: List[str]
    ) -> List[str]:
        """
        Generate suggestions for improving the response.
        """
        
        if not issues:
            return ["Response appears to be high quality."]
        
        prompt = f"""You are a response improvement advisor.

ORIGINAL QUERY: {query}

CURRENT RESPONSE:
{response}

ISSUES IDENTIFIED:
{json.dumps(issues, indent=2)}

Provide 2-3 specific, actionable suggestions to improve this response.
Focus on accuracy, clarity, and completeness.

Respond with JSON:
{{"suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]}}"""

        try:
            result = chat(prompt, temperature=0.3)
            
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("suggestions", [])
            
        except Exception as e:
            logger.warning(f"Error generating suggestions: {e}")
        
        return ["Review response for accuracy."]
    
    async def validate(
        self,
        response: str,
        context: str,
        query: str
    ) -> ValidationResult:
        """
        Complete validation pipeline.
        
        Runs all checks and returns comprehensive validation result.
        """
        
        logger.info("Meta-Cognition: Starting validation")
        
        # 1. Score confidence
        confidence, confidence_level, conf_reasoning = await self.score_confidence(
            response, context, query
        )
        
        # 2. Detect hallucinations
        hall_severity, unsupported, verified = await self.detect_hallucinations(
            response, context
        )
        
        # 3. Check factual accuracy
        factual_errors = await self.check_factual_accuracy(response, context)
        
        # 4. Generate suggestions based on issues
        issues = unsupported + [e.get("claim", "") for e in factual_errors]
        suggestions = await self.generate_suggestions(response, query, issues)
        
        # 5. Calculate overall quality
        quality_score = confidence
        
        if hall_severity == HallucinationSeverity.SEVERE:
            quality_score *= 0.3
        elif hall_severity == HallucinationSeverity.MODERATE:
            quality_score *= 0.6
        elif hall_severity == HallucinationSeverity.MINOR:
            quality_score *= 0.85
        
        if factual_errors:
            quality_score *= (1 - 0.1 * len(factual_errors))
        
        quality_score = max(0, min(1, quality_score))
        
        result = ValidationResult(
            confidence=confidence,
            confidence_level=confidence_level,
            hallucination_severity=hall_severity,
            unsupported_claims=unsupported,
            verified_claims=verified,
            factual_errors=factual_errors,
            suggestions=suggestions,
            overall_quality=quality_score,
            reasoning=conf_reasoning
        )
        
        logger.info(f"Meta-Cognition validation complete: quality={quality_score:.2f}")
        
        return result
    
    def should_refine(self, result: ValidationResult) -> bool:
        """
        Decide if the response should be refined based on validation.
        """
        
        # Refine if quality is low or there are significant issues
        if result.overall_quality < 0.5:
            return True
        if result.hallucination_severity in [HallucinationSeverity.SEVERE, HallucinationSeverity.MODERATE]:
            return True
        if len(result.factual_errors) >= 2:
            return True
        
        return False
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """
        Generate human-readable validation summary.
        """
        
        quality_emoji = "🟢" if result.overall_quality > 0.7 else "🟡" if result.overall_quality > 0.4 else "🔴"
        
        summary = f"""
{quality_emoji} **Response Quality: {result.overall_quality:.0%}**

📊 Confidence: {result.confidence_level.value} ({result.confidence:.0%})
🔍 Hallucination Check: {result.hallucination_severity.value}
✅ Verified Claims: {len(result.verified_claims)}
⚠️ Unverified Claims: {len(result.unsupported_claims)}
❌ Factual Errors: {len(result.factual_errors)}
""".strip()
        
        if result.suggestions:
            summary += f"\n\n💡 Suggestions:\n" + "\n".join(f"  • {s}" for s in result.suggestions)
        
        return summary


# Convenience function
async def validate_response(
    response: str,
    context: str,
    query: str
) -> Dict[str, Any]:
    """
    Simple interface to validate a response.
    
    Returns dict with validation results.
    """
    
    agent = MetaCognitionAgent()
    result = await agent.validate(response, context, query)
    
    return {
        "quality": result.overall_quality,
        "confidence": result.confidence,
        "confidence_level": result.confidence_level.value,
        "hallucinations": result.hallucination_severity.value,
        "unsupported_claims": result.unsupported_claims,
        "factual_errors": result.factual_errors,
        "suggestions": result.suggestions,
        "should_refine": agent.should_refine(result),
        "summary": agent.get_validation_summary(result)
    }


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        context = """
        Q4 2024 Financial Report - Acme Corporation
        Total revenue: $2.5 million (up 15% from Q3)
        Operating expenses: $1.8 million
        Net profit: $700,000
        Customer count: 1,250
        Churn rate: 3.2%
        """
        
        # Test with a good response
        good_response = "Q4 revenue was $2.5 million, a 15% increase from Q3. Net profit reached $700,000."
        
        # Test with a bad response (hallucination)
        bad_response = "Q4 revenue was $3.5 million, the highest ever. The company expanded to 50 countries."
        
        print("=== Testing Good Response ===")
        result = await validate_response(good_response, context, "What was Q4 revenue?")
        print(result["summary"])
        
        print("\n=== Testing Bad Response ===")
        result = await validate_response(bad_response, context, "What was Q4 revenue?")
        print(result["summary"])
    
    asyncio.run(test())
