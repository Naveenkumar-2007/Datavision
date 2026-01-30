"""
🔬 DEEP RESEARCH AGENT - Claude-Style Deep Research System
==========================================================

A sophisticated multi-agent system for deep research and analysis.

Architecture (as shown in diagram):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌─────────────┐                    ┌─────────────┐       │
│   │  Planning   │◄──────────────────►│ Sub Agents  │       │
│   │    Tool     │                    │             │       │
│   └──────┬──────┘                    └──────┬──────┘       │
│          │                                  │               │
│          │        ┌─────────────┐          │               │
│          └───────►│ Deep Agents │◄─────────┘               │
│                   │ (Orchestrator)│                         │
│          ┌───────►│             │◄─────────┐               │
│          │        └─────────────┘          │               │
│          │                                  │               │
│   ┌──────┴──────┐                    ┌──────┴──────┐       │
│   │    File     │                    │   System    │       │
│   │   System    │                    │   Prompt    │       │
│   └─────────────┘                    └─────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Components:
- Planning Tool: Creates hierarchical execution plans
- Sub Agents: Specialized agents for different tasks
- File System: Read/write/analyze files
- System Prompt: Dynamic context and instruction management

Features:
- Multi-agent orchestration
- Hierarchical task decomposition
- File I/O capabilities
- Dynamic sub-agent spawning
- Research synthesis
- Source tracking
"""

import logging
import os
import json
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
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
# COMPONENT TYPES
# =============================================================================

class SubAgentType(Enum):
    """Types of specialized sub-agents."""
    RESEARCHER = "researcher"         # Deep research on topics
    ANALYST = "analyst"               # Data analysis
    WRITER = "writer"                 # Content generation
    CRITIC = "critic"                 # Evaluation and critique
    SYNTHESIZER = "synthesizer"       # Combine findings
    FACT_CHECKER = "fact_checker"     # Verify information
    CODER = "coder"                   # Code generation/analysis


class PlanStatus(Enum):
    """Status of execution plan steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A step in the execution plan."""
    step_id: int
    description: str
    agent_type: SubAgentType
    dependencies: List[int] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Hierarchical execution plan."""
    goal: str
    steps: List[PlanStep]
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def get_next_step(self) -> Optional[PlanStep]:
        """Get next executable step (dependencies met)."""
        completed_ids = {s.step_id for s in self.steps if s.status == PlanStatus.COMPLETED}
        
        for step in self.steps:
            if step.status == PlanStatus.PENDING:
                if all(dep in completed_ids for dep in step.dependencies):
                    return step
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps are done."""
        return all(s.status in [PlanStatus.COMPLETED, PlanStatus.SKIPPED] for s in self.steps)


@dataclass
class ResearchResult:
    """Result from deep research."""
    query: str
    findings: List[str]
    sources: List[str]
    confidence: float
    synthesis: str
    plan_trace: List[str]
    sub_agent_results: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PLANNING TOOL
# =============================================================================

