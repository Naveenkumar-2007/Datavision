# Production-Grade Business AI Engine
# Architected using ChatGPT/Claude core principles
"""
This is the ORCHESTRATION LAYER - not a model.

Components:
1. Memory Systems (3 layers)
2. Query Understanding Pipeline (7 steps)
3. Data Governance Engine
4. Visualization Engine
5. Self-Audit System
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# =============================================================================
# 1️⃣ FOUNDATIONAL TRUTH RULE
# =============================================================================

class TruthSource(Enum):
    """All valid sources of truth"""
    UPLOADED_DATA = "uploaded_data"
    CONVERSATION_MEMORY = "conversation_memory"
    VERIFIED_TOOL_OUTPUT = "verified_tool_output"
    USER_INPUT = "user_input"
    NONE = "none"  # No valid source - REFUSE to answer


@dataclass
class GroundedClaim:
    """Every claim must be grounded in a source"""
    claim: str
    source: TruthSource
    evidence: str  # Exact data/quote supporting the claim
    confidence: float  # 0-1
    traceable_to: Optional[str] = None  # File/row/column path


# =============================================================================
# 2️⃣ STATEFUL MEMORY SYSTEM (WHY CHATGPT WORKS)
# =============================================================================

@dataclass
class ConversationTurn:
    """Single conversation turn"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    topic: Optional[str] = None
    result_type: Optional[str] = None  # "text", "chart", "table"
    chart_type: Optional[str] = None
    data_shown: Optional[Dict] = None
    metrics_computed: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnalyticalState:
    """State of previous computations"""
    last_computation: Optional[str] = None
    computed_metrics: Dict[str, float] = field(default_factory=dict)
    generated_charts: List[Dict] = field(default_factory=list)
    derived_insights: List[str] = field(default_factory=list)
    data_schema: Optional[Dict] = None


