"""
🤖 DEEP AGENTS - Advanced Agent Patterns
========================================

Silicon Valley-grade autonomous agents with multiple reasoning strategies.

Agent Types:
- ReActAgent: Reason + Act loop with tool calling
- PlanAndExecuteAgent: Plan first, then execute
- ReflexionAgent: Self-reflection and improvement
- HybridAgent: Combines multiple strategies

Features:
- Tool registry and execution
- Thought chains and reasoning traces
- Self-correction and improvement
- Memory and context management
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

# LLM for reasoning
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def llm_chat(*args, **kwargs):
        return "LLM not available"


# =============================================================================
# AGENT TYPES
# =============================================================================

class AgentType(Enum):
    """Types of deep agents."""
    REACT = "react"               # Reason + Act loop
    PLAN_EXECUTE = "plan_execute" # Plan then execute
    REFLEXION = "reflexion"       # Self-reflection
    HYBRID = "hybrid"             # Combined strategies


@dataclass
class AgentTool:
    """Definition of a tool the agent can use."""
    name: str
    description: str
    function: Callable
    params: List[str] = field(default_factory=list)
    
    def to_prompt_text(self) -> str:
        """Format tool for LLM prompt."""
        params_str = ", ".join(self.params) if self.params else "none"
        return f"- {self.name}: {self.description} (params: {params_str})"


@dataclass
class ThoughtStep:
    """A step in the agent's reasoning chain."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None
    

@dataclass
class AgentResult:
    """Result from agent execution."""
    answer: str
    thought_chain: List[ThoughtStep]
    tools_used: List[str]
    agent_type: AgentType
    success: bool = True
    reflection: Optional[str] = None


# =============================================================================
# BASE AGENT
# =============================================================================

class BaseAgent:
    """Base class for all deep agents."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tools: Dict[str, AgentTool] = {}
        self.thought_chain: List[ThoughtStep] = []
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools available to all agents."""
        self.register_tool(AgentTool(
            name="search_data",
            description="Search user's data for information",
            function=self._tool_search_data,
            params=["query"]
        ))
        
        self.register_tool(AgentTool(
            name="calculate",
            description="Perform mathematical calculations",
            function=self._tool_calculate,
            params=["expression"]
        ))
        
        self.register_tool(AgentTool(
            name="get_statistics",
            description="Get statistics for a column (mean, sum, count, etc.)",
            function=self._tool_get_statistics,
            params=["column", "operation"]
        ))
        
        self.register_tool(AgentTool(
            name="get_unique_values",
            description="Get unique values count for a categorical column",
            function=self._tool_get_unique,
            params=["column"]
        ))
        
        self.register_tool(AgentTool(
            name="ask_ai",
            description="Ask AI for general knowledge (not from user data)",
            function=self._tool_ask_ai,
            params=["question"]
        ))
    
    def register_tool(self, tool: AgentTool):
        """Register a tool."""
        self.tools[tool.name] = tool
    
    def _tool_search_data(self, query: str) -> str:
        """Search user data."""
        try:
            from core.rag import rag_search
            context, sources = rag_search(self.user_id, query, k=3)
            return context if context else "No relevant data found."
        except Exception as e:
            return f"Search error: {str(e)[:100]}"
    
    def _tool_calculate(self, expression: str) -> str:
        """Calculate expression."""
        try:
            # Safe eval
            result = eval(expression, {"__builtins__": {}}, {
                "abs": abs, "round": round, "min": min, "max": max, "sum": sum,
                "len": len, "float": float, "int": int
            })
            return str(result)
        except Exception as e:
            return f"Calculation error: {str(e)[:50]}"
    
    def _tool_get_statistics(self, column: str, operation: str = "mean") -> str:
        """Get column statistics."""
        try:
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(self.user_id)
            
            if df is None or column not in df.columns:
                return f"Column '{column}' not found"
            
            ops = {
                "mean": df[column].mean,
                "sum": df[column].sum,
                "count": df[column].count,
                "min": df[column].min,
                "max": df[column].max,
                "std": df[column].std
            }
            
            if operation in ops:
                result = ops[operation]()
                return f"{operation}({column}) = {result:,.2f}" if isinstance(result, float) else str(result)
            return f"Unknown operation: {operation}"
        except Exception as e:
            return f"Statistics error: {str(e)[:100]}"
    
    def _tool_get_unique(self, column: str) -> str:
        """Get unique values count."""
        try:
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(self.user_id)
            
            if df is None or column not in df.columns:
                return f"Column '{column}' not found"
            
            unique_count = df[column].nunique()
            top_values = df[column].value_counts().head(5).to_dict()
            
            return f"Unique {column}: {unique_count}. Top values: {top_values}"
        except Exception as e:
            return f"Error: {str(e)[:100]}"
    
    def _tool_ask_ai(self, question: str) -> str:
        """Ask AI general knowledge."""
        prompt = f"""Answer this general knowledge question briefly:
{question}

Be concise (2-3 sentences max). Indicate this is general AI knowledge, not from user data."""
        
        return llm_chat(prompt, temperature=0.3, max_tokens=150)
    
    def execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"
        
        tool = self.tools[tool_name]
        try:
            # Parse input as dict or single value
            if tool_input.startswith("{"):
                try:
                    kwargs = json.loads(tool_input)
                    return tool.function(**kwargs)
                except:
                    pass
            return tool.function(tool_input)
        except Exception as e:
            return f"Tool error: {str(e)[:100]}"
    
    def get_tools_prompt(self) -> str:
        """Get formatted tools list for prompt."""
        return "\n".join([t.to_prompt_text() for t in self.tools.values()])