class PlanningTool:
    """
    Creates hierarchical execution plans for complex tasks.
    
    Decomposes goals into sub-tasks with dependencies.
    """
    
    def __init__(self):
        self.plans: List[ExecutionPlan] = []
    
    def create_plan(self, goal: str, context: str = "") -> ExecutionPlan:
        """Create execution plan using LLM."""
        prompt = f"""Create a detailed execution plan for this goal.

GOAL: {goal}
CONTEXT: {context if context else "No additional context"}

Break this into 3-6 concrete steps. For each step, specify:
1. What needs to be done
2. Which type of agent should do it:
   - researcher: Deep research on topics
   - analyst: Data analysis  
   - writer: Content generation
   - critic: Evaluation
   - synthesizer: Combine findings
   - fact_checker: Verify information
   - coder: Code tasks
3. Dependencies (which previous steps must be completed first)

FORMAT (strict JSON):
{{
  "steps": [
    {{"id": 1, "description": "...", "agent": "researcher", "depends_on": []}},
    {{"id": 2, "description": "...", "agent": "analyst", "depends_on": [1]}},
    ...
  ]
}}"""

        response = llm_chat(prompt, temperature=0.2, max_tokens=500)
        
        # Parse response
        steps = self._parse_plan(response, goal)
        
        plan = ExecutionPlan(goal=goal, steps=steps)
        self.plans.append(plan)
        
        return plan
    
    def _parse_plan(self, response: str, goal: str) -> List[PlanStep]:
        """Parse LLM response into plan steps."""
        steps = []
        
        try:
            # Extract JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                json_str = response[response.find("{"):response.rfind("}")+1]
            else:
                json_str = response
            
            data = json.loads(json_str)
            
            for s in data.get("steps", []):
                agent_type = SubAgentType.RESEARCHER  # Default
                agent_str = s.get("agent", "researcher").lower()
                for at in SubAgentType:
                    if at.value == agent_str:
                        agent_type = at
                        break
                
                steps.append(PlanStep(
                    step_id=s.get("id", len(steps) + 1),
                    description=s.get("description", ""),
                    agent_type=agent_type,
                    dependencies=s.get("depends_on", [])
                ))
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Plan parsing failed: {e}, using default plan")
            # Default plan
            steps = [
                PlanStep(1, f"Research: {goal}", SubAgentType.RESEARCHER),
                PlanStep(2, f"Analyze findings", SubAgentType.ANALYST, [1]),
                PlanStep(3, f"Synthesize results", SubAgentType.SYNTHESIZER, [2])
            ]
        
        return steps
    
    def update_step(self, plan: ExecutionPlan, step_id: int, 
                    status: PlanStatus, result: str = None):
        """Update a step's status."""
        for step in plan.steps:
            if step.step_id == step_id:
                step.status = status
                step.result = result
                break


# =============================================================================
# SUB AGENTS
# =============================================================================

class SubAgentFactory:
    """Factory for creating specialized sub-agents."""
    
    @staticmethod
    def create(agent_type: SubAgentType, user_id: str) -> 'BaseSubAgent':
        """Create a sub-agent of the specified type."""
        agents = {
            SubAgentType.RESEARCHER: ResearcherAgent,
            SubAgentType.ANALYST: AnalystSubAgent,
            SubAgentType.WRITER: WriterAgent,
            SubAgentType.CRITIC: CriticAgent,
            SubAgentType.SYNTHESIZER: SynthesizerAgent,
            SubAgentType.FACT_CHECKER: FactCheckerAgent,
            SubAgentType.CODER: CoderAgent
        }
        
        agent_class = agents.get(agent_type, ResearcherAgent)
        return agent_class(user_id)


class BaseSubAgent:
    """Base class for sub-agents."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.agent_type: SubAgentType = SubAgentType.RESEARCHER
    
    def execute(self, task: str, context: str = "") -> str:
        """Execute the task."""
        raise NotImplementedError


class ResearcherAgent(BaseSubAgent):
    """Deep research on topics using available data and knowledge."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agent_type = SubAgentType.RESEARCHER
    
    def execute(self, task: str, context: str = "") -> str:
        # Try to get data context
        data_context = ""
        try:
            from core.rag import rag_search
            data_context, sources = rag_search(self.user_id, task, k=5)
        except:
            pass
        
        prompt = f"""You are a Deep Research Agent. Research this topic thoroughly.

TASK: {task}

DATA FROM USER'S FILES:
{data_context if data_context else "No user data available"}

PREVIOUS CONTEXT:
{context if context else "No previous context"}

Provide comprehensive research findings with:
1. Key facts and insights
2. Data-backed observations (if data available)
3. Important patterns or trends
4. Source references

Be thorough but concise."""

        return llm_chat(prompt, temperature=0.3, max_tokens=600)


class AnalystSubAgent(BaseSubAgent):
    """Data analysis specialist."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agent_type = SubAgentType.ANALYST
    
    def execute(self, task: str, context: str = "") -> str:
        # Get user data statistics
        stats_context = ""
        try:
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(self.user_id)
            if df is not None and not df.empty:
                stats_context = f"""
