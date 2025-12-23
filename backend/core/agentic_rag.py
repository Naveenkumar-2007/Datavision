"""
Agentic RAG System
===================

Agentic RAG goes beyond simple retrieval:
- Agent decides WHAT to retrieve
- Agent decides WHEN to retrieve
- Agent can use TOOLS (SQL, calculations, charts)
- Agent can ITERATE and refine answers

Flow:
1. Agent analyzes query → decides action plan
2. Agent executes tools (retrieve, calculate, visualize)
3. Agent self-reflects and iterates if needed
4. Agent produces final response with text + charts
"""

import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json


class AgentAction(Enum):
    """Actions the agent can take"""
    RETRIEVE = "retrieve"       # Get documents from vector store
    SQL_QUERY = "sql_query"     # Execute SQL on data
    CALCULATE = "calculate"     # Perform calculations
    VISUALIZE = "visualize"     # Generate chart
    COMPARE = "compare"         # Compare multiple items
    SUMMARIZE = "summarize"     # Summarize retrieved info
    ANSWER = "answer"           # Final answer


@dataclass
class AgentStep:
    """A single step in agent execution"""
    action: AgentAction
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    reasoning: str = ""


class AgenticRAG:
    """
    Agentic RAG - The agent decides how to answer queries
    using available tools and iterative refinement.
    """
    
    def __init__(self, user_id: str, tools: Dict[str, Callable] = None):
        self.user_id = user_id
        self.tools = tools or {}
        self.execution_log: List[AgentStep] = []
        self.max_iterations = 3
        
    def register_tool(self, name: str, func: Callable):
        """Register a tool the agent can use"""
        self.tools[name] = func
        
    def plan_execution(self, query: str) -> List[AgentAction]:
        """
        Analyze query and create execution plan.
        Returns ordered list of actions to take.
        """
        query_lower = query.lower()
        plan = []
        
        # Always start with retrieval
        plan.append(AgentAction.RETRIEVE)
        
        # Detect if SQL needed
        if any(kw in query_lower for kw in ['total', 'sum', 'count', 'average', 'max', 'min']):
            plan.append(AgentAction.SQL_QUERY)
            
        # Detect if calculation needed
        if any(kw in query_lower for kw in ['calculate', 'compute', 'percentage', 'growth', 'ratio']):
            plan.append(AgentAction.CALCULATE)
            
        # Detect if comparison needed
        if any(kw in query_lower for kw in ['compare', 'vs', 'versus', 'difference', 'between']):
            plan.append(AgentAction.COMPARE)
            
        # Detect if visualization needed
        if any(kw in query_lower for kw in ['chart', 'graph', 'visualize', 'trend', 'show me', 'plot']):
            plan.append(AgentAction.VISUALIZE)
            
        # Detect if summary needed
        if any(kw in query_lower for kw in ['summary', 'overview', 'highlight', 'key']):
            plan.append(AgentAction.SUMMARIZE)
            
        # Always end with answer
        plan.append(AgentAction.ANSWER)
        
        return plan
    
    async def execute_tool(self, action: AgentAction, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool/action"""
        tool_name = action.value
        
        if tool_name in self.tools:
            try:
                result = await self.tools[tool_name](input_data)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Default implementations
        if action == AgentAction.RETRIEVE:
            return {"success": True, "result": input_data.get("context", "")}
        elif action == AgentAction.ANSWER:
            return {"success": True, "result": input_data.get("accumulated_data", {})}
            
        return {"success": False, "error": f"Tool {tool_name} not implemented"}
    
    async def run(self, query: str, initial_context: str = "") -> Dict[str, Any]:
        """
        Main execution loop - runs the agent to answer the query.
        
        Returns:
            {
                "answer": str,
                "chart": optional chart data,
                "steps": execution log,
                "sources": list of sources
            }
        """
        self.execution_log = []
        
        # Plan execution
        plan = self.plan_execution(query)
        print(f"🤖 Agent plan: {[a.value for a in plan]}")
        
        # Accumulated data through execution
        accumulated = {
            "query": query,
            "context": initial_context,
            "retrieved": [],
            "calculations": [],
            "chart_data": None
        }
        
        # Execute each action
        for action in plan:
            step = AgentStep(
                action=action,
                input_data={"query": query, "accumulated_data": accumulated},
                reasoning=f"Executing {action.value} based on query analysis"
            )
            
            result = await self.execute_tool(action, step.input_data)
            step.output_data = result
            self.execution_log.append(step)
            
            # Update accumulated data based on action result
            if result.get("success") and result.get("result"):
                if action == AgentAction.RETRIEVE:
                    accumulated["retrieved"].append(result["result"])
                elif action == AgentAction.CALCULATE:
                    accumulated["calculations"].append(result["result"])
                elif action == AgentAction.VISUALIZE:
                    accumulated["chart_data"] = result["result"]
        
        return {
            "answer": accumulated.get("final_answer", ""),
            "chart": accumulated.get("chart_data"),
            "steps": [{"action": s.action.value, "success": s.output_data.get("success")} 
                      for s in self.execution_log],
            "sources": accumulated.get("retrieved", [])
        }
    
    def get_execution_summary(self) -> str:
        """Get human-readable execution summary"""
        summary = "🤖 Agent Execution:\n"
        for step in self.execution_log:
            status = "✅" if step.output_data and step.output_data.get("success") else "❌"
            summary += f"  {status} {step.action.value}\n"
        return summary


def create_agentic_rag_prompt(query: str, context: str, agent_plan: List[str]) -> str:
    """Create enhanced prompt for agentic RAG - produces clean, concise output"""
    
    return f"""You are a professional Business Analyst. Answer the user's question using ONLY the data provided below.

## DATA (use ONLY these exact numbers):
{context[:6000]}

## QUESTION: {query}

## CRITICAL RULES:
1. Use ONLY numbers and values that appear in the DATA section above
2. DO NOT invent or make up any numbers - if data isn't available, say so
3. Give a clean, concise answer - no step-by-step explanations
4. A chart will be generated automatically - do not describe chart generation
5. Format numbers with commas (e.g., 121,057,121 not 121057121)
6. Be direct and professional like a real business analyst

## YOUR RESPONSE (clean, data-driven):"""


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = AgenticRAG(user_id="test_user")
        
        # Test plan generation
        queries = [
            "What is the total salary?",
            "Compare Engineering vs Sales salary and show a chart",
            "Calculate the percentage growth and summarize"
        ]
        
        for q in queries:
            plan = agent.plan_execution(q)
            print(f"\nQuery: {q}")
            print(f"Plan: {[a.value for a in plan]}")
    
    asyncio.run(test())