# =============================================================================
# REACT AGENT (Reason + Act)
# =============================================================================

class ReActAgent(BaseAgent):
    """
    ReAct Agent: Reason + Act loop.
    
    Pattern: Thought → Action → Observation → Thought → ...
    
    Inspired by the ReAct paper (Yao et al., 2022)
    """
    
    def process(self, query: str, max_steps: int = 5) -> AgentResult:
        """Run ReAct loop."""
        self.thought_chain = []
        tools_used = []
        
        system_prompt = f"""You are a ReAct agent. Solve problems by alternating between:
- THOUGHT: Reason about what to do next
- ACTION: Use a tool to get information
- OBSERVATION: Process the tool result

AVAILABLE TOOLS:
{self.get_tools_prompt()}

FORMAT YOUR RESPONSE EXACTLY AS:
THOUGHT: [your reasoning]
ACTION: [tool_name]
INPUT: [tool input]

When you have the final answer, respond:
THOUGHT: I now have enough information
ANSWER: [your final answer]

USER QUESTION: {query}"""

        conversation = [{"role": "system", "content": system_prompt}]
        
        for step in range(max_steps):
            # Get agent's next thought/action
            response = llm_chat(
                messages=conversation,
                temperature=0.2,
                max_tokens=300
            )
            
            # Parse response
            thought_match = re.search(r'THOUGHT:\s*(.+?)(?=ACTION:|ANSWER:|$)', response, re.DOTALL)
            action_match = re.search(r'ACTION:\s*(\w+)', response)
            input_match = re.search(r'INPUT:\s*(.+?)(?=THOUGHT:|$)', response, re.DOTALL)
            answer_match = re.search(r'ANSWER:\s*(.+)', response, re.DOTALL)
            
            thought = thought_match.group(1).strip() if thought_match else ""
            
            # Check for final answer
            if answer_match:
                final_answer = answer_match.group(1).strip()
                self.thought_chain.append(ThoughtStep(
                    thought=thought,
                    action="FINAL",
                    observation=final_answer
                ))
                
                return AgentResult(
                    answer=final_answer,
                    thought_chain=self.thought_chain,
                    tools_used=tools_used,
                    agent_type=AgentType.REACT,
                    success=True
                )
            
            # Execute action
            if action_match:
                action = action_match.group(1).strip()
                action_input = input_match.group(1).strip() if input_match else ""
                
                observation = self.execute_tool(action, action_input)
                tools_used.append(action)
                
                self.thought_chain.append(ThoughtStep(
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=observation
                ))
                
                # Add observation to conversation
                conversation.append({"role": "assistant", "content": response})
                conversation.append({"role": "user", "content": f"OBSERVATION: {observation}"})
            else:
                # No action parsed, try to extract answer
                self.thought_chain.append(ThoughtStep(thought=thought or response))
                break
        
        # Max steps reached - generate final answer
        final_prompt = f"""Based on the observations, provide a final answer to: {query}
        
Be direct and concise."""
        
        final_answer = llm_chat(final_prompt, temperature=0.3, max_tokens=300)
        
        return AgentResult(
            answer=final_answer,
            thought_chain=self.thought_chain,
            tools_used=tools_used,
            agent_type=AgentType.REACT,
            success=True
        )