Dataset: {len(df)} rows × {len(df.columns)} columns
Columns: {', '.join(df.columns.tolist()[:10])}
"""
                # Add numeric stats
                numeric_cols = df.select_dtypes(include=['number']).columns[:5]
                for col in numeric_cols:
                    stats_context += f"- {col}: mean={df[col].mean():,.2f}, sum={df[col].sum():,.2f}\n"
        except:
            pass
        
        prompt = f"""You are a Data Analyst Agent. Analyze this task.

TASK: {task}

DATA STATISTICS:
{stats_context if stats_context else "No data available"}

PREVIOUS FINDINGS:
{context if context else "No previous findings"}

Provide analytical insights:
1. Key metrics and values
2. Statistical observations
3. Patterns and anomalies
4. Data-driven conclusions

Use actual numbers from the data."""

        return llm_chat(prompt, temperature=0.2, max_tokens=500)


class WriterAgent(BaseSubAgent):
    """Content generation specialist."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agent_type = SubAgentType.WRITER
    
    def execute(self, task: str, context: str = "") -> str:
        prompt = f"""You are a Writer Agent. Create content for this task.

TASK: {task}

CONTEXT AND RESEARCH:
{context if context else "No context provided"}

Write clear, professional content that:
1. Is well-structured
2. Uses the provided research
3. Is engaging and informative
4. Includes key data points

Keep it concise but comprehensive."""

        return llm_chat(prompt, temperature=0.4, max_tokens=600)


class CriticAgent(BaseSubAgent):
    """Evaluation and critique specialist."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agent_type = SubAgentType.CRITIC
    
    def execute(self, task: str, context: str = "") -> str:
        prompt = f"""You are a Critic Agent. Evaluate this content critically.

TASK: {task}

CONTENT TO EVALUATE:
{context if context else "No content provided"}

Provide critical evaluation:
1. Strengths of the analysis
2. Weaknesses or gaps
3. Accuracy concerns
4. Suggestions for improvement

Be constructive but thorough."""

        return llm_chat(prompt, temperature=0.3, max_tokens=400)


class SynthesizerAgent(BaseSubAgent):
    """Combines findings from multiple sources."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agent_type = SubAgentType.SYNTHESIZER
    
    def execute(self, task: str, context: str = "") -> str:
        prompt = f"""You are a Synthesizer Agent. Combine and summarize findings.

TASK: {task}

FINDINGS TO SYNTHESIZE:
{context if context else "No findings provided"}

Create a unified synthesis that:
1. Combines key insights
2. Resolves contradictions
3. Highlights consensus
4. Provides actionable conclusions

Be comprehensive but concise."""

        return llm_chat(prompt, temperature=0.3, max_tokens=500)


class FactCheckerAgent(BaseSubAgent):
    """Verifies information accuracy."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agent_type = SubAgentType.FACT_CHECKER
    
    def execute(self, task: str, context: str = "") -> str:
        prompt = f"""You are a Fact Checker Agent. Verify the accuracy of claims.

TASK: {task}

CLAIMS TO VERIFY:
{context if context else "No claims provided"}

For each claim:
1. ✅ Verified - backed by data
2. ⚠️ Uncertain - needs more evidence
3. ❌ Incorrect - contradicts data

Provide verification results with reasoning."""

        return llm_chat(prompt, temperature=0.2, max_tokens=400)


class CoderAgent(BaseSubAgent):
    """Code generation and analysis."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.agent_type = SubAgentType.CODER
    
    def execute(self, task: str, context: str = "") -> str:
        prompt = f"""You are a Coder Agent. Handle code-related tasks.

TASK: {task}

CONTEXT:
{context if context else "No context provided"}

Provide:
1. Code solution (if applicable)
2. Explanation of approach
3. Key considerations

Format code in markdown code blocks."""

        return llm_chat(prompt, temperature=0.2, max_tokens=600)


# =============================================================================
# FILE SYSTEM TOOL
# =============================================================================

