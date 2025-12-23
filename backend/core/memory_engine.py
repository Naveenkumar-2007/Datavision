# Persistent Memory Engine (Company Brain)
"""
Enterprise 4-Layer Memory System

Layers:
1. Short-Term (Session) - Last 20 messages, in-memory
2. Mid-Term (Insights) - Predictions, scenarios, 90-day expiry
3. Long-Term (Company Brain) - Entities, relationships, permanent
4. Document (RAG Store) - Uploaded files, persistent vector index

Usage:
    from core.memory_engine import MemoryEngine
    memory = MemoryEngine(workspace_id)
    
    # Store insight
    memory.store_insight(type="prediction", data={...})
    
    # Retrieve for context
    context = memory.get_memory_context(query)
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import numpy as np


class MemoryLayer(Enum):
    """Memory layer types"""
    SHORT_TERM = "short_term"      # Session memory
    MID_TERM = "mid_term"          # Insights memory (90 days)
    LONG_TERM = "long_term"        # Company brain (permanent)
    DOCUMENT = "document"          # RAG document store


class MemoryType(Enum):
    """Types of memory entries"""
    # Short-term
    MESSAGE = "message"
    
    # Mid-term
    INSIGHT = "insight"
    PREDICTION = "prediction"
    SCENARIO = "scenario"
    ANOMALY = "anomaly"
    CHART = "chart"
    REPORT = "report"
    
    # Long-term
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    KPI = "kpi"
    PATTERN = "pattern"
    EVENT = "event"


@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: str
    layer: MemoryLayer
    memory_type: MemoryType
    content: Dict[str, Any]
    workspace_id: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class ShortTermMemory:
    """
    Layer 1: Short-Term Memory (Session)
    - Last 20 messages per session
    - In-memory with TTL
    - Conversation continuity
    - AUTHORITATIVE METRIC TRACKING (new)
    - CONCLUSION & REASONING STORAGE (new)
    """
    
    MAX_MESSAGES = 20
    TTL_HOURS = 24
    
    def __init__(self):
        # session_id -> list of messages
        self._sessions: Dict[str, List[Dict]] = {}
        self._session_times: Dict[str, datetime] = {}
        
        # =====================================================================
        # AUTHORITATIVE METRIC TRACKING - Per session source of truth
        # =====================================================================
        self._primary_metrics: Dict[str, Dict] = {}
        # Structure: {session_id: {"metric": "total_revenue", "value": 548765.39, "currency": "INR"}}
        
        # =====================================================================
        # CONCLUSION & REASONING STORAGE - For self-explanation
        # =====================================================================
        self._conclusions: Dict[str, Dict] = {}
        # Structure: {session_id: {"conclusion": "good", "reasons": [...], "metric": "revenue"}}
        
        # =====================================================================
        # CURRENCY PREFERENCE - Remember user's preferred output currency
        # =====================================================================
        self._currency_preferences: Dict[str, str] = {}
        # Structure: {session_id: "USD"}
        
        # =====================================================================
        # AUTHORITATIVE AGGREGATES - Computed data that CANNOT be contradicted
        # =====================================================================
        self._aggregates: Dict[str, Dict] = {}
        # Structure: {session_id: {
        #   "monthly_revenue": {"Jan": 82883, "Feb": 72705, ...},
        #   "best_month": "June",
        #   "best_month_value": 101779,
        #   "worst_month": "April",
        #   "trend_direction": "recovering",
        #   "top_customers": [...]
        # }}
        
        # =====================================================================
        # LAST CHART CONTEXT - For chart-explanation binding
        # =====================================================================
        self._last_chart: Dict[str, Dict] = {}
        # Structure: {session_id: {
        #   "type": "monthly_revenue",
        #   "title": "Monthly Revenue Trend",
        #   "data_summary": "Revenue from Jan to Jul, peak in June",
        #   "peak": {"label": "June", "value": 101779},
        #   "low": {"label": "April", "value": 57973}
        # }}
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to session memory"""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            self._session_times[session_id] = datetime.now()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self._sessions[session_id].append(message)
        
        # Keep only last N messages
        if len(self._sessions[session_id]) > self.MAX_MESSAGES:
            self._sessions[session_id] = self._sessions[session_id][-self.MAX_MESSAGES:]
        
        self._session_times[session_id] = datetime.now()
    
    def get_messages(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent messages from session"""
        self._cleanup_expired()
        return self._sessions.get(session_id, [])[-limit:]
    
    def get_context(self, session_id: str) -> str:
        """Get formatted context string"""
        messages = self.get_messages(session_id)
        if not messages:
            return ""
        
        context = "Recent conversation:\n"
        for msg in messages[-5:]:
            role = msg.get("role", "").upper()
            content = msg.get("content", "")[:200]
            context += f"{role}: {content}\n"
        
        return context
    
    def _cleanup_expired(self):
        """Remove expired sessions"""
        cutoff = datetime.now() - timedelta(hours=self.TTL_HOURS)
        expired = [
            sid for sid, time in self._session_times.items()
            if time < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]
            del self._session_times[sid]
    
    def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            del self._session_times[session_id]
    
    def get_last_entity(self, session_id: str) -> Optional[str]:
        """Get the last mentioned entity (customer, product, metric)"""
        messages = self.get_messages(session_id, limit=5)
        
        # Entity patterns to look for
        import re
        entity_patterns = [
            r'(?:customer|client)\s+([A-Za-z0-9_\-]+)',
            r'([A-Za-z0-9_\-]+)(?:\'s|s\')?\s+(?:revenue|sales|orders)',
            r'top\s+(?:customer|product):\s*([A-Za-z0-9_\-]+)',
        ]
        
        for msg in reversed(messages):
            content = msg.get('content', '')
            for pattern in entity_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return None
    
    def get_last_metric(self, session_id: str) -> Optional[str]:
        """Get the last mentioned metric (revenue, orders, etc.)"""
        messages = self.get_messages(session_id, limit=5)
        
        metrics = ['revenue', 'sales', 'orders', 'customers', 'products', 
                   'growth', 'profit', 'margin', 'aov', 'arpu', 'churn']
        
        for msg in reversed(messages):
            content = msg.get('content', '').lower()
            for metric in metrics:
                if metric in content:
                    return metric
        
        return None
    
    def get_last_time_reference(self, session_id: str) -> Optional[str]:
        """Get the last mentioned time period"""
        messages = self.get_messages(session_id, limit=5)
        
        import re
        time_patterns = [
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s*\d*',
            r'(q[1-4])\s*\d*',
            r'(last|this|next)\s+(week|month|quarter|year)',
            r'\d{4}-\d{2}',
            r'(fy\s*\d+)',
        ]
        
        for msg in reversed(messages):
            content = msg.get('content', '').lower()
            for pattern in time_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        return None
    
    # =========================================================================
    # AUTHORITATIVE METRIC TRACKING - Source of truth for follow-ups
    # =========================================================================
    
    def set_primary_metric(self, session_id: str, metric: str, value: Any, 
                           currency: str = "INR", formatted: str = None):
        """
        Set the authoritative primary metric for this session.
        All follow-up references to 'it', 'that', 'this' will resolve to this.
        """
        self._primary_metrics[session_id] = {
            "metric": metric,
            "value": value,
            "currency": currency,
            "formatted": formatted or str(value),
            "timestamp": datetime.now().isoformat()
        }
        print(f"[MEMORY] Primary metric set: {metric} = {formatted or value}")
    
    def get_primary_metric(self, session_id: str) -> Optional[Dict]:
        """
        Get the authoritative primary metric for this session.
        Returns: {"metric": "total_revenue", "value": 548765.39, "currency": "INR", "formatted": "₹548,765.39"}
        """
        return self._primary_metrics.get(session_id)
    
    # =========================================================================
    # CONCLUSION & REASONING STORAGE - For self-explanation
    # =========================================================================
    
    def set_conclusion(self, session_id: str, conclusion: str, reasons: List[str], 
                       metric: str = None):
        """
        Store an evaluative conclusion with reasons for self-explanation.
        Called after "Is this good or bad?" type answers.
        """
        self._conclusions[session_id] = {
            "conclusion": conclusion,  # e.g., "good", "healthy", "concerning"
            "reasons": reasons,        # e.g., ["Revenue is above average", "Growth is steady"]
            "metric": metric,
            "timestamp": datetime.now().isoformat()
        }
        print(f"[MEMORY] Conclusion stored: {conclusion} with {len(reasons)} reasons")
    
    def get_conclusion(self, session_id: str) -> Optional[Dict]:
        """
        Get the last stored conclusion for self-explanation.
        Returns: {"conclusion": "good", "reasons": [...], "metric": "revenue"}
        """
        return self._conclusions.get(session_id)
    
    # =========================================================================
    # LAST ANSWER RETRIEVAL - For follow-up context
    # =========================================================================
    
    def get_last_answer(self, session_id: str) -> Optional[str]:
        """Get the most recent assistant response for follow-up reference."""
        messages = self.get_messages(session_id, limit=10)
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return None
    
    # =========================================================================
    # CURRENCY PREFERENCE - Remember user's preferred output currency
    # =========================================================================
    
    def set_currency_preference(self, session_id: str, currency: str):
        """Store user's preferred output currency (USD, EUR, GBP, INR)."""
        self._currency_preferences[session_id] = currency.upper()
        print(f"[MEMORY] Currency preference set: {currency.upper()}")
    
    def get_currency_preference(self, session_id: str) -> Optional[str]:
        """Get user's preferred output currency."""
        return self._currency_preferences.get(session_id)
    
    # =========================================================================
    # AUTHORITATIVE AGGREGATES - Unified truth across all modes
    # =========================================================================
    
    def set_aggregate(self, session_id: str, key: str, value: Any):
        """
        Store an authoritative aggregate that CANNOT be contradicted.
        
        Examples:
            set_aggregate(session_id, "monthly_revenue", {"Jan": 82883, ...})
            set_aggregate(session_id, "best_month", "June")
            set_aggregate(session_id, "best_month_value", 101779)
        """
        if session_id not in self._aggregates:
            self._aggregates[session_id] = {}
        self._aggregates[session_id][key] = value
        print(f"[MEMORY] Aggregate stored: {key}")
    
    def get_aggregate(self, session_id: str, key: str) -> Any:
        """Get a stored aggregate value."""
        return self._aggregates.get(session_id, {}).get(key)
    
    def get_all_aggregates(self, session_id: str) -> Dict:
        """Get all stored aggregates for a session."""
        return self._aggregates.get(session_id, {})
    
    def get_aggregates_context(self, session_id: str) -> str:
        """
        Get formatted aggregates for LLM context.
        This is the AUTHORITATIVE DATA that cannot be contradicted.
        """
        aggregates = self.get_all_aggregates(session_id)
        if not aggregates:
            return ""
        
        context = "\nAUTHORITATIVE DATA (already computed - DO NOT contradict):\n"
        
        if "monthly_revenue" in aggregates:
            context += f"Monthly Revenue: {aggregates['monthly_revenue']}\n"
        if "best_month" in aggregates:
            context += f"Best Month: {aggregates['best_month']} = {aggregates.get('best_month_value', 'N/A')}\n"
        if "worst_month" in aggregates:
            context += f"Worst Month: {aggregates['worst_month']} = {aggregates.get('worst_month_value', 'N/A')}\n"
        if "trend_direction" in aggregates:
            context += f"Trend: {aggregates['trend_direction']}\n"
        if "top_customers" in aggregates:
            context += f"Top Customers: {aggregates['top_customers'][:3]}\n"
        
        return context
    
    # =========================================================================
    # CHART CONTEXT - For chart-explanation binding
    # =========================================================================
    
    def set_last_chart(self, session_id: str, chart_info: Dict):
        """
        Store the last rendered chart for explanation binding.
        
        chart_info should contain:
            type: "monthly_revenue", "customer_breakdown", etc.
            title: Chart title
            data_summary: Brief description
            peak: {label, value}
            low: {label, value}
        """
        self._last_chart[session_id] = chart_info
        print(f"[MEMORY] Chart context stored: {chart_info.get('type', 'unknown')}")
    
    def get_last_chart(self, session_id: str) -> Optional[Dict]:
        """Get the last chart context for explanation."""
        return self._last_chart.get(session_id)
    
    def get_chart_explanation_context(self, session_id: str) -> str:
        """
        Get formatted chart context for "explain this chart" queries.
        """
        chart = self.get_last_chart(session_id)
        if not chart:
            return ""
        
        context = f"""
LAST CHART SHOWN (explain THIS chart, not other data):
- Type: {chart.get('type', 'unknown')}
- Title: {chart.get('title', 'Chart')}
- Summary: {chart.get('data_summary', 'N/A')}
"""
        if chart.get('peak'):
            context += f"- Peak: {chart['peak'].get('label')} = {chart['peak'].get('value')}\n"
        if chart.get('low'):
            context += f"- Low: {chart['low'].get('label')} = {chart['low'].get('value')}\n"
        
        context += "\nEXPLAIN THE CHART ABOVE ONLY. Do not reference unrelated metrics.\n"
        return context
    
    # =========================================================================
    # $5M ENHANCEMENT: QUERY RESULT MEMORY - For ChatGPT-style follow-ups
    # =========================================================================
    # When user asks "top 5 customers", we store the results so they can
    # follow up with "compare top vs bottom" or "tell me about Customer_1"
    
    _query_results: Dict[str, Dict] = {}
    
    def set_last_query_result(self, session_id: str, query_type: str, 
                               data: List[Dict], summary: str = ""):
        """
        Store the result of a data query for follow-up reference.
        
        This is CRITICAL for queries like "compare top vs lowest" where
        we need to remember what was just shown.
        
        Args:
            session_id: Session identifier
            query_type: Type of result ('customers', 'products', 'months', etc.)
            data: List of data items, each with 'name' and 'value' keys
            summary: Optional summary description
            
        Example:
            set_last_query_result(session_id, 'products', [
                {'name': 'Product A', 'value': 95827.71, 'rank': 1},
                {'name': 'Product B', 'value': 87968.61, 'rank': 2},
                ...
            ])
        """
        if session_id not in self._query_results:
            self._query_results[session_id] = {}
        
        self._query_results[session_id] = {
            'type': query_type,
            'data': data,
            'summary': summary,
            'timestamp': datetime.now().isoformat(),
            # Precompute common references
            'top_item': data[0] if data else None,
            'bottom_item': data[-1] if data else None,
            'count': len(data)
        }
        print(f"[MEMORY] Query result stored: {query_type} with {len(data)} items")
    
    def get_last_query_result(self, session_id: str) -> Optional[Dict]:
        """
        Get the last query result for follow-up queries.
        
        Returns dict with:
            type: 'customers', 'products', etc.
            data: List of items
            top_item: First/best item
            bottom_item: Last/worst item
            count: Number of items
        """
        return self._query_results.get(session_id)
    
    def get_item_by_reference(self, session_id: str, reference: str) -> Optional[Dict]:
        """
        Get an item by contextual reference like 'top', 'best', 'lowest', 'worst'.
        
        Args:
            session_id: Session identifier
            reference: 'top', 'best', 'first', 'highest' -> returns top_item
                      'bottom', 'worst', 'last', 'lowest' -> returns bottom_item
                      
        Returns:
            Item dict with 'name', 'value', 'rank' or None
        """
        result = self.get_last_query_result(session_id)
        if not result:
            return None
        
        reference_lower = reference.lower()
        
        # Top references
        if any(ref in reference_lower for ref in ['top', 'best', 'first', 'highest', 'leading']):
            return result.get('top_item')
        
        # Bottom references
        if any(ref in reference_lower for ref in ['bottom', 'worst', 'last', 'lowest', 'trailing']):
            return result.get('bottom_item')
        
        # Try to find by name
        data = result.get('data', [])
        for item in data:
            if item.get('name', '').lower() in reference_lower:
                return item
        
        return None
    
    def get_comparison_context(self, session_id: str) -> str:
        """
        Get formatted context for comparison follow-ups.
        
        Called when user asks "compare top vs bottom" style questions.
        """
        result = self.get_last_query_result(session_id)
        if not result:
            return ""
        
        top = result.get('top_item')
        bottom = result.get('bottom_item')
        
        if not top or not bottom:
            return ""
        
        context = f"""
PREVIOUS QUERY RESULTS ({result.get('type', 'items')}):
- TOP: {top.get('name')} = {top.get('value'):,.2f}
- BOTTOM: {bottom.get('name')} = {bottom.get('value'):,.2f}
- Total items shown: {result.get('count')}

When user refers to 'top', 'best', 'highest' → use {top.get('name')}
When user refers to 'bottom', 'worst', 'lowest' → use {bottom.get('name')}
"""
        return context


# =============================================================================
# GLOBAL SINGLETON INSTANCE - Use this for shared state across modules
# =============================================================================
# This MUST be used by both chat.py and nodes.py to share chart context,
# aggregates, and conversation state.
_shared_memory_instance = None

def get_shared_memory() -> ShortTermMemory:
    """
    Get the shared memory singleton instance.
    
    Usage:
        from core.memory_engine import get_shared_memory
        memory = get_shared_memory()
        memory.set_last_chart(...)
    """
    global _shared_memory_instance
    if _shared_memory_instance is None:
        _shared_memory_instance = ShortTermMemory()
        print("[MEMORY] Created shared memory singleton instance")
    return _shared_memory_instance

# Also export a direct reference for backward compatibility
shared_memory = get_shared_memory()


class ReferenceResolver:
    """
    Resolves pronouns and contextual references in follow-up queries.
    Enables natural conversation like "compare that to last month".
    """
    
    # Reference patterns to detect
    ENTITY_REFS = ['that', 'this', 'it', 'them', 'those', 'these']
    TIME_REFS = ['last month', 'previous', 'before', 'prior', 'earlier']
    CONTEXT_REFS = ['same', 'above', 'mentioned', 'earlier']
    
    def __init__(self, short_term: ShortTermMemory):
        self.short_term = short_term
    
    def resolve(self, query: str, session_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Resolve references in the query.
        
        Returns:
            (resolved_query, metadata)
            
        Example:
            Input: "Compare that to last month"
            Output: ("Compare Customer_1 revenue to November 2024", 
                     {"resolved": {"that": "Customer_1 revenue"}})
        """
        import re
        query_lower = query.lower()
        resolved = {}
        resolved_query = query
        
        # Check for entity references
        for ref in self.ENTITY_REFS:
            pattern = rf'\b{ref}\b'
            if re.search(pattern, query_lower):
                entity = self.short_term.get_last_entity(session_id)
                metric = self.short_term.get_last_metric(session_id)
                
                if entity or metric:
                    replacement = []
                    if entity:
                        replacement.append(entity)
                    if metric:
                        replacement.append(metric)
                    replacement_str = ' '.join(replacement)
                    
                    # Replace the reference
                    resolved_query = re.sub(pattern, replacement_str, resolved_query, flags=re.IGNORECASE)
                    resolved[ref] = replacement_str
        
        # Check for time references  
        if 'last month' in query_lower or 'previous' in query_lower:
            time_ref = self.short_term.get_last_time_reference(session_id)
            if time_ref:
                resolved['time_context'] = time_ref
        
        metadata = {
            'resolved': resolved,
            'had_references': len(resolved) > 0,
            'original_query': query
        }
        
        return resolved_query, metadata
    
    def needs_resolution(self, query: str) -> bool:
        """Check if query contains references that need resolution"""
        query_lower = query.lower()
        
        all_refs = self.ENTITY_REFS + self.TIME_REFS + self.CONTEXT_REFS
        for ref in all_refs:
            if ref in query_lower:
                return True
        
        return False


class MidTermMemory:
    """
    Layer 2: Mid-Term Memory (Insights)
    - Predictions, scenarios, anomalies, charts
    - 90-day expiry
    - PostgreSQL + Vector embeddings
    """
    
    DEFAULT_EXPIRY_DAYS = 90
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url
        # In-memory fallback: workspace_id -> list of entries
        self._memory: Dict[str, List[MemoryEntry]] = {}
    
    def store(
        self,
        workspace_id: str,
        memory_type: MemoryType,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None,
        expiry_days: int = DEFAULT_EXPIRY_DAYS
    ) -> MemoryEntry:
        """Store an insight/prediction/scenario to mid-term memory"""
        entry_id = hashlib.sha256(
            f"{workspace_id}:{memory_type.value}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        entry = MemoryEntry(
            id=entry_id,
            layer=MemoryLayer.MID_TERM,
            memory_type=memory_type,
            content=content,
            workspace_id=workspace_id,
            metadata=metadata or {},
            expires_at=datetime.now() + timedelta(days=expiry_days)
        )
        
        if workspace_id not in self._memory:
            self._memory[workspace_id] = []
        
        self._memory[workspace_id].append(entry)
        
        return entry
    
    def get_insights(self, workspace_id: str, memory_type: Optional[MemoryType] = None, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve insights from mid-term memory"""
        self._cleanup_expired()
        
        entries = self._memory.get(workspace_id, [])
        
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        
        # Sort by recency
        entries.sort(key=lambda e: e.created_at, reverse=True)
        
        return entries[:limit]
    
    def get_context(self, workspace_id: str) -> str:
        """Get formatted context from insights"""
        insights = self.get_insights(workspace_id, limit=5)
        
        if not insights:
            return ""
        
        context = "Recent insights:\n"
        for entry in insights:
            type_str = entry.memory_type.value
            summary = entry.content.get("summary", entry.content.get("message", str(entry.content)))[:100]
            context += f"• [{type_str}] {summary}\n"
        
        return context
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        for workspace_id in list(self._memory.keys()):
            self._memory[workspace_id] = [
                e for e in self._memory[workspace_id]
                if e.expires_at is None or e.expires_at > now
            ]


class LongTermMemory:
    """
    Layer 3: Long-Term Memory (Company Brain)
    - Entities, relationships, KPIs
    - Permanent storage
    - Used by GraphRAG
    """
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url
        # In-memory: workspace_id -> {entity_type -> list of entities}
        self._entities: Dict[str, Dict[str, List[Dict]]] = {}
        self._relationships: Dict[str, List[Dict]] = {}
        self._kpis: Dict[str, List[Dict]] = {}
        self._patterns: Dict[str, List[Dict]] = {}
    
    def store_entity(
        self,
        workspace_id: str,
        entity_type: str,  # customer, product, category
        entity_id: str,
        properties: Dict[str, Any]
    ):
        """Store an entity to long-term memory"""
        if workspace_id not in self._entities:
            self._entities[workspace_id] = {}
        
        if entity_type not in self._entities[workspace_id]:
            self._entities[workspace_id][entity_type] = []
        
        # Check if exists
        existing = [
            e for e in self._entities[workspace_id][entity_type]
            if e.get("id") == entity_id
        ]
        
        if existing:
            # Update
            existing[0].update(properties)
            existing[0]["updated_at"] = datetime.now().isoformat()
        else:
            # Create
            self._entities[workspace_id][entity_type].append({
                "id": entity_id,
                "type": entity_type,
                **properties,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
    
    def store_relationship(
        self,
        workspace_id: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict] = None
    ):
        """Store a relationship between entities"""
        if workspace_id not in self._relationships:
            self._relationships[workspace_id] = []
        
        rel = {
            "source": source_id,
            "target": target_id,
            "type": relationship_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat()
        }
        
        self._relationships[workspace_id].append(rel)
    
    def store_kpi(
        self,
        workspace_id: str,
        kpi_name: str,
        value: float,
        period: str,
        metadata: Optional[Dict] = None
    ):
        """Store a KPI metric"""
        if workspace_id not in self._kpis:
            self._kpis[workspace_id] = []
        
        self._kpis[workspace_id].append({
            "name": kpi_name,
            "value": value,
            "period": period,
            "metadata": metadata or {},
            "recorded_at": datetime.now().isoformat()
        })
    
    def store_pattern(
        self,
        workspace_id: str,
        pattern_type: str,
        description: str,
        evidence: List[str],
        confidence: float
    ):
        """Store a discovered business pattern"""
        if workspace_id not in self._patterns:
            self._patterns[workspace_id] = []
        
        self._patterns[workspace_id].append({
            "type": pattern_type,
            "description": description,
            "evidence": evidence,
            "confidence": confidence,
            "discovered_at": datetime.now().isoformat()
        })
    
    def get_entities(self, workspace_id: str, entity_type: Optional[str] = None) -> List[Dict]:
        """Get entities from memory"""
        entities = self._entities.get(workspace_id, {})
        
        if entity_type:
            return entities.get(entity_type, [])
        
        # Return all
        all_entities = []
        for etype, elist in entities.items():
            all_entities.extend(elist)
        
        return all_entities
    
    def get_relationships(self, workspace_id: str, entity_id: Optional[str] = None) -> List[Dict]:
        """Get relationships from memory"""
        rels = self._relationships.get(workspace_id, [])
        
        if entity_id:
            return [r for r in rels if r["source"] == entity_id or r["target"] == entity_id]
        
        return rels
    
    def get_context(self, workspace_id: str) -> str:
        """Get formatted context from long-term memory"""
        context_parts = []
        
        # Entities summary
        entities = self.get_entities(workspace_id)
        if entities:
            context_parts.append(f"Known entities: {len(entities)} total")
            by_type = {}
            for e in entities:
                etype = e.get("type", "unknown")
                by_type[etype] = by_type.get(etype, 0) + 1
            for etype, count in by_type.items():
                context_parts.append(f"  • {count} {etype}s")
        
        # Recent patterns
        patterns = self._patterns.get(workspace_id, [])
        if patterns:
            context_parts.append(f"Discovered patterns: {len(patterns)}")
            for p in patterns[-3:]:
                context_parts.append(f"  • {p['description'][:50]}")
        
        return "\n".join(context_parts) if context_parts else ""


class DocumentMemory:
    """
    Layer 4: Document Memory (RAG Store)
    - Uploaded files (PDF, Excel, CSV, images)
    - Persistent vector index (ChromaDB)
    - Multi-dataset merging
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path("./storage/documents")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory document index: workspace_id -> list of docs
        self._docs: Dict[str, List[Dict]] = {}
    
    def store_document(
        self,
        workspace_id: str,
        filename: str,
        content: str,
        doc_type: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a document in memory"""
        doc_id = hashlib.sha256(
            f"{workspace_id}:{filename}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        if workspace_id not in self._docs:
            self._docs[workspace_id] = []
        
        doc = {
            "id": doc_id,
            "filename": filename,
            "content": content,
            "type": doc_type,
            "metadata": metadata or {},
            "workspace_id": workspace_id,
            "indexed_at": datetime.now().isoformat()
        }
        
        self._docs[workspace_id].append(doc)
        
        return doc_id
    
    def search(self, workspace_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search documents (simple keyword matching)"""
        docs = self._docs.get(workspace_id, [])
        
        # Simple search
        query_lower = query.lower()
        matches = []
        
        for doc in docs:
            content = doc.get("content", "").lower()
            if query_lower in content:
                matches.append(doc)
        
        return matches[:limit]
    
    def get_all(self, workspace_id: str) -> List[Dict]:
        """Get all documents for workspace"""
        return self._docs.get(workspace_id, [])
    
    def get_context(self, workspace_id: str) -> str:
        """Get summary context for documents"""
        docs = self.get_all(workspace_id)
        if not docs:
            return ""
        
        context = f"Available documents: {len(docs)}\n"
        for doc in docs[-5:]:
            context += f"  • {doc['filename']} ({doc['type']})\n"
        
        return context


class MemoryEngine:
    """
    Unified 4-Layer Memory Engine
    
    Integrates all memory layers and provides a unified interface
    for storing and retrieving memories across the system.
    """
    
    def __init__(self, db_url: Optional[str] = None, storage_path: Optional[str] = None):
        self.db_url = db_url
        
        # Initialize all layers
        self.short_term = ShortTermMemory()
        self.mid_term = MidTermMemory(db_url)
        self.long_term = LongTermMemory(db_url)
        self.document = DocumentMemory(storage_path)
        
        # Memory update callbacks
        self._update_callbacks: List[callable] = []
    
    def on_memory_update(self, callback: callable):
        """Register callback for memory updates"""
        self._update_callbacks.append(callback)
    
    def _notify_update(self, layer: MemoryLayer, entry: Any):
        """Notify callbacks of memory update"""
        for cb in self._update_callbacks:
            try:
                cb(layer, entry)
            except:
                pass
    
    # =========================================================================
    # UNIFIED STORE METHODS
    # =========================================================================
    
    def store_message(self, workspace_id: str, session_id: str, role: str, content: str):
        """Store a chat message (short-term)"""
        self.short_term.add_message(session_id, role, content, {"workspace_id": workspace_id})
    
    def store_insight(self, workspace_id: str, insight_type: str, data: Dict[str, Any]) -> MemoryEntry:
        """Store an insight (mid-term)"""
        memory_type = MemoryType.INSIGHT
        if insight_type == "prediction":
            memory_type = MemoryType.PREDICTION
        elif insight_type == "scenario":
            memory_type = MemoryType.SCENARIO
        elif insight_type == "anomaly":
            memory_type = MemoryType.ANOMALY
        elif insight_type == "chart":
            memory_type = MemoryType.CHART
        
        entry = self.mid_term.store(workspace_id, memory_type, data)
        self._notify_update(MemoryLayer.MID_TERM, entry)
        return entry
    
    def store_entity(self, workspace_id: str, entity_type: str, entity_id: str, properties: Dict):
        """Store an entity (long-term)"""
        self.long_term.store_entity(workspace_id, entity_type, entity_id, properties)
        self._notify_update(MemoryLayer.LONG_TERM, {"type": entity_type, "id": entity_id})
    
    def store_kpi(self, workspace_id: str, kpi_name: str, value: float, period: str):
        """Store a KPI (long-term)"""
        self.long_term.store_kpi(workspace_id, kpi_name, value, period)
    
    def store_document(self, workspace_id: str, filename: str, content: str, doc_type: str) -> str:
        """Store a document (document memory)"""
        doc_id = self.document.store_document(workspace_id, filename, content, doc_type)
        self._notify_update(MemoryLayer.DOCUMENT, {"id": doc_id, "filename": filename})
        return doc_id
    
    # =========================================================================
    # UNIFIED RETRIEVAL
    # =========================================================================
    
    def get_memory_context(
        self,
        workspace_id: str,
        session_id: Optional[str] = None,
        include_layers: Optional[List[MemoryLayer]] = None
    ) -> str:
        """
        Get merged context from all memory layers.
        
        This is the main method for context injection into LLM prompts.
        """
        if include_layers is None:
            include_layers = [MemoryLayer.SHORT_TERM, MemoryLayer.MID_TERM, MemoryLayer.LONG_TERM]
        
        context_parts = []
        
        # Short-term (session)
        if MemoryLayer.SHORT_TERM in include_layers and session_id:
            short_ctx = self.short_term.get_context(session_id)
            if short_ctx:
                context_parts.append(f"## Session Context\n{short_ctx}")
        
        # Mid-term (insights)
        if MemoryLayer.MID_TERM in include_layers:
            mid_ctx = self.mid_term.get_context(workspace_id)
            if mid_ctx:
                context_parts.append(f"## Recent Insights\n{mid_ctx}")
        
        # Long-term (company brain)
        if MemoryLayer.LONG_TERM in include_layers:
            long_ctx = self.long_term.get_context(workspace_id)
            if long_ctx:
                context_parts.append(f"## Company Knowledge\n{long_ctx}")
        
        # Document (RAG)
        if MemoryLayer.DOCUMENT in include_layers:
            doc_ctx = self.document.get_context(workspace_id)
            if doc_ctx:
                context_parts.append(f"## Documents\n{doc_ctx}")
        
        return "\n\n".join(context_parts)
    
    def get_insights(self, workspace_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Get recent insights"""
        return self.mid_term.get_insights(workspace_id, limit=limit)
    
    def get_entities(self, workspace_id: str, entity_type: Optional[str] = None) -> List[Dict]:
        """Get entities from company brain"""
        return self.long_term.get_entities(workspace_id, entity_type)
    
    def search_documents(self, workspace_id: str, query: str) -> List[Dict]:
        """Search documents"""
        return self.document.search(workspace_id, query)
    
    # =========================================================================
    # MEMORY MANAGEMENT
    # =========================================================================
    
    def clear_session(self, session_id: str):
        """Clear session memory"""
        self.short_term.clear_session(session_id)
    
    def get_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "short_term_sessions": len(self.short_term._sessions),
            "mid_term_entries": len(self.mid_term._memory.get(workspace_id, [])),
            "long_term_entities": len(self.long_term.get_entities(workspace_id)),
            "long_term_relationships": len(self.long_term.get_relationships(workspace_id)),
            "documents": len(self.document.get_all(workspace_id))
        }


# Singleton instance
_memory_engine: Optional[MemoryEngine] = None


def get_memory_engine(db_url: Optional[str] = None) -> MemoryEngine:
    """Get or create the memory engine singleton"""
    global _memory_engine
    if _memory_engine is None:
        _memory_engine = MemoryEngine(db_url)
    return _memory_engine


# Quick test
if __name__ == "__main__":
    engine = MemoryEngine()
    
    # Test short-term
    engine.store_message("ws1", "session1", "user", "What is our revenue?")
    engine.store_message("ws1", "session1", "assistant", "Your revenue is ₹5,00,000")
    
    # Test mid-term
    engine.store_insight("ws1", "prediction", {
        "summary": "Revenue will grow 15% next month",
        "confidence": 85
    })
    
    # Test long-term
    engine.store_entity("ws1", "customer", "cust_1", {"name": "Acme Corp", "revenue": 100000})
    engine.store_kpi("ws1", "total_revenue", 500000, "2025-01")
    
    # Test document
    engine.store_document("ws1", "sales.csv", "Customer,Amount\nAcme,100000", "csv")
    
    # Get full context
    context = engine.get_memory_context("ws1", "session1")
    print("Memory Context:")
    print(context)
    
    print(f"\nStats: {engine.get_stats('ws1')}")