# =============================================================================
# PLAN AND EXECUTE AGENT
# =============================================================================

class PlanAndExecuteAgent(BaseAgent):
    """
    Plan-and-Execute Agent: Creates plan first, then executes.
    
    Pattern: Plan → Execute Step 1 → ... → Execute Step N → Synthesize
    """
    
    def create_plan(self, query: str) -> List[Dict[str, str]]:
        """Create execution plan."""
        prompt = f"""Create a step-by-step plan to answer this question:

QUESTION: {query}

AVAILABLE TOOLS:
{self.get_tools_prompt()}

Create a plan with 2-4 steps. Format:
STEP 1: [action description] | TOOL: [tool_name] | INPUT: [input]
STEP 2: [action description] | TOOL: [tool_name] | INPUT: [input]
...

Keep it simple and focused."""

        response = llm_chat(prompt, temperature=0.2, max_tokens=300)
        
        # Parse plan
        plan = []
        for line in response.split('\n'):
            if 'STEP' in line.upper() and 'TOOL:' in line:
                try:
                    parts = line.split('|')
                    step_desc = parts[0].split(':')[1].strip() if ':' in parts[0] else parts[0].strip()
                    tool = parts[1].split(':')[1].strip().lower() if len(parts) > 1 else ""
                    tool_input = parts[2].split(':')[1].strip() if len(parts) > 2 else ""
                    
                    if tool in self.tools:
                        plan.append({
                            "description": step_desc,
                            "tool": tool,
                            "input": tool_input
                        })
                except:
                    pass
        
        # Default plan if parsing fails
        if not plan:
            plan = [{"description": "Search data", "tool": "search_data", "input": query}]
        
        return plan
    
    def process(self, query: str) -> AgentResult:
        """Run plan-and-execute."""
        self.thought_chain = []
        tools_used = []
        
        # Create plan
        plan = self.create_plan(query)
        self.thought_chain.append(ThoughtStep(
            thought=f"Created plan with {len(plan)} steps"
        ))
        
        # Execute plan
        observations = []
        for i, step in enumerate(plan):
            result = self.execute_tool(step["tool"], step["input"])
            observations.append(f"Step {i+1} ({step['tool']}): {result}")
            tools_used.append(step["tool"])
            
            self.thought_chain.append(ThoughtStep(
                thought=step["description"],
                action=step["tool"],
                action_input=step["input"],
                observation=result
            ))
        
        # Synthesize final answer
        synthesis_prompt = f"""Based on these observations, answer the question.

QUESTION: {query}

OBSERVATIONS:
{chr(10).join(observations)}

Provide a clear, direct answer synthesizing all the information."""

        final_answer = llm_chat(synthesis_prompt, temperature=0.3, max_tokens=400)
        
        return AgentResult(
            answer=final_answer,
            thought_chain=self.thought_chain,
            tools_used=tools_used,
            agent_type=AgentType.PLAN_EXECUTE,
            success=True
        )


# =============================================================================
# REFLEXION AGENT
# =============================================================================