class FileSystemTool:
    """
    File system capabilities for deep research.
    
    Features:
    - Read user's uploaded files
    - Analyze file contents
    - Search across files
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def list_files(self) -> List[str]:
        """List available user files."""
        try:
            from utils.paths import get_user_paths
            paths = get_user_paths(self.user_id)
            files = []
            for ext in ['*.csv', '*.xlsx', '*.pdf', '*.txt']:
                import glob
                files.extend(glob.glob(os.path.join(paths.get('uploads', ''), ext)))
            return [os.path.basename(f) for f in files]
        except:
            return []
    
    def read_file_summary(self, filename: str) -> str:
        """Get summary of a file."""
        try:
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(self.user_id)
            
            if df is not None:
                return f"""File Summary:
- Rows: {len(df)}
- Columns: {len(df.columns)}
- Columns: {', '.join(df.columns.tolist()[:15])}
- Memory: {df.memory_usage(deep=True).sum() / 1024:.1f} KB"""
            return "File not found or not readable"
        except Exception as e:
            return f"Error reading file: {str(e)[:100]}"
    
    def search_in_files(self, query: str) -> str:
        """Search for information in user's files."""
        try:
            from core.rag import rag_search
            context, sources = rag_search(self.user_id, query, k=5)
            return context if context else "No matching content found"
        except Exception as e:
            return f"Search error: {str(e)[:100]}"


# =============================================================================
# SYSTEM PROMPT MANAGER
# =============================================================================

class SystemPromptManager:
    """
    Manages dynamic system prompts for the deep agent.
    
    Maintains context across interactions and agent executions.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_prompt = """You are a Deep Research Agent - an advanced AI system capable of:
1. Breaking down complex research tasks
2. Coordinating specialized sub-agents
3. Synthesizing findings from multiple sources
4. Providing accurate, data-grounded insights

