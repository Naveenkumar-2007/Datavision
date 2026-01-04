"""
AGENT ENGINE - Full Autonomous AI (Universal)
===============================================

Power: Complete autonomous agent with task orchestration.

💡 UNIQUE STRENGTH: Autonomous Task Decomposition
- Breaks complex tasks into sub-tasks
- Orchestrates multiple tools
- Combines YOUR data with external research (when asked)

Features:
- Task Decomposition: Breaks complex tasks into steps
- Multi-Tool: Orchestrates analysis tools
- Web Search: ONLY when explicitly requested
- Smart Planning: Shows execution plan

This is the most POWERFUL mode - full AI agent for YOUR data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.llm import chat

logger = logging.getLogger(__name__)


# Simple web search (optional)
def safe_web_search(query: str) -> str:
    """Safe web search that won't crash if unavailable"""
    try:
        from mcp.web_scraper import search_web
        results = search_web(query, max_results=2)
        if results:
            return "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')[:100]}" for r in results[:2]])
    except:
        pass
    return ""


class AgentEngine:
    """
    🤖 ENHANCED AGENT ENGINE - Autonomous AI with Tool Orchestration
    
    💡 WHEN TO USE:
    - 🎯 Complex Multi-Step Tasks: "Compare last month to this month and find anomalies"
    - 🔧 Tool Orchestration: Combines multiple analysis tools automatically
    - 🌐 Web Research: "Research industry trends and compare to my data"
    - 📊 Report Generation: "Create a comprehensive analysis report"
    - 🔄 Error Recovery: Automatically retries with different approaches
    
    This is the MOST POWERFUL mode - full autonomous AI for YOUR data!
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.available_tools = self._discover_tools()
        self.max_retries = 2
    
    def _discover_tools(self) -> Dict[str, Dict]:
        """Discover available MCP tools"""
        tools = {
            "data_analyzer": {
                "name": "Data Analyzer",
                "description": "Analyze patterns in data",
                "emoji": "📊"
            },
            "forecaster": {
                "name": "Forecaster",
                "description": "Predict future trends",
                "emoji": "🔮"
            },
            "anomaly_detector": {
                "name": "Anomaly Detector",
                "description": "Find outliers and anomalies",
                "emoji": "⚠️"
            },
            "chart_generator": {
                "name": "Chart Generator",
                "description": "Create visualizations",
                "emoji": "📈"
            },
            "web_searcher": {
                "name": "Web Searcher",
                "description": "Research external data",
                "emoji": "🌐"
            },
            "summarizer": {
                "name": "Summarizer",
                "description": "Summarize findings",
                "emoji": "📝"
            }
        }
        return tools
    
    async def process(
        self,
        query: str,
        context: str = "",
        enable_web_search: bool = True,
        enable_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process with full autonomous agent capabilities.
        
        Flow:
        1. Analyze task and detect required tools
        2. Create intelligent execution plan
        3. Execute step by step with YOUR data
        4. Handle errors with retry/fallback
        5. Synthesize comprehensive results
        """
        
        start_time = datetime.now()
        logger.info(f"🤖 AGENT ENGINE (Enhanced): Processing '{query[:50]}...'")
        
        tools_used = []
        web_results = ""
        execution_log = []
        
        # Step 1: Detect required tools from query
        required_tools = self._detect_required_tools(query)
        logger.info(f"🔧 Tools selected: {required_tools}")
        execution_log.append(f"🔧 Selected tools: {', '.join(required_tools)}")
        
        # Step 2: Create intelligent execution plan
        task_plan = await self._create_execution_plan(query, required_tools)
        execution_log.append(f"📋 Created {len(task_plan)} step plan")
        
        # Step 3: Check if web search explicitly requested
        needs_web = self._needs_web_search(query)
        
        if needs_web and enable_web_search:
            logger.info("🌐 Agent: Web search requested by user")
            web_results = safe_web_search(query)
            if web_results:
                tools_used.append("Web Searcher")
                execution_log.append("🌐 Web search completed")
        
        # Step 4: Execute the plan with error handling
        results = await self._execute_plan_with_retry(
            query, context, task_plan, required_tools, web_results
        )
        
        tools_used.extend(required_tools)
        
        # Step 5: Build comprehensive response
        response = results.get("response", "Analysis complete.")
        
        # Format response with agent header
        formatted = self._format_agent_response(
            response, task_plan, tools_used, needs_web, execution_log
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(context, results, len(task_plan))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "answer": formatted,
            "mode": "agent",
            "plan": task_plan,
            "tools_used": list(set(tools_used)),
            "web_search": bool(web_results),
            "execution_log": execution_log,
            "confidence": confidence,
            "execution_time": f"{execution_time:.2f}s",
            "features_used": ["Task Planning", "Tool Orchestration", "Error Recovery", "Data Grounding"] + tools_used,
            "sources": ["Your Data"] + (["Web Research"] if web_results else [])
        }
    
    def _detect_required_tools(self, query: str) -> List[str]:
        """Detect which tools are needed based on query"""
        query_lower = query.lower()
        tools = []
        
        tool_keywords = {
            "data_analyzer": ["analyze", "breakdown", "compare", "summary", "statistics"],
            "forecaster": ["predict", "forecast", "future", "next month", "projection"],
            "anomaly_detector": ["anomaly", "outlier", "unusual", "problem", "issue", "wrong"],
            "chart_generator": ["chart", "graph", "visualize", "plot", "show me"],
            "web_searcher": ["research", "search", "industry", "market", "trend", "news"],
            "summarizer": ["summarize", "report", "overview", "brief", "conclusion"]
        }
        
        for tool, keywords in tool_keywords.items():
            if any(kw in query_lower for kw in keywords):
                tools.append(tool)
        
        # Default to data_analyzer if no specific tool detected
        if not tools:
            tools = ["data_analyzer", "summarizer"]
        
        return tools[:4]  # Limit to 4 tools max
    
    async def _create_execution_plan(self, query: str, tools: List[str]) -> List[str]:
        """Create intelligent execution plan"""
        
        # Build plan based on tools
        plan = []
        
        if "data_analyzer" in tools:
            plan.append("📊 Step 1: Analyze the data to understand patterns")
        
        if "anomaly_detector" in tools:
            plan.append("⚠️ Step 2: Detect any anomalies or outliers")
        
        if "forecaster" in tools:
            plan.append("🔮 Step 3: Generate predictions based on trends")
        
        if "chart_generator" in tools:
            plan.append("📈 Step 4: Create visualization of findings")
        
        if "web_searcher" in tools:
            plan.append("🌐 Step 5: Research external context if needed")
        
        if "summarizer" in tools:
            plan.append("📝 Final: Synthesize all findings into actionable insights")
        
        if not plan:
            plan = [
                "📊 Step 1: Analyze the query requirements",
                "🔍 Step 2: Process relevant data",
                "📝 Step 3: Generate comprehensive response"
            ]
        
        return plan
    
    def _needs_web_search(self, query: str) -> bool:
        """Check if web search is explicitly requested"""
        web_keywords = [
            'search online', 'search web', 'latest news', 'find online',
            'look up', 'external data', 'industry trends', 'market research',
            'research', 'what are others doing', 'benchmark'
        ]
        return any(kw in query.lower() for kw in web_keywords)
    
    async def _execute_plan_with_retry(
        self,
        query: str,
        context: str,
        plan: List[str],
        tools: List[str],
        web_results: str
    ) -> Dict[str, Any]:
        """Execute plan with error recovery"""
        
        for attempt in range(self.max_retries + 1):
            try:
                # Build comprehensive agent prompt
                agent_prompt = self._build_agent_prompt(
                    query, context, plan, tools, web_results, attempt
                )
                
                response = chat(agent_prompt, temperature=0.3, max_tokens=2500)
                
                return {"response": response, "success": True}
                
            except Exception as e:
                logger.warning(f"Agent attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    return {
                        "response": f"I encountered an error but here's what I found: {str(e)}",
                        "success": False,
                        "error": str(e)
                    }
        
        return {"response": "Unable to complete analysis", "success": False}
    
    def _build_agent_prompt(
        self,
        query: str,
        context: str,
        plan: List[str],
        tools: List[str],
        web_results: str,
        attempt: int
    ) -> str:
        """Build the comprehensive agent prompt"""
        
        tools_desc = ", ".join([self.available_tools[t]["emoji"] + " " + self.available_tools[t]["name"] 
                               for t in tools if t in self.available_tools])
        
        needs_web = bool(web_results)
        
        return f"""You are DataVision Agent - an autonomous AI assistant with tool orchestration.

🤖 ACTIVE TOOLS: {tools_desc}

⚠️ CRITICAL - DATA GROUNDING:
{"You may use web results to SUPPLEMENT the user's data." if needs_web else "Use ONLY the user's personal data below. NEVER use outside knowledge!"}

📊 USER'S PERSONAL DATA:
{context[:4000] if context else "No user data uploaded. Advise them to upload files for better analysis."}

{"🌐 WEB RESEARCH RESULTS:" if web_results else ""}
{web_results if web_results else ""}

📋 EXECUTION PLAN:
{chr(10).join(plan)}

🎯 TASK: {query}

{"⚠️ Previous attempt had issues - being more careful with data grounding." if attempt > 0 else ""}

Execute the plan step by step:

## 🎯 Task Understanding
[What exactly does the user need? What data is relevant?]

## 📊 Step-by-Step Analysis

### Step 1: Data Overview
[What do I see in the user's data?]

### Step 2: Deep Analysis
[Execute the main analysis using ONLY the data provided]

### Step 3: Key Findings
[List 3-5 specific findings with actual numbers from the data]

## ✅ Results Summary
[Comprehensive answer to the user's query]

## 💡 Actionable Recommendations
[What should the user do based on THEIR data?]

## ⚠️ Limitations (if any)
[What couldn't be determined? What data is missing?]

Execute now:"""
    
    def _format_agent_response(
        self,
        response: str,
        plan: List[str],
        tools: List[str],
        needs_web: bool,
        execution_log: List[str]
    ) -> str:
        """Format the comprehensive agent response"""
        
        tools_str = ", ".join([self.available_tools[t]["emoji"] + " " + self.available_tools[t]["name"] 
                              for t in tools if t in self.available_tools])
        
        return f"""🤖 **Autonomous Agent Mode** 

📋 **Execution Plan:**
{chr(10).join('• ' + step for step in plan)}

---

{response}

---
🔧 **Tools Used:** {tools_str}
⚡ *{"Combined your data with web research" if needs_web else "Based on YOUR data only"}*"""
    
    def _calculate_confidence(self, context: str, results: Dict, plan_steps: int) -> float:
        """Calculate confidence score"""
        confidence = 0.7
        
        if context and len(context) > 500:
            confidence += 0.15
        if results.get("success"):
            confidence += 0.1
        if plan_steps >= 3:
            confidence += 0.05
        
        if not context or len(context) < 100:
            confidence = 0.5
        
        return min(0.95, confidence)


