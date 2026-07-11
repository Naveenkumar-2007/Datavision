"""
Base Agent Runner - Abstract class for all AI agents
Provides common functionality for insight detection and notification dispatch.

Migrated from Supabase to PostgreSQL/SQLAlchemy.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.db import AsyncSessionLocal
from database.orm import UserProfile, WorkspaceMember
from database.workspace_ops import get_workspace_members
from services.notification_service import (
    enqueue_notification,
    NotificationJob,
    should_notify,
    in_dnd_window,
    check_rate_limit
)

logger = logging.getLogger(__name__)


class Insight:
    """Data class for AI-generated insights"""
    def __init__(
        self,
        title: str,
        body: str,
        severity: str,  # 'low' | 'medium' | 'high'
        score: float = None,
        metadata: Dict[str, Any] = None,
        chart_payload: Dict[str, Any] = None
    ):
        self.title = title
        self.body = body
        self.severity = severity
        self.score = score
        self.metadata = metadata or {}
        self.chart_payload = chart_payload


class AgentRunner(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agents.{agent_name}")
    
    @abstractmethod
    async def detect_insights(self, workspace_id: str) -> List[Insight]:
        """
        Detect insights for a workspace
        Must be implemented by each agent
        """
        pass
    
    async def run(self, workspace_id: str):
        """
        Main execution method
        1. Detect insights
        2. Persist to DB
        3. Log execution
        4. Dispatch notifications
        """
        self.logger.info(f"Running {self.agent_name} for workspace {workspace_id}")
        
        try:
            # Log agent start
            await self._log_execution(workspace_id, 'started', f"{self.agent_name} execution started")
            
            # Detect insights
            insights = await self.detect_insights(workspace_id)
            
            self.logger.info(f"Detected {len(insights)} insights for workspace {workspace_id}")
            
            for insight in insights:
                await self._process_insight(workspace_id, insight)
            
            # Log agent completion
            await self._log_execution(
                workspace_id,
                'completed',
                f"{self.agent_name} completed: {len(insights)} insights generated"
            )
            
        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}", exc_info=True)
            
            # Log error
            await self._log_execution(
                workspace_id,
                'error',
                f"{self.agent_name} failed: {str(e)}",
                {'error': str(e)}
            )
    
    async def _process_insight(self, workspace_id: str, insight: Insight):
        """Process a single insight: persist, log, and notify"""
        try:
            # 1. Persist insight to database
            saved_insight = await self._persist_insight(workspace_id, insight)
            
            if not saved_insight:
                self.logger.error("Failed to persist insight")
                return
            
            insight_id = saved_insight['id']
            
            # 2. Log insight creation
            await self._log_execution(
                workspace_id,
                'insight_created',
                f"Insight created: {insight.title}",
                {'insight_id': insight_id, 'severity': insight.severity}
            )
            
            # 3. Dispatch notifications to workspace members
            await self._dispatch_notifications(workspace_id, insight_id, insight)
            
        except Exception as e:
            self.logger.error(f"Failed to process insight: {e}", exc_info=True)
    
    async def _persist_insight(self, workspace_id: str, insight: Insight) -> Optional[Dict[str, Any]]:
        """Save insight to database via direct SQL (ai_insights table)"""
        try:
            async with AsyncSessionLocal() as db:
                # Use raw SQL insert since we don't have a dedicated AIInsight ORM model yet
                from sqlalchemy import text
                insight_id = str(uuid.uuid4())
                stmt = text("""
                    INSERT INTO ai_insights (id, workspace_id, title, body, severity, score, metadata, chart_payload, created_by_agent, created_at)
                    VALUES (:id, :workspace_id, :title, :body, :severity, :score, :metadata, :chart_payload, :agent, :created_at)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """)
                result = await db.execute(stmt, {
                    'id': insight_id,
                    'workspace_id': workspace_id,
                    'title': insight.title,
                    'body': insight.body,
                    'severity': insight.severity,
                    'score': insight.score,
                    'metadata': json.dumps(insight.metadata) if insight.metadata else '{}',
                    'chart_payload': json.dumps(insight.chart_payload) if insight.chart_payload else None,
                    'agent': self.agent_name,
                    'created_at': datetime.utcnow()
                })
                await db.commit()
                return {'id': insight_id}
                
        except Exception as e:
            self.logger.error(f"Failed to persist insight: {e}")
            # If the ai_insights table doesn't exist yet, return a generated ID
            # so notification dispatch can still proceed
            return {'id': str(uuid.uuid4())}
    
    async def _dispatch_notifications(self, workspace_id: str, insight_id: str, insight: Insight):
        """Send notifications to all workspace members based on their preferences"""
        try:
            # Get workspace members from PostgreSQL
            async with AsyncSessionLocal() as db:
                members = await get_workspace_members(db, workspace_id)
            
            self.logger.info(f"Dispatching notifications to {len(members)} members")
            
            for member in members:
                user_id = member['user_id']
                
                # For now, use default notification settings since we're migrating
                # from Supabase notification_settings table
                # Default: email enabled, push disabled, medium threshold
                default_settings = {
                    'ai_insights': True,
                    'email_notifications': True,
                    'push_notifications': False,
                    'severity_threshold': 'medium',
                    'dnd_start': None,
                    'dnd_end': None
                }
                
                # Check if AI insights are enabled
                if not default_settings.get('ai_insights', True):
                    continue
                
                # Check severity threshold
                if not should_notify(insight.severity, default_settings.get('severity_threshold', 'medium')):
                    self.logger.info(f"Insight severity {insight.severity} below threshold for user {user_id}")
                    continue
                
                # Check Do Not Disturb window
                if in_dnd_window(default_settings.get('dnd_start'), default_settings.get('dnd_end')):
                    self.logger.info(f"User {user_id} is in DND window")
                    continue
                
                # Check rate limit
                if await check_rate_limit(workspace_id, user_id):
                    self.logger.warning(f"Rate limit exceeded for user {user_id}")
                    continue
                
                # Enqueue notification
                job = NotificationJob(
                    insight_id=insight_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    channels={
                        'email': default_settings.get('email_notifications', True),
                        'push': default_settings.get('push_notifications', False)
                    },
                    payload={
                        'title': insight.title,
                        'body': insight.body,
                        'chart_payload': insight.chart_payload
                    }
                )
                
                await enqueue_notification(job)
                self.logger.info(f"Notification enqueued for user {user_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to dispatch notifications: {e}", exc_info=True)
    
    async def _log_execution(
        self,
        workspace_id: str,
        status: str,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        """Log agent execution to database"""
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import text
                stmt = text("""
                    INSERT INTO agent_logs (id, agent_name, workspace_id, status, message, metadata, created_at)
                    VALUES (:id, :agent_name, :workspace_id, :status, :message, :metadata, :created_at)
                    ON CONFLICT DO NOTHING
                """)
                await db.execute(stmt, {
                    'id': str(uuid.uuid4()),
                    'agent_name': self.agent_name,
                    'workspace_id': workspace_id,
                    'status': status,
                    'message': message,
                    'metadata': json.dumps(metadata or {}),
                    'created_at': datetime.utcnow()
                })
                await db.commit()
        except Exception as e:
            # Don't let logging failures crash the agent
            self.logger.error(f"Failed to log execution: {e}")