class ThreeLayerMemory:
    """
    Synchronized 3-layer memory system.
    
    Layer 1: Conversation Memory - All turns, references
    Layer 2: Persistent Knowledge - Files, schemas, metrics
    Layer 3: Analytical State - Computations, charts, insights
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        # Layer 1: Conversation
        self.conversation: List[ConversationTurn] = []
        
        # Layer 2: Persistent Knowledge
        self.uploaded_files: Dict[str, Dict] = {}  # filename -> schema
        self.learned_schemas: Dict[str, Dict] = {}
        self.known_metrics: Dict[str, float] = {}
        
        # Layer 3: Analytical State
        self.analytical_state = AnalyticalState()
    
    def add_turn(
        self, 
        role: str, 
        content: str,
        topic: str = None,
        result_type: str = None,
        chart_type: str = None,
        data_shown: Dict = None,
        metrics: Dict[str, float] = None
    ):
        """Add a conversation turn"""
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now(),
            topic=topic,
            result_type=result_type,
            chart_type=chart_type,
            data_shown=data_shown,
            metrics_computed=metrics or {}
        )
        self.conversation.append(turn)
        
        # Update analytical state
        if metrics:
            self.analytical_state.computed_metrics.update(metrics)
            self.known_metrics.update(metrics)
        
        if chart_type:
            self.analytical_state.generated_charts.append({
                "type": chart_type,
                "topic": topic,
                "timestamp": datetime.now().isoformat()
            })
    
    def resolve_reference(self, reference: str) -> Tuple[str, Dict]:
        """
        Resolve references like "above", "that chart", "earlier result".
        
        Returns: (resolved_content, metadata)
        """
        ref_lower = reference.lower()
        
        # Get recent assistant turns
        recent_assistant = [
            t for t in reversed(self.conversation[-10:]) 
            if t.role == "assistant"
        ]
        
        if not recent_assistant:
            return reference, {"resolved": False, "reason": "No previous context"}
        
        last = recent_assistant[0]
        
        # Reference patterns
        if any(r in ref_lower for r in ["above", "that", "this", "previous", "earlier"]):
            # Determine what was shown
            if last.chart_type:
                resolved = f"the {last.chart_type} chart showing {last.topic or 'data'}"
            elif last.result_type == "table":
                resolved = f"the table showing {last.topic or 'data'}"
            elif last.metrics_computed:
                metrics_desc = ", ".join(f"{k}={v}" for k, v in last.metrics_computed.items())
                resolved = f"the analysis showing {metrics_desc}"
            else:
                resolved = f"the previous response about {last.topic or 'your query'}"
            
            return resolved, {
                "resolved": True,
                "original_reference": reference,
                "resolved_to": resolved,
                "last_topic": last.topic,
                "last_result_type": last.result_type,
                "last_chart_type": last.chart_type,
                "last_content": last.content[:500]
            }
        
        return reference, {"resolved": False}
    
    def get_context_for_llm(self, limit: int = 10) -> List[Dict]:
        """Get conversation history formatted for LLM"""
        messages = []
        for turn in self.conversation[-limit:]:
            messages.append({
                "role": turn.role,
                "content": turn.content[:800] if len(turn.content) > 800 else turn.content
            })
        return messages
    
    def get_known_metrics(self) -> Dict[str, float]:
        """Get all computed metrics for validation"""
        return self.known_metrics
    
    def get_data_schema(self, filename: str = None) -> Optional[Dict]:
        """Get schema for a file or all files"""
        if filename:
            return self.uploaded_files.get(filename)
        return self.learned_schemas


# Global memory store
_memory_store: Dict[str, ThreeLayerMemory] = {}


def get_memory(session_id: str) -> ThreeLayerMemory:
    """Get or create memory for session"""
    if session_id not in _memory_store:
        _memory_store[session_id] = ThreeLayerMemory(session_id)
    return _memory_store[session_id]


# =============================================================================
# 3️⃣ DATA-FIRST OPERATING MODEL
# =============================================================================

@dataclass
class DataAvailability:
    """Result of data availability check"""
    is_available: bool
    available_columns: List[str]
    missing_requirements: List[str]
    suggested_action: str
    data_source: Optional[str] = None


def check_data_availability(
    query: str,
    memory: ThreeLayerMemory
) -> DataAvailability:
    """
    Check if required data is available before answering.
    
    FIXED: Now checks actual file storage, not just memory!
    """
    session_id = memory.session_id
    has_data = False
    data_source = None
    
    # ==========================================================================
    # FIX: Check ACTUAL file storage, not just memory
    # ==========================================================================
    try:
        from utils.paths import get_user_paths
        
        paths = get_user_paths(session_id)
        data_path = paths.get("data")
        
        if data_path and data_path.exists():
            # Check for any data files
            data_files = list(data_path.glob("*.csv")) + \
                        list(data_path.glob("*.xlsx")) + \
                        list(data_path.glob("*.xls")) + \
                        list(data_path.glob("*.parquet"))
            
            if data_files:
                has_data = True
                data_source = data_files[0].name
                
                # Update memory with file info
                for f in data_files:
                    memory.uploaded_files[f.name] = {
                        "path": str(f),
                        "detected_columns": {}  # Will be populated on load
                    }
                
                print(f"[DATA-CHECK] Found {len(data_files)} data files: {data_source}")
                
    except Exception as e:
        print(f"[DATA-CHECK] Path check error: {e}")
    
    # Also check for vector DB / indexed data
    if not has_data:
        try:
            from utils.paths import get_user_paths
            
            paths = get_user_paths(session_id)
            vector_path = paths.get("vectors", paths.get("data"))
            
            if vector_path and vector_path.exists():
                # Check for index files
                index_files = list(vector_path.glob("*.faiss")) + \
                             list(vector_path.glob("*.pkl")) + \
                             list(vector_path.glob("*.index"))
                
                if index_files:
                    has_data = True
                    data_source = "indexed_data"
                    print(f"[DATA-CHECK] Found indexed data")
                    
        except Exception as e:
            print(f"[DATA-CHECK] Index check error: {e}")
    
    # If still no data, check memory as fallback
    if not has_data:
        schemas = memory.get_data_schema()
        if schemas or memory.uploaded_files:
            has_data = True
            data_source = list(memory.uploaded_files.keys())[0] if memory.uploaded_files else "memory"
    
    # ==========================================================================
    # NO DATA FOUND
    # ==========================================================================
    if not has_data:
        return DataAvailability(
            is_available=False,
            available_columns=[],
            missing_requirements=["No data uploaded"],
            suggested_action="Please upload a data file first (CSV, Excel, etc.)"
        )
    
    # ==========================================================================
    # DATA FOUND - Don't refuse, let the query proceed
    # ==========================================================================
    # For now, assume data is available if files exist
    # The RAG system will handle column detection
    
    return DataAvailability(
        is_available=True,
        available_columns=["auto_detected"],  # Will be detected during query
        missing_requirements=[],
        suggested_action="Data available, proceeding with analysis",
        data_source=data_source
    )


# =============================================================================
# 4️⃣ QUERY UNDERSTANDING PIPELINE (7 STEPS)
# =============================================================================

class QueryIntent(Enum):
    """What is the user asking for?"""
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    TREND = "trend"
    AGGREGATION = "aggregation"
    RANKING = "ranking"
    VISUALIZATION = "visualization"
    VALIDATION = "validation"
    CLARIFICATION = "clarification"
    GENERAL = "general"


@dataclass
class PipelineResult:
    """Result of the 7-step pipeline"""
    # Step 1: Intent
    intent: QueryIntent
    intent_confidence: float
    
    # Step 2: Context
    context_resolved: bool
    resolved_references: Dict
    
    # Step 3: Data Check
    data_available: DataAvailability
    
    # Step 4: Reasoning Plan
    computation_required: List[str]
    tools_needed: List[str]
    
    # Step 5: Execution
    execution_status: str = "pending"
    
    # Step 6: Validation
    validated: bool = False
    validation_issues: List[str] = field(default_factory=list)
    
    # Step 7: Response
    should_respond: bool = True
    refuse_reason: Optional[str] = None


def execute_query_pipeline(
    query: str,
    session_id: str,
    memory: ThreeLayerMemory
) -> PipelineResult:
    """
    Execute the 7-step query understanding pipeline.
    
    NEVER skip steps - skipping is a system error.
    """
    
    # STEP 1: Intent Resolution
    intent, confidence = _resolve_intent(query)
    print(f"[PIPELINE] Step 1 - Intent: {intent.value} (conf: {confidence:.2f})")
    
    # STEP 2: Context Resolution
    resolved_query, resolution_meta = memory.resolve_reference(query)
    context_resolved = resolution_meta.get("resolved", False)
    print(f"[PIPELINE] Step 2 - Context: resolved={context_resolved}")
    
    # STEP 3: Data Feasibility Check
    data_check = check_data_availability(resolved_query, memory)
    print(f"[PIPELINE] Step 3 - Data: available={data_check.is_available}")
    
    if not data_check.is_available:
        return PipelineResult(
            intent=intent,
            intent_confidence=confidence,
            context_resolved=context_resolved,
            resolved_references=resolution_meta,
            data_available=data_check,
            computation_required=[],
            tools_needed=[],
            should_respond=True,
            refuse_reason=data_check.suggested_action
        )
    
    # STEP 4: Reasoning Plan
    computations, tools = _plan_reasoning(query, intent)
    print(f"[PIPELINE] Step 4 - Plan: {computations}")
    
    # STEP 5-6-7 happen during actual execution
    
    return PipelineResult(
        intent=intent,
        intent_confidence=confidence,
        context_resolved=context_resolved,
        resolved_references=resolution_meta,
        data_available=data_check,
        computation_required=computations,
        tools_needed=tools,
        should_respond=True
    )


def _resolve_intent(query: str) -> Tuple[QueryIntent, float]:
    """Determine user intent from query"""
    q_lower = query.lower()
    
    # Explanation patterns
    if any(w in q_lower for w in ["explain", "why", "what does", "how come", "tell me about"]):
        return QueryIntent.EXPLANATION, 0.9
    
    # Comparison patterns
    if any(w in q_lower for w in ["compare", "versus", "vs", "difference", "better"]):
        return QueryIntent.COMPARISON, 0.9
    
    # Trend patterns
    if any(w in q_lower for w in ["trend", "over time", "growth", "change", "month"]):
        return QueryIntent.TREND, 0.85
    
    # Aggregation patterns
    if any(w in q_lower for w in ["total", "sum", "average", "count", "how much", "how many"]):
        return QueryIntent.AGGREGATION, 0.9
    
    # Ranking patterns
    if any(w in q_lower for w in ["top", "bottom", "best", "worst", "highest", "lowest", "rank"]):
        return QueryIntent.RANKING, 0.9
    
    # Visualization patterns
    if any(w in q_lower for w in ["show", "chart", "graph", "visualize", "plot", "display"]):
        return QueryIntent.VISUALIZATION, 0.85
    
    return QueryIntent.GENERAL, 0.7


def _plan_reasoning(query: str, intent: QueryIntent) -> Tuple[List[str], List[str]]:
    """Plan what computations and tools are needed"""
    computations = []
    tools = []
    
    if intent == QueryIntent.AGGREGATION:
        computations.append("sum_or_average")
    elif intent == QueryIntent.RANKING:
        computations.append("sort_and_rank")
    elif intent == QueryIntent.TREND:
        computations.append("time_series_analysis")
    elif intent == QueryIntent.COMPARISON:
        computations.append("comparative_analysis")
    
    if "chart" in query.lower() or intent == QueryIntent.VISUALIZATION:
        tools.append("visualization_engine")
    
    return computations, tools


# =============================================================================
# 9️⃣ SELF-AUDIT SYSTEM
# =============================================================================

@dataclass
class AuditResult:
    """Result of self-audit before responding"""
    passed: bool
    claims_verified: int
    claims_unverified: int
    issues: List[str]
    recommendation: str


def self_audit(
    response: str,
    memory: ThreeLayerMemory,
    pipeline_result: PipelineResult
) -> AuditResult:
    """
    Self-audit before every response.
    
    Verify:
    1. Is every claim supported?
    2. Can every number be traced?
    3. Does this answer the exact question?
    """
    issues = []
    claims_verified = 0
    claims_unverified = 0
    
    # Check 1: Data grounding
    if not pipeline_result.data_available.is_available:
        if "no data" not in response.lower() and "upload" not in response.lower():
            issues.append("Response doesn't acknowledge missing data")
    
    # Check 2: Number verification
    import re
    numbers = re.findall(r'[\$₹€£]?[\d,]+\.?\d*', response)
    known_metrics = memory.get_known_metrics()
    
    for num_str in numbers:
        # Clean and convert
        num_clean = num_str.replace(',', '').replace('$', '').replace('₹', '').replace('€', '').replace('£', '')
        try:
            num = float(num_clean)
            # Check if this number exists in known metrics or data
            if any(abs(v - num) < 0.01 for v in known_metrics.values()):
                claims_verified += 1
            else:
                claims_unverified += 1
        except ValueError:
            pass
    
    # Check 3: Intent alignment
    if pipeline_result.intent == QueryIntent.EXPLANATION:
        if len(response) < 50:
            issues.append("Explanation response too short")
    
    passed = len(issues) == 0 and claims_unverified == 0
    
    recommendation = "Response approved" if passed else "Consider revising or refusing"
    
    return AuditResult(
        passed=passed,
        claims_verified=claims_verified,
        claims_unverified=claims_unverified,
        issues=issues,
        recommendation=recommendation
    )


# =============================================================================
# 🔟 FAILURE CONDITIONS (SYSTEM MUST REFUSE)
# =============================================================================

def should_refuse(pipeline_result: PipelineResult) -> Tuple[bool, str]:
    """
    Determine if system should refuse to answer.
    
    Refusal with explanation is CORRECT behavior.
    """
    # Refuse if data is insufficient
    if not pipeline_result.data_available.is_available:
        return True, pipeline_result.data_available.suggested_action
    
    # Refuse if intent is ambiguous
    if pipeline_result.intent_confidence < 0.5:
        return True, (
            "I'm not entirely sure what you're asking. Could you clarify:\n"
            "- Are you looking for a specific number?\n"
            "- Do you want to see a chart?\n"
            "- Are you asking about a specific time period?"
        )
    
    # Refuse if required context is missing
    if pipeline_result.intent == QueryIntent.EXPLANATION:
        if not pipeline_result.context_resolved:
            if any(w in pipeline_result.resolved_references.get("original_reference", "").lower() 
                   for w in ["above", "that", "this"]):
                return True, (
                    "I'm not sure what 'that' or 'above' refers to. "
                    "Could you specify what you'd like me to explain?"
                )
    
    return False, ""


# =============================================================================
# MASTER SYSTEM PROMPT (FINAL)
# =============================================================================

def get_production_system_prompt(
    memory: ThreeLayerMemory,
    pipeline_result: PipelineResult,
    currency_symbol: str = "$"
) -> str:
    """Generate the production-grade system prompt"""
    
    # Build context section
    context_section = ""
    if pipeline_result.context_resolved:
        ref = pipeline_result.resolved_references
        context_section = f"""