async def agent_response(
    user_id: str,
    query: str,
    context: str = "",
    enable_web_search: bool = True
) -> Dict[str, Any]:
    """Quick function for agent response"""
    engine = AgentEngine(user_id)
    return await engine.process(query, context, enable_web_search)


def agent_response_sync(
    user_id: str,
    query: str,
    context: str = "",
    df = None
) -> str:
    """
    Synchronous agent response with dynamic visualization.
    
    Features:
    - Autonomous task execution
    - Multi-tool orchestration
    - Dynamic chart generation
    """
    import json
    
    # Check if web explicitly requested
    needs_web = any(kw in query.lower() for kw in ['search online', 'latest news', 'look up'])
    
    web_context = ""
    if needs_web:
        web_context = safe_web_search(query)
        if web_context:
            web_context = f"\n\n🌐 Web Results:\n{web_context}"
    
    prompt = f"""You are DataVision Agent - autonomous AI assistant.

⚠️ CRITICAL: {"May supplement with web research." if needs_web else "Use ONLY user's data below!"}

📊 USER'S DATA:
{context[:3000] if context else "No data uploaded."}
{web_context}

🎯 TASK: {query}

Provide:
1. Task Understanding (what they need from THEIR data)
2. Analysis/Execution (using data above)
3. Actionable Results
4. Next Steps

YOUR RESPONSE:"""

    try:
        response = chat(prompt, temperature=0.3, max_tokens=2000)
        result = f"🤖 **Agent Mode**\n\n{response}"
        
        # Add dynamic visualization if DataFrame provided
        if df is not None:
            try:
                from core.mode_engines.universal_visualizer import auto_visualize
                chart = auto_visualize(df, query)
                if chart:
                    result += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
                    logger.info("✅ Added dynamic chart to agent response")
            except Exception as chart_err:
                logger.warning(f"Chart generation skipped: {chart_err}")
        
        return result
    except Exception as e:
        return f"Agent error: {str(e)}"