Always prioritize:
- User's data over general knowledge
- Accuracy over speculation
- Concise, actionable insights"""
        
        self.context_stack: List[str] = []
        self.research_history: List[str] = []
    
    def get_full_prompt(self, task: str = "") -> str:
        """Get complete system prompt with context."""
        prompt = self.base_prompt
        
        if self.context_stack:
            prompt += "\n\nACCUMULATED CONTEXT:\n"
            prompt += "\n".join(self.context_stack[-5:])  # Last 5 contexts
        
        if task:
            prompt += f"\n\nCURRENT TASK: {task}"
        
        return prompt
    
    def add_context(self, context: str):
        """Add context to the stack."""
        self.context_stack.append(context)
    
    def add_research(self, finding: str):
        """Add research finding to history."""
        self.research_history.append(finding)
    
    def get_research_summary(self) -> str:
        """Get summary of research history."""
        if not self.research_history:
            return "No research conducted yet."
        return "\n---\n".join(self.research_history[-10:])
    
    def clear(self):
        """Clear all context."""
        self.context_stack = []
        self.research_history = []


# =============================================================================
# DEEP RESEARCH AGENT (MAIN ORCHESTRATOR)
# =============================================================================

class DeepResearchAgent:
    """
    🔬 DEEP RESEARCH AGENT - Claude-Style Research System
    
    Main orchestrator that coordinates:
    - Planning Tool: Creates execution plans
    - Sub Agents: Specialized task executors
    - File System: Data access
    - System Prompt: Context management
    
    Flow:
    1. Receive research query
    2. Planning Tool creates hierarchical plan
    3. Sub Agents execute each step
    4. File System provides data context
    5. System Prompt maintains context
    6. Synthesize final results
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Initialize components
        self.planning_tool = PlanningTool()
        self.file_system = FileSystemTool(user_id)
        self.system_prompt = SystemPromptManager(user_id)
        
        # Track execution
        self.execution_trace: List[str] = []
    
    def research(self, query: str, depth: str = "standard") -> ResearchResult:
        """
        Execute deep research on a query.
        
        Args:
            query: Research question or topic
            depth: "quick" (1-2 steps), "standard" (3-4 steps), "deep" (5+ steps)
        
        Returns:
            ResearchResult with findings, sources, and synthesis
        """
        self.execution_trace = []
        self.execution_trace.append(f"🔬 Starting deep research: {query}")
        
        # Get file context
        files = self.file_system.list_files()
        file_context = f"Available files: {', '.join(files[:5])}" if files else ""
        self.system_prompt.add_context(f"User has {len(files)} files available")
        
        # Create execution plan
        self.execution_trace.append("📋 Creating execution plan...")
        plan = self.planning_tool.create_plan(
            goal=query,
            context=file_context
        )
        self.execution_trace.append(f"📋 Plan created with {len(plan.steps)} steps")
        
        # Execute plan
        findings = []
        sources = []
        sub_agent_results = {}
        
        while not plan.is_complete():
            step = plan.get_next_step()
            if not step:
                break
            
            self.execution_trace.append(f"▶️ Step {step.step_id}: {step.description}")
            
            # Update status
            self.planning_tool.update_step(plan, step.step_id, PlanStatus.IN_PROGRESS)
            
            # Create and execute sub-agent
            try:
                sub_agent = SubAgentFactory.create(step.agent_type, self.user_id)
                
                # Build context from previous steps
                prev_context = "\n\n".join([
                    s.result for s in plan.steps 
                    if s.status == PlanStatus.COMPLETED and s.result
                ])
                
                # Execute
                result = sub_agent.execute(step.description, prev_context)
                
                # Store result
                self.planning_tool.update_step(plan, step.step_id, PlanStatus.COMPLETED, result)
                sub_agent_results[f"step_{step.step_id}"] = {
                    "agent": step.agent_type.value,
                    "result": result[:500]  # Truncate for storage
                }
                
                # Add to findings
                findings.append(result)
                sources.append(f"{step.agent_type.value}_agent")
                
                # Update system context
                self.system_prompt.add_research(f"Step {step.step_id}: {result[:200]}")
                
                self.execution_trace.append(f"✅ Step {step.step_id} completed")
                
            except Exception as e:
                self.planning_tool.update_step(plan, step.step_id, PlanStatus.FAILED, error=str(e))
                self.execution_trace.append(f"❌ Step {step.step_id} failed: {str(e)[:100]}")
        
        plan.completed_at = datetime.now()
        
        # Final synthesis
        self.execution_trace.append("🔄 Synthesizing results...")
        synthesizer = SynthesizerAgent(self.user_id)
        synthesis = synthesizer.execute(
            f"Synthesize research findings for: {query}",
            "\n\n---\n\n".join(findings)
        )
        
        self.execution_trace.append("✅ Research complete")
        
        # Calculate confidence
        completed_steps = sum(1 for s in plan.steps if s.status == PlanStatus.COMPLETED)
        confidence = completed_steps / len(plan.steps) if plan.steps else 0.5
        
        return ResearchResult(
            query=query,
            findings=findings,
            sources=list(set(sources)),
            confidence=confidence,
            synthesis=synthesis,
            plan_trace=self.execution_trace,
            sub_agent_results=sub_agent_results
        )
    
    def format_response(self, result: ResearchResult) -> str:
        """Format research result for display."""
        response = f"""## 🔬 Deep Research Results

**Query:** {result.query}
**Confidence:** {result.confidence:.0%}

---

### 📊 Synthesis

{result.synthesis}

---

### 📋 Research Process

"""
        for trace in result.plan_trace:
            response += f"- {trace}\n"
        
        response += f"\n---\n**Sources:** {', '.join(result.sources)}"
        
        return response


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def deep_research(user_id: str, query: str, depth: str = "standard") -> Dict[str, Any]:
    """Quick function for deep research."""
    agent = DeepResearchAgent(user_id)
    result = agent.research(query, depth)
    
    return {
        "query": result.query,
        "synthesis": result.synthesis,
        "findings": result.findings,
        "sources": result.sources,
        "confidence": result.confidence,
        "trace": result.plan_trace
    }


def deep_research_formatted(user_id: str, query: str) -> str:
    """Deep research with formatted response."""
    agent = DeepResearchAgent(user_id)
    result = agent.research(query)
    return agent.format_response(result)


# Module exports
__all__ = [
    'DeepResearchAgent',
    'PlanningTool',
    'SubAgentFactory',
    'FileSystemTool',
    'SystemPromptManager',
    'ResearchResult',
    'ExecutionPlan',
    'SubAgentType',
    'deep_research',
    'deep_research_formatted'
]
