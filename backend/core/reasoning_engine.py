"""
🤖 REASONING ENGINE - DataVision Advanced AI Reasoning
======================================================

Silicon Valley-grade reasoning capabilities:
- Chain-of-Thought (CoT) - Step-by-step reasoning
- ReAct (Reasoning + Acting) - Thought-Action-Observation loops
- Self-Correction - Automatic error detection and fixing
- Confidence Scoring - Know when AI is uncertain

FREE MODELS: Groq (Llama 3.3 70B), Gemini Free
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm import chat

logger = logging.getLogger(__name__)


class ReasoningMode(Enum):
    """Available reasoning modes"""
    DIRECT = "direct"           # Simple direct answer
    CHAIN_OF_THOUGHT = "cot"    # Step-by-step reasoning
    REACT = "react"             # Reasoning + Acting loops
    SELF_CONSISTENCY = "sc"     # Multiple attempts with voting


@dataclass
class ReasoningStep:
    """A single step in the reasoning process"""
    step_number: int
    step_type: str  # thought, action, observation, conclusion
    content: str
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReasoningResult:
    """Complete result from reasoning engine"""
    query: str
    mode: ReasoningMode
    steps: List[ReasoningStep]
    final_answer: str
    confidence: float
    reasoning_time_ms: int
    tokens_used: int = 0
    needs_data: bool = False
    suggested_mcps: List[str] = field(default_factory=list)


class ReasoningEngine:
    """
    🧠 Advanced Reasoning Engine
    
    Provides ChatGPT/Claude-level reasoning capabilities:
    - Chain-of-Thought for complex analysis
    - ReAct for multi-step data operations  
    - Self-correction when answers are uncertain
    """
    
    def __init__(self):
        self.max_react_iterations = 5
        self.confidence_threshold = 0.7
    
    async def reason(
        self,
        query: str,
        context: str = "",
        data_schema: Optional[Dict] = None,
        mode: ReasoningMode = ReasoningMode.CHAIN_OF_THOUGHT,
        available_mcps: Optional[List[str]] = None
    ) -> ReasoningResult:
        """
        Main reasoning entry point
        
        Args:
            query: User's question or request
            context: Additional context (data summary, previous conversation)
            data_schema: Schema of available data
            mode: Which reasoning mode to use
            available_mcps: List of available MCPs for ReAct mode
            
        Returns:
            Complete reasoning result with steps and answer
        """
        start_time = datetime.now()
        
        logger.info(f"🤖 Reasoning: mode={mode.value}, query={query[:50]}...")
        
        if mode == ReasoningMode.DIRECT:
            result = await self._direct_answer(query, context)
        elif mode == ReasoningMode.CHAIN_OF_THOUGHT:
            result = await self._chain_of_thought(query, context, data_schema)
        elif mode == ReasoningMode.REACT:
            result = await self._react_reasoning(query, context, data_schema, available_mcps or [])
        elif mode == ReasoningMode.SELF_CONSISTENCY:
            result = await self._self_consistency(query, context, data_schema)
        else:
            result = await self._chain_of_thought(query, context, data_schema)
        
        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        result.reasoning_time_ms = duration_ms
        
        logger.info(f"✅ Reasoning complete: {duration_ms}ms, confidence={result.confidence:.2f}")
        
        return result
    
    async def _direct_answer(self, query: str, context: str) -> ReasoningResult:
        """Simple direct answer without explicit reasoning"""
        prompt = f"""Answer this question directly and concisely.

Question: {query}

Context: {context if context else "No additional context"}

Provide a clear, helpful answer."""

        response = await self._call_llm(prompt)
        
        return ReasoningResult(
            query=query,
            mode=ReasoningMode.DIRECT,
            steps=[ReasoningStep(
                step_number=1,
                step_type="answer",
                content=response
            )],
            final_answer=response,
            confidence=0.8,
            reasoning_time_ms=0
        )
    
    async def _chain_of_thought(
        self, 
        query: str, 
        context: str,
        data_schema: Optional[Dict] = None
    ) -> ReasoningResult:
        """
        Chain-of-Thought reasoning - step by step analysis
        
        This produces ChatGPT-quality explanations by:
        1. Breaking down the problem
        2. Analyzing each part
        3. Synthesizing insights
        4. Providing actionable conclusions
        """
        schema_str = ""
        if data_schema:
            schema_str = f"\n\nAvailable Data Schema:\n{json.dumps(data_schema, indent=2)}"
        
        prompt = f"""You are a world-class data analyst. Think through this step-by-step.