CONVERSATION CONTEXT:
- Referring to: {ref.get('resolved_to', 'previous response')}
- Topic: {ref.get('last_topic', 'unknown')}
- Result type: {ref.get('last_result_type', 'text')}
- Previous content: {ref.get('last_content', '')[:200]}...
"""
    
    # Build data section
    data_section = ""
    if pipeline_result.data_available.is_available:
        data_section = f"""
DATA AVAILABLE:
- Source: {pipeline_result.data_available.data_source}
- Columns: {', '.join(pipeline_result.data_available.available_columns)}
"""
    
    # Build known metrics
    metrics = memory.get_known_metrics()
    metrics_section = ""
    if metrics:
        metrics_section = "COMPUTED METRICS:\n"
        for k, v in metrics.items():
            metrics_section += f"- {k}: {currency_symbol}{v:,.2f}\n"
    
    return f"""═══════════════════════════════════════════════════════════════════════════
                    PRODUCTION-GRADE BUSINESS AI ENGINE
                    (ChatGPT/Claude Architecture)
═══════════════════════════════════════════════════════════════════════════

🚨 FOUNDATIONAL TRUTH RULE
Every claim must be grounded in data. Never fabricate.
If data is missing, say: "I cannot answer this accurately."

{context_section}

{data_section}

{metrics_section}

📊 CURRENT QUERY ANALYSIS:
- Intent: {pipeline_result.intent.value}
- Confidence: {pipeline_result.intent_confidence:.0%}
- Computations needed: {', '.join(pipeline_result.computation_required) or 'none'}

✅ RESPONSE RULES:
1. Use ONLY data from context provided
2. Use {currency_symbol} for currency formatting
3. Be direct and confident (no "As an AI...")
4. If showing numbers, they MUST exist in data
5. If user says "above/that/this" - refer to CONVERSATION CONTEXT above

🛑 BEFORE RESPONDING:
- Verify every claim is supported
- Verify every number is traceable
- If uncertain, ASK instead of guessing

═══════════════════════════════════════════════════════════════════════════
"""