class ReflexionAgent(BaseAgent):
    """
    Reflexion Agent: Self-reflection and improvement.
    
    Pattern: Act → Evaluate → Reflect → Improve → Act again (if needed)
    
    Inspired by Reflexion paper (Shinn et al., 2023)
    """
    
    def evaluate_answer(self, query: str, answer: str, context: str = "") -> Tuple[bool, str]:
        """Evaluate if answer is good enough."""
        prompt = f"""Evaluate this answer for quality and accuracy.

QUESTION: {query}
CONTEXT: {context[:300] if context else 'No context'}
ANSWER: {answer}

Evaluation criteria:
1. Does it directly answer the question?
2. Is it based on actual data/evidence?
3. Is it complete and clear?

Respond with:
VERDICT: PASS or FAIL
FEEDBACK: [one line of constructive feedback]"""

        response = llm_chat(prompt, temperature=0.2, max_tokens=100)
        
        is_pass = "PASS" in response.upper() and "FAIL" not in response.upper()
        return is_pass, response
    
    def reflect(self, query: str, previous_answer: str, feedback: str) -> str:
        """Generate reflection for improvement."""
        prompt = f"""Reflect on the previous attempt and how to improve.

QUESTION: {query}
PREVIOUS ANSWER: {previous_answer}
FEEDBACK: {feedback}

What should be done differently? Provide a brief reflection (2-3 sentences)."""

        return llm_chat(prompt, temperature=0.3, max_tokens=150)
    
    def process(self, query: str, max_attempts: int = 2) -> AgentResult:
        """Run reflexion loop."""
        self.thought_chain = []
        tools_used = []
        
        # Initial attempt using ReAct
        react_agent = ReActAgent(self.user_id)
        react_agent.tools = self.tools
        
        for attempt in range(max_attempts):
            # Execute
            result = react_agent.process(query)
            tools_used.extend(result.tools_used)
            
            self.thought_chain.append(ThoughtStep(
                thought=f"Attempt {attempt + 1}",
                observation=result.answer[:200]
            ))
            
            # Evaluate
            is_good, feedback = self.evaluate_answer(query, result.answer)
            
            if is_good:
                return AgentResult(
                    answer=result.answer,
                    thought_chain=self.thought_chain,
                    tools_used=tools_used,
                    agent_type=AgentType.REFLEXION,
                    success=True,
                    reflection=f"Passed after {attempt + 1} attempt(s)"
                )
            
            # Reflect and improve
            if attempt < max_attempts - 1:
                reflection = self.reflect(query, result.answer, feedback)
                self.thought_chain.append(ThoughtStep(
                    thought=f"Reflection: {reflection}"
                ))
        
        # Return best attempt
        return AgentResult(
            answer=result.answer,
            thought_chain=self.thought_chain,
            tools_used=tools_used,
            agent_type=AgentType.REFLEXION,
            success=True,
            reflection="Max attempts reached"
        )


# =============================================================================
# HYBRID AGENT (Auto-Select Best Strategy)
# =============================================================================

class HybridAgent(BaseAgent):
    """
    Hybrid Agent: Selects best agent strategy based on query.
    """
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agents = {
            AgentType.REACT: ReActAgent(user_id),
            AgentType.PLAN_EXECUTE: PlanAndExecuteAgent(user_id),
            AgentType.REFLEXION: ReflexionAgent(user_id)
        }
    
    def select_strategy(self, query: str) -> AgentType:
        """Select best agent strategy."""
        q_lower = query.lower()
        
        # Reflexion for high-stakes queries
        if any(kw in q_lower for kw in ['important', 'accurate', 'critical', 'exact', 'precise']):
            return AgentType.REFLEXION
        
        # Plan-and-Execute for multi-step queries
        if any(kw in q_lower for kw in ['and then', 'first', 'next', 'step by step', 'multiple']):
            return AgentType.PLAN_EXECUTE
        
        # Default to ReAct
        return AgentType.REACT
    
    def process(self, query: str) -> AgentResult:
        """Run with auto-selected strategy."""
        strategy = self.select_strategy(query)
        logger.info(f"🤖 Hybrid Agent selected: {strategy.value}")
        
        agent = self.agents.get(strategy, self.agents[AgentType.REACT])
        result = agent.process(query)
        
        # Mark as hybrid
        result.thought_chain.insert(0, ThoughtStep(
            thought=f"Selected strategy: {strategy.value}"
        ))
        
        return result


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def deep_agent_query(user_id: str, query: str, agent_type: str = "hybrid") -> Dict[str, Any]:
    """Quick function for deep agent query."""
    agents = {
        "react": ReActAgent,
        "plan": PlanAndExecuteAgent,
        "reflexion": ReflexionAgent,
        "hybrid": HybridAgent
    }
    
    agent_class = agents.get(agent_type.lower(), HybridAgent)
    agent = agent_class(user_id)
    result = agent.process(query)
    
    return {
        "answer": result.answer,
        "tools_used": result.tools_used,
        "agent_type": result.agent_type.value,
        "thought_chain": [
            {"thought": t.thought, "action": t.action, "observation": t.observation}
            for t in result.thought_chain
        ],
        "reflection": result.reflection
    }


# Module exports
__all__ = [
    'AgentType',
    'AgentTool',
    'AgentResult',
    'BaseAgent',
    'ReActAgent',
    'PlanAndExecuteAgent',
    'ReflexionAgent',
    'HybridAgent',
    'deep_agent_query'
]
