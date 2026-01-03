"""
Orchestrator Agent: The CEO of the Agent Network
=================================================

The Orchestrator is responsible for:
1. TASK DECOMPOSITION - Breaking complex queries into sub-tasks
2. AGENT DELEGATION - Assigning tasks to specialized agents
3. RESULT SYNTHESIS - Combining outputs from multiple agents
4. QUALITY CONTROL - Ensuring final output meets standards
5. ADAPTIVE PLANNING - Adjusting strategy based on results

This is the "brain" that coordinates all other agents.

Uses FREE APIs only (Groq/Gemini).
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm import chat

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the orchestrator can handle"""
    ANALYSIS = "analysis"          # Data analysis
    RETRIEVAL = "retrieval"        # Information retrieval
    VISUALIZATION = "visualization" # Chart/graph creation
    PREDICTION = "prediction"      # Forecasting
    COMPARISON = "comparison"      # Compare entities
    SUMMARY = "summary"            # Summarize information
    CALCULATION = "calculation"    # Math operations
    EXPLANATION = "explanation"    # Explain concepts
    ACTION = "action"              # Take an action (email, etc.)


class AgentType(Enum):
    """Types of agents available"""
    RESEARCHER = "researcher"       # Deep analysis
    DATA_SCIENTIST = "data_scientist"  # ML/predictions
    VISUALIZER = "visualizer"       # Charts
    WRITER = "writer"               # Reports/text
    CALCULATOR = "calculator"       # Computations
    VALIDATOR = "validator"         # Fact-checking
    EXECUTOR = "executor"           # Actions


@dataclass
class SubTask:
    """A sub-task to be executed"""
    id: str
    type: TaskType
    description: str
    assigned_agent: AgentType
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    priority: int = 1


@dataclass
class ExecutionPlan:
    """Complete execution plan for a query"""
    query: str
    sub_tasks: List[SubTask]
    execution_order: List[str]  # Task IDs in order
    estimated_time: str
    reasoning: str


