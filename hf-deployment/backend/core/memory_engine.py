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
    """
    
    MAX_MESSAGES = 20
    TTL_HOURS = 24
    
    def __init__(self):
        # session_id -> list of messages
        self._sessions: Dict[str, List[Dict]] = {}
        self._session_times: Dict[str, datetime] = {}
    
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
