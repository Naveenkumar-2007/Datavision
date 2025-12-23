# Insight Queue - Proactive Business Intelligence
"""
Manages proactive insights for workspaces.
Stores detected anomalies and insights with priority for dashboard surfacing.

Storage: Supabase (cloud-persistent for production)
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

# Supabase client
try:
    from database.supabase_client import get_supabase_admin_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class InsightPriority(Enum):
    """Priority levels for insights"""
    CRITICAL = 10  # Immediate attention required
    HIGH = 8       # Important for today
    MEDIUM = 5     # Worth reviewing
    LOW = 2        # Nice to know
    INFO = 1       # Informational only


class InsightCategory(Enum):
    """Categories of proactive insights"""
    ANOMALY = "anomaly"           # Statistical anomaly detected
    TREND = "trend"               # Trend change detected
    RISK = "risk"                 # Risk or warning
    OPPORTUNITY = "opportunity"   # Potential opportunity
    ALERT = "alert"               # Time-based alert
    MILESTONE = "milestone"       # Achievement or milestone


@dataclass
class QueuedInsight:
    """A single queued insight for a workspace"""
    id: str
    workspace_id: str
    title: str
    body: str
    category: str
    priority: int
    severity: str  # "high", "medium", "low"
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    chart_payload: Optional[Dict] = None
    
    # Status tracking
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    seen_at: Optional[str] = None
    dismissed: bool = False
    actioned: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)


class InsightQueue:
    """
    Manages proactive insights for workspaces.
    Primary storage: Supabase for production
    Fallback: In-memory for development
    """
    
    def __init__(self):
        # In-memory fallback: workspace_id -> list of insights
        self._queue: Dict[str, List[QueuedInsight]] = {}
    
    def _get_supabase(self):
        """Get Supabase client with error handling"""
        if not SUPABASE_AVAILABLE:
            return None
        return get_supabase_admin_client()
    
    def add(
        self,
        workspace_id: str,
        title: str,
        body: str,
        category: str = "anomaly",
        priority: int = 5,
        severity: str = "medium",
        metadata: Optional[Dict] = None,
        chart_payload: Optional[Dict] = None
    ) -> QueuedInsight:
        """Add a new insight to the queue"""
        # Generate unique ID
        insight_id = hashlib.sha256(
            f"{workspace_id}:{title}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        insight = QueuedInsight(
            id=insight_id,
            workspace_id=workspace_id,
            title=title,
            body=body,
            category=category,
            priority=priority,
            severity=severity,
            metadata=metadata or {},
            chart_payload=chart_payload,
        )
        
        # Try Supabase first
        supabase = self._get_supabase()
        if supabase:
            try:
                supabase.table("insight_queue").insert(insight.to_dict()).execute()
                print(f"✅ Insight queued to Supabase: {title}")
            except Exception as e:
                print(f"⚠️ Supabase insert failed, using memory: {e}")
                self._add_to_memory(workspace_id, insight)
        else:
            self._add_to_memory(workspace_id, insight)
        
        return insight
    
    def _add_to_memory(self, workspace_id: str, insight: QueuedInsight):
        """Add insight to in-memory queue"""
        if workspace_id not in self._queue:
            self._queue[workspace_id] = []
        self._queue[workspace_id].append(insight)
        
        # Keep only last 50 per workspace
        if len(self._queue[workspace_id]) > 50:
            self._queue[workspace_id] = sorted(
                self._queue[workspace_id],
                key=lambda x: x.priority,
                reverse=True
            )[:50]
    
    def get_unseen(self, workspace_id: str, limit: int = 5) -> List[QueuedInsight]:
        """Get unseen insights for a workspace, ordered by priority"""
        supabase = self._get_supabase()
        
        if supabase:
            try:
                result = supabase.table("insight_queue").select("*").eq(
                    "workspace_id", workspace_id
                ).is_("seen_at", "null").eq(
                    "dismissed", False
                ).order(
                    "priority", desc=True
                ).limit(limit).execute()
                
                if result.data:
                    return [
                        QueuedInsight(
                            id=row["id"],
                            workspace_id=row["workspace_id"],
                            title=row["title"],
                            body=row["body"],
                            category=row.get("category", "anomaly"),
                            priority=row.get("priority", 5),
                            severity=row.get("severity", "medium"),
                            metadata=row.get("metadata", {}),
                            chart_payload=row.get("chart_payload"),
                            created_at=row.get("created_at", ""),
                            seen_at=row.get("seen_at"),
                            dismissed=row.get("dismissed", False),
                        )
                        for row in result.data
                    ]
            except Exception as e:
                print(f"⚠️ Supabase query failed: {e}")
        
        # Fallback to memory
        insights = self._queue.get(workspace_id, [])
        unseen = [i for i in insights if i.seen_at is None and not i.dismissed]
        unseen.sort(key=lambda x: x.priority, reverse=True)
        return unseen[:limit]
    
    def mark_seen(self, insight_id: str) -> bool:
        """Mark an insight as seen"""
        supabase = self._get_supabase()
        
        if supabase:
            try:
                supabase.table("insight_queue").update({
                    "seen_at": datetime.now().isoformat()
                }).eq("id", insight_id).execute()
                return True
            except Exception as e:
                print(f"⚠️ Supabase update failed: {e}")
        
        # Fallback to memory
        for workspace_id, insights in self._queue.items():
            for insight in insights:
                if insight.id == insight_id:
                    insight.seen_at = datetime.now().isoformat()
                    return True
        
        return False
    
    def dismiss(self, insight_id: str) -> bool:
        """Dismiss an insight"""
        supabase = self._get_supabase()
        
        if supabase:
            try:
                supabase.table("insight_queue").update({
                    "dismissed": True
                }).eq("id", insight_id).execute()
                return True
            except Exception as e:
                print(f"⚠️ Supabase update failed: {e}")
        
        # Fallback to memory
        for workspace_id, insights in self._queue.items():
            for insight in insights:
                if insight.id == insight_id:
                    insight.dismissed = True
                    return True
        
        return False
    
    def get_summary(self, workspace_id: str) -> Dict[str, Any]:
        """Get summary of pending insights for a workspace"""
        unseen = self.get_unseen(workspace_id, limit=100)
        
        # Count by category
        by_category = {}
        by_severity = {"high": 0, "medium": 0, "low": 0}
        
        for insight in unseen:
            cat = insight.category
            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[insight.severity] = by_severity.get(insight.severity, 0) + 1
        
        return {
            "total_unseen": len(unseen),
            "by_category": by_category,
            "by_severity": by_severity,
            "high_priority_count": sum(1 for i in unseen if i.priority >= 8),
            "summary_text": self._build_summary_text(len(unseen), by_severity),
        }
    
    def _build_summary_text(self, total: int, by_severity: Dict[str, int]) -> str:
        """Build human-readable summary"""
        if total == 0:
            return "No new insights"
        
        high = by_severity.get("high", 0)
        if high > 0:
            return f"⚠️ {high} high-priority insight{'s' if high != 1 else ''} require attention"
        
        return f"📊 {total} new insight{'s' if total != 1 else ''} since your last visit"
    
    def clear_old(self, workspace_id: str, days: int = 30) -> int:
        """Clear insights older than N days"""
        # Implementation for cleanup
        return 0


# Singleton instance
_insight_queue: Optional[InsightQueue] = None


def get_insight_queue() -> InsightQueue:
    """Get or create the insight queue singleton"""
    global _insight_queue
    if _insight_queue is None:
        _insight_queue = InsightQueue()
    return _insight_queue