class OrchestratorAgent:
    """
    The CEO of the agent network - decomposes, delegates, and synthesizes.
    
    Uses FREE APIs (Groq/Gemini).
    """
    
    def __init__(self):
        self.agents: Dict[AgentType, Callable] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_agent(self, agent_type: AgentType, handler: Callable):
        """Register a handler for an agent type"""
        self.agents[agent_type] = handler
        logger.info(f"Registered agent: {agent_type.value}")
    
    async def decompose_query(self, query: str, context: str = "") -> ExecutionPlan:
        """
        Decompose a complex query into sub-tasks.
        
        This is the "planning" phase.
        """
        
        prompt = f"""You are a task planning AI. Decompose this user query into sub-tasks.

USER QUERY: {query}

AVAILABLE CONTEXT:
{context[:2000] if context else "General business data available"}

AVAILABLE AGENTS:
- researcher: Deep analysis, multi-source synthesis
- data_scientist: ML predictions, forecasting, statistics
- visualizer: Charts, graphs, visualizations
- writer: Reports, summaries, explanations
- calculator: Math, aggregations, computations
- validator: Fact-checking, verification

Decompose the query into 1-5 sub-tasks. Each task should be:
1. Specific and actionable
2. Assigned to the most appropriate agent
3. Ordered by dependencies (what must run first)

Respond with JSON:
{{
    "sub_tasks": [
        {{
            "id": "task_1",
            "type": "analysis" | "retrieval" | "visualization" | "prediction" | "comparison" | "summary" | "calculation" | "explanation",
            "description": "what this task does",
            "agent": "researcher" | "data_scientist" | "visualizer" | "writer" | "calculator" | "validator",
            "dependencies": [],
            "priority": 1-5
        }}
    ],
    "execution_order": ["task_1", "task_2"],
    "estimated_time": "5 seconds",
    "reasoning": "why this plan makes sense"
}}"""

        try:
            result = chat(prompt, temperature=0.2)
            
            # Parse JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                sub_tasks = []
                for task_data in data.get("sub_tasks", []):
                    task = SubTask(
                        id=task_data.get("id", f"task_{len(sub_tasks)}"),
                        type=TaskType(task_data.get("type", "analysis")),
                        description=task_data.get("description", ""),
                        assigned_agent=AgentType(task_data.get("agent", "researcher")),
                        dependencies=task_data.get("dependencies", []),
                        priority=task_data.get("priority", 1)
                    )
                    sub_tasks.append(task)
                
                return ExecutionPlan(
                    query=query,
                    sub_tasks=sub_tasks,
                    execution_order=data.get("execution_order", [t.id for t in sub_tasks]),
                    estimated_time=data.get("estimated_time", "unknown"),
                    reasoning=data.get("reasoning", "")
                )
        
        except Exception as e:
            logger.error(f"Error decomposing query: {e}")
        
        # Fallback: single analysis task
        return ExecutionPlan(
            query=query,
            sub_tasks=[
                SubTask(
                    id="task_main",
                    type=TaskType.ANALYSIS,
                    description=query,
                    assigned_agent=AgentType.RESEARCHER
                )
            ],
            execution_order=["task_main"],
            estimated_time="5 seconds",
            reasoning="Fallback to single task execution"
        )
    
    async def execute_task(
        self,
        task: SubTask,
        context: str,
        previous_results: Dict[str, Any]
    ) -> Any:
        """
        Execute a single sub-task.
        """
        
        task.status = "running"
        logger.info(f"Executing task {task.id}: {task.description}")
        
        # Check if we have a registered agent
        if task.assigned_agent in self.agents:
            try:
                handler = self.agents[task.assigned_agent]
                result = await handler(task.description, context, previous_results)
                task.status = "completed"
                task.result = result
                return result
            except Exception as e:
                logger.error(f"Agent error: {e}")
                task.status = "failed"
                return {"error": str(e)}
        
        # Default: use LLM for the task
        return await self._default_task_handler(task, context, previous_results)
    
    async def _default_task_handler(
        self,
        task: SubTask,
        context: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Default handler when no specific agent is registered.
        Uses LLM to handle the task.
        """
        
        prev_context = ""
        if previous_results:
            prev_context = "\n\nPREVIOUS RESULTS:\n" + json.dumps(previous_results, indent=2)[:1500]
        
        prompt = f"""You are a {task.assigned_agent.value} agent. Complete this task.

TASK: {task.description}

TASK TYPE: {task.type.value}

AVAILABLE DATA:
{context[:3000]}
{prev_context}

Complete the task and provide a clear, concise output.
If it's a calculation, show the math.
If it's analysis, provide insights.
If it's visualization, describe what chart to create.

YOUR OUTPUT:"""

        try:
            result = chat(prompt, temperature=0.3)
            task.status = "completed"
            task.result = {"output": result.strip()}
            return task.result
        except Exception as e:
            task.status = "failed"
            return {"error": str(e)}
    
    async def synthesize_results(
        self,
        query: str,
        plan: ExecutionPlan,
        results: Dict[str, Any]
    ) -> str:
        """
        Synthesize results from all sub-tasks into a final response.
        """
        
        results_summary = "\n\n".join([
            f"**{task.description}**:\n{json.dumps(results.get(task.id, {}), indent=2)[:500]}"
            for task in plan.sub_tasks
        ])
        
        prompt = f"""You are a response synthesizer. Combine these sub-task results into a final, coherent response.

ORIGINAL QUERY: {query}

SUB-TASK RESULTS:
{results_summary}

Create a clear, professional response that:
1. Directly answers the user's query
2. Integrates insights from all sub-tasks
3. Is concise and well-structured
4. Highlights key findings

FINAL RESPONSE:"""

        try:
            response = chat(prompt, temperature=0.3)
            return response.strip()
        except Exception as e:
            logger.error(f"Error synthesizing: {e}")
            # Fallback: just return the first result
            first_result = list(results.values())[0] if results else {}
            return first_result.get("output", "Unable to synthesize results.")
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        context: str
    ) -> Dict[str, Any]:
        """
        Execute all sub-tasks in the plan.
        """
        
        results: Dict[str, Any] = {}
        
        for task_id in plan.execution_order:
            # Find the task
            task = next((t for t in plan.sub_tasks if t.id == task_id), None)
            if not task:
                continue
            
            # Check dependencies
            for dep_id in task.dependencies:
                if dep_id not in results:
                    logger.warning(f"Dependency {dep_id} not ready for {task_id}")
            
            # Execute the task
            result = await self.execute_task(task, context, results)
            results[task_id] = result
        
        return results
    
    async def run(
        self,
        query: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Main entry point - execute a query end-to-end.
        
        Returns:
            {
                "response": str,
                "plan": ExecutionPlan,
                "sub_results": Dict,
                "execution_time": str
            }
        """
        
        start_time = datetime.now()
        
        # 1. Decompose the query
        logger.info(f"Orchestrator: Planning for query: {query[:50]}...")
        plan = await self.decompose_query(query, context)
        logger.info(f"Orchestrator: Created plan with {len(plan.sub_tasks)} tasks")
        
        # 2. Execute all tasks
        results = await self.execute_plan(plan, context)
        
        # 3. Synthesize final response
        response = await self.synthesize_results(query, plan, results)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Record in history
        self.execution_history.append({
            "query": query,
            "plan": plan,
            "results": results,
            "response": response,
            "time": execution_time,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "response": response,
            "plan": {
                "tasks": [
                    {
                        "id": t.id,
                        "type": t.type.value,
                        "agent": t.assigned_agent.value,
                        "description": t.description,
                        "status": t.status
                    }
                    for t in plan.sub_tasks
                ],
                "reasoning": plan.reasoning
            },
            "sub_results": results,
            "execution_time": f"{execution_time:.2f}s"
        }
    
    def get_plan_summary(self, plan: ExecutionPlan) -> str:
        """
        Get human-readable plan summary.
        """
        
        summary = f"📋 **Execution Plan** ({plan.estimated_time})\n\n"
        
        for i, task in enumerate(plan.sub_tasks, 1):
            status_emoji = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(task.status, "⏳")
            
            summary += f"{i}. {status_emoji} [{task.assigned_agent.value}] {task.description}\n"
        
        summary += f"\n💡 {plan.reasoning}"
        
        return summary


# Convenience function
async def orchestrate_query(
    query: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    Simple interface to orchestrate a query.
    """
    
    orchestrator = OrchestratorAgent()
    return await orchestrator.run(query, context)


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        query = "Compare Q3 and Q4 revenue, identify the main driver of growth, and create a visualization"
        
        context = """
        Q3 2024: Revenue $1.4M, Expenses $1.2M, Customers: 1,100
        Q4 2024: Revenue $2.5M, Expenses $1.8M, Customers: 1,250
        Main products: Product A ($1.5M Q4), Product B ($800K Q4), Services ($200K Q4)
        """
        
        result = await orchestrate_query(query, context)
        
        print("=== PLAN ===")
        print(json.dumps(result["plan"], indent=2))
        
        print("\n=== RESPONSE ===")
        print(result["response"])
        
        print(f"\n⏱️ Execution time: {result['execution_time']}")
    
    asyncio.run(test())