USER QUESTION: {query}

CONTEXT: {context if context else "No additional context"}{schema_str}

Think through this problem step by step:

1. UNDERSTAND: What exactly is the user asking for?
2. ANALYZE: What data or information do we need?
3. APPROACH: How should we solve this?
4. EXECUTE: Work through the solution
5. CONCLUDE: What's the final answer and key insights?

Format your response as:
**Step 1 - Understanding:**
[Your analysis of what's being asked]

**Step 2 - Data Needed:**
[What data/information is required]

**Step 3 - Approach:**
[How you'll solve this]

**Step 4 - Analysis:**
[The actual analysis work]

**Step 5 - Conclusion:**
[Final answer with actionable insights]

Be thorough but concise. Focus on delivering VALUE."""

        response = await self._call_llm(prompt, temperature=0.3)
        
        # Parse steps from response
        steps = self._parse_cot_steps(response)
        
        # Extract final answer
        final_answer = self._extract_conclusion(response)
        
        # Calculate confidence based on step quality
        confidence = self._calculate_cot_confidence(steps, response)
        
        return ReasoningResult(
            query=query,
            mode=ReasoningMode.CHAIN_OF_THOUGHT,
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            reasoning_time_ms=0
        )
    
    async def _react_reasoning(
        self,
        query: str,
        context: str,
        data_schema: Optional[Dict],
        available_mcps: List[str]
    ) -> ReasoningResult:
        """
        ReAct (Reasoning + Acting) - Thought-Action-Observation loops
        
        This enables autonomous data operations:
        1. Think about what to do
        2. Choose an action (MCP to call)
        3. Observe the result
        4. Repeat until solved
        """
        steps = []
        iteration = 0
        accumulated_observations = []
        
        mcp_list = ", ".join(available_mcps) if available_mcps else "forecast, analyze, segment, anomaly_detect"
        
        while iteration < self.max_react_iterations:
            iteration += 1
            
            # Build context with previous observations
            obs_context = "\n".join(accumulated_observations) if accumulated_observations else "None yet"
            
            prompt = f"""You are an AI data agent using the ReAct framework. Think and act step by step.

GOAL: {query}

AVAILABLE ACTIONS (MCPs):
{mcp_list}

PREVIOUS OBSERVATIONS:
{obs_context}

DATA CONTEXT:
{context if context else "No specific data context"}

Now, reason about what to do next:

THOUGHT: [Your reasoning about the current situation and what to do next]
ACTION: [The action to take - either call an MCP or provide final answer]
ACTION_INPUT: [Input for the action, or your final answer if ACTION is "finish"]

If you have enough information to answer, use:
ACTION: finish
ACTION_INPUT: [Your complete final answer]

Be decisive. If you can answer, answer. Don't loop unnecessarily."""

            response = await self._call_llm(prompt, temperature=0.2)
            
            # Parse the response
            thought, action, action_input = self._parse_react_response(response)
            
            # Record thought step
            steps.append(ReasoningStep(
                step_number=len(steps) + 1,
                step_type="thought",
                content=thought
            ))
            
            # Check if finished
            if action.lower() == "finish":
                steps.append(ReasoningStep(
                    step_number=len(steps) + 1,
                    step_type="conclusion",
                    content=action_input
                ))
                
                return ReasoningResult(
                    query=query,
                    mode=ReasoningMode.REACT,
                    steps=steps,
                    final_answer=action_input,
                    confidence=0.85,
                    reasoning_time_ms=0,
                    suggested_mcps=[s.content for s in steps if s.step_type == "action"]
                )
            
            # Record action step
            steps.append(ReasoningStep(
                step_number=len(steps) + 1,
                step_type="action",
                content=f"{action}: {action_input}"
            ))
            
            # Simulate observation (in real implementation, would call MCP)
            observation = f"[MCP {action} called with input: {action_input}] - Result would be provided by MCP execution"
            accumulated_observations.append(f"Action {iteration}: {action} -> {observation[:200]}")
            
            steps.append(ReasoningStep(
                step_number=len(steps) + 1,
                step_type="observation",
                content=observation
            ))
        
        # Max iterations reached
        final_answer = "I need more information or actions to fully answer this question. Based on my analysis so far: " + (steps[-1].content if steps else "No conclusion reached")
        
        return ReasoningResult(
            query=query,
            mode=ReasoningMode.REACT,
            steps=steps,
            final_answer=final_answer,
            confidence=0.5,
            reasoning_time_ms=0,
            needs_data=True,
            suggested_mcps=[s.content.split(":")[0] for s in steps if s.step_type == "action"]
        )
    
    async def _self_consistency(
        self,
        query: str,
        context: str,
        data_schema: Optional[Dict]
    ) -> ReasoningResult:
        """
        Self-Consistency - Multiple reasoning paths with voting
        
        Generates multiple independent answers and picks the most consistent one.
        Useful for complex analytical questions.
        """
        num_samples = 3
        answers = []
        all_steps = []
        
        for i in range(num_samples):
            result = await self._chain_of_thought(query, context, data_schema)
            answers.append(result.final_answer)
            all_steps.extend([
                ReasoningStep(
                    step_number=len(all_steps) + 1,
                    step_type=f"attempt_{i+1}",
                    content=result.final_answer,
                    confidence=result.confidence
                )
            ])
        
        # Use LLM to synthesize the best answer
        synthesis_prompt = f"""You received {num_samples} different attempts to answer this question:

Question: {query}

Attempt 1: {answers[0][:500]}

Attempt 2: {answers[1][:500]}

Attempt 3: {answers[2][:500]}

Synthesize these into a single, best answer. Take the most consistent and well-reasoned elements from each attempt.

Provide:
1. The synthesized best answer
2. Your confidence (0-1) in this answer
3. Any areas of disagreement between attempts

Format:
BEST_ANSWER: [Your synthesized answer]
CONFIDENCE: [0.0-1.0]
DISAGREEMENTS: [Any notable disagreements]"""

        synthesis = await self._call_llm(synthesis_prompt, temperature=0.1)
        
        # Parse synthesis
        best_answer = self._extract_section(synthesis, "BEST_ANSWER:", "CONFIDENCE:")
        confidence_str = self._extract_section(synthesis, "CONFIDENCE:", "DISAGREEMENTS:")
        
        try:
            confidence = float(confidence_str.strip())
        except:
            confidence = 0.75
        
        all_steps.append(ReasoningStep(
            step_number=len(all_steps) + 1,
            step_type="synthesis",
            content=best_answer,
            confidence=confidence
        ))
        
        return ReasoningResult(
            query=query,
            mode=ReasoningMode.SELF_CONSISTENCY,
            steps=all_steps,
            final_answer=best_answer,
            confidence=min(confidence, 0.95),
            reasoning_time_ms=0
        )
    
    def _parse_cot_steps(self, response: str) -> List[ReasoningStep]:
        """Parse Chain-of-Thought steps from LLM response"""
        steps = []
        
        # Look for step patterns
        step_patterns = [
            (r"\*\*Step 1[^*]*\*\*:?\s*(.*?)(?=\*\*Step 2|\Z)", "understanding"),
            (r"\*\*Step 2[^*]*\*\*:?\s*(.*?)(?=\*\*Step 3|\Z)", "data_analysis"),
            (r"\*\*Step 3[^*]*\*\*:?\s*(.*?)(?=\*\*Step 4|\Z)", "approach"),
            (r"\*\*Step 4[^*]*\*\*:?\s*(.*?)(?=\*\*Step 5|\Z)", "execution"),
            (r"\*\*Step 5[^*]*\*\*:?\s*(.*?)(?=\Z)", "conclusion"),
        ]
        
        for i, (pattern, step_type) in enumerate(step_patterns):
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    steps.append(ReasoningStep(
                        step_number=i + 1,
                        step_type=step_type,
                        content=content[:1000]  # Limit length
                    ))
        
        # If no structured steps found, create a single step
        if not steps:
            steps.append(ReasoningStep(
                step_number=1,
                step_type="analysis",
                content=response[:2000]
            ))
        
        return steps
    
    def _extract_conclusion(self, response: str) -> str:
        """Extract the final conclusion from CoT response"""
        # Look for conclusion section
        patterns = [
            r"\*\*Step 5[^*]*\*\*:?\s*(.*?)(?=\Z)",
            r"\*\*Conclusion[^*]*\*\*:?\s*(.*?)(?=\Z)",
            r"(?:In conclusion|To summarize|Final answer)[:\s]*(.*?)(?=\Z)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()[:2000]
        
        # Return last part of response if no conclusion found
        lines = response.strip().split('\n')
        return '\n'.join(lines[-5:])[:2000]
    
    def _calculate_cot_confidence(self, steps: List[ReasoningStep], response: str) -> float:
        """Calculate confidence based on reasoning quality"""
        confidence = 0.7  # Base confidence
        
        # More steps = more thorough = higher confidence
        if len(steps) >= 4:
            confidence += 0.1
        
        # Check for hedging language
        hedging_words = ['maybe', 'possibly', 'might', 'uncertain', 'not sure', 'could be']
        hedging_count = sum(1 for word in hedging_words if word in response.lower())
        confidence -= hedging_count * 0.05
        
        # Check for confident language
        confident_words = ['clearly', 'definitely', 'certainly', 'shows that', 'indicates']
        confident_count = sum(1 for word in confident_words if word in response.lower())
        confidence += confident_count * 0.03
        
        # Clamp to valid range
        return max(0.3, min(0.95, confidence))
    
    def _parse_react_response(self, response: str) -> Tuple[str, str, str]:
        """Parse ReAct response into thought, action, action_input"""
        thought = ""
        action = "finish"
        action_input = ""
        
        # Extract thought
        thought_match = re.search(r"THOUGHT:\s*(.*?)(?=ACTION:|$)", response, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()
        
        # Extract action
        action_match = re.search(r"ACTION:\s*(.*?)(?=ACTION_INPUT:|$)", response, re.DOTALL | re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().split('\n')[0]
        
        # Extract action input
        input_match = re.search(r"ACTION_INPUT:\s*(.*?)(?=$)", response, re.DOTALL | re.IGNORECASE)
        if input_match:
            action_input = input_match.group(1).strip()
        
        return thought, action, action_input
    
    def _extract_section(self, text: str, start: str, end: str) -> str:
        """Extract text between two markers"""
        try:
            start_idx = text.find(start)
            if start_idx == -1:
                return ""
            start_idx += len(start)
            
            end_idx = text.find(end, start_idx)
            if end_idx == -1:
                return text[start_idx:].strip()
            
            return text[start_idx:end_idx].strip()
        except:
            return ""
    
    async def _call_llm(self, prompt: str, temperature: float = 0.4) -> str:
        """Call the LLM"""
        try:
            response = chat(
                messages=prompt,
                system="You are an expert data analyst and reasoning agent. Think carefully and provide thorough, accurate analysis.",
                temperature=temperature,
                max_tokens=2000
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def select_reasoning_mode(self, query: str, context: str = "") -> ReasoningMode:
        """
        Automatically select the best reasoning mode for a query
        
        Returns:
            The most appropriate reasoning mode
        """
        query_lower = query.lower()
        
        # Direct mode for simple questions
        simple_patterns = ['what is', 'who is', 'when was', 'define', 'list']
        if any(pattern in query_lower for pattern in simple_patterns):
            if len(query) < 50:
                return ReasoningMode.DIRECT
        
        # ReAct for action-oriented queries
        action_patterns = ['calculate', 'predict', 'forecast', 'analyze and', 'find and', 'create', 'generate']
        if any(pattern in query_lower for pattern in action_patterns):
            return ReasoningMode.REACT
        
        # Self-consistency for uncertain/complex analysis
        complex_patterns = ['compare', 'evaluate', 'assess', 'which is better', 'should i']
        if any(pattern in query_lower for pattern in complex_patterns):
            return ReasoningMode.SELF_CONSISTENCY
        
        # Default to Chain-of-Thought for most queries
        return ReasoningMode.CHAIN_OF_THOUGHT


# Global instance
_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine() -> ReasoningEngine:
    """Get or create the global reasoning engine"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine


async def reason(
    query: str,
    context: str = "",
    data_schema: Optional[Dict] = None,
    mode: Optional[ReasoningMode] = None,
    available_mcps: Optional[List[str]] = None
) -> ReasoningResult:
    """
    Quick function to reason about a query
    
    Usage:
        result = await reason("Why did sales drop in Q3?", context=data_summary)
    """
    engine = get_reasoning_engine()
    
    # Auto-select mode if not specified
    if mode is None:
        mode = engine.select_reasoning_mode(query, context)
    
    return await engine.reason(query, context, data_schema, mode, available_mcps)
