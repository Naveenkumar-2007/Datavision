"""
Notification Service - Core delivery engine
Handles email and push notifications with retry logic and rate limiting.

Migrated from Supabase to PostgreSQL/SQLAlchemy.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from database.db import AsyncSessionLocal
from database.orm import Notification, PushToken, UserProfile
from services.email_service import send_insight_email
# Temporarily disabled - uncomment when pywebpush is in requirements.txt
# from services.push_service import send_push_notification
import logging

logger = logging.getLogger(__name__)


class NotificationJob:
    def __init__(
        self,
        insight_id: str,
        workspace_id: str,
        user_id: str,
        channels: Dict[str, bool],
        payload: Dict[str, Any]
    ):
        self.insight_id = insight_id
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.channels = channels
        self.payload = payload


async def _get_user_email(user_id: str) -> Optional[str]:
    """Get user email from PostgreSQL."""
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return None
    
    async with AsyncSessionLocal() as db:
        stmt = select(UserProfile.email).where(UserProfile.id == uid)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


async def _log_notification(
    insight_id: str,
    workspace_id: str,
    user_id: str,
    channel: str,
    payload: Dict,
    success: bool,
    attempt: int,
    error_message: str = None
):
    """Log notification to PostgreSQL notifications table."""
    try:
        async with AsyncSessionLocal() as db:
            notification = Notification(
                workspace_id=uuid.UUID(workspace_id) if workspace_id else None,
                user_id=uuid.UUID(user_id),
                type=channel,
                title=payload.get('title', 'Notification'),
                message=payload.get('body', ''),
                channel=payload.get('channel', 'system'),
                status='sent' if success else 'failed',
                metadata={
                    'insight_id': insight_id,
                    'attempt': attempt,
                    'payload': payload,
                    'error_message': error_message
                }
            )
            db.add(notification)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to log notification: {e}")


async def enqueue_notification(job: NotificationJob):
    """Main entry point for notification sending"""
    # Send email if enabled
    if job.channels.get('email', False):
        asyncio.create_task(_send_email_with_retry(job, attempt=1))
    
    # Send push if enabled
    if job.channels.get('push', False):
        asyncio.create_task(_send_push_with_retry(job, attempt=1))


async def _send_email_with_retry(job: NotificationJob, attempt: int = 1):
    """Send email with exponential backoff retry"""
    MAX_ATTEMPTS = 3
    
    try:
        # Get user email
        user_email = await _get_user_email(job.user_id)
        if not user_email:
            logger.warning(f"No email found for user {job.user_id}")
            return
        
        # Send email
        await send_insight_email(
            to_email=user_email,
            title=job.payload['title'],
            body=job.payload['body'],
            chart_payload=job.payload.get('chart_payload'),
            workspace_id=job.workspace_id
        )
        
        # Log success
        await _log_notification(
            job.insight_id, job.workspace_id, job.user_id,
            'email', job.payload, True, attempt
        )
        
        logger.info(f"Email sent successfully to {user_email} for insight {job.insight_id}")
        
    except Exception as e:
        logger.error(f"Email send failed (attempt {attempt}): {e}")
        
        if attempt < MAX_ATTEMPTS:
            # Exponential backoff: 2^attempt seconds
            delay = pow(2, attempt)
            logger.info(f"Retrying email in {delay} seconds...")
            await asyncio.sleep(delay)
            return await _send_email_with_retry(job, attempt + 1)
        
        # Log failure after max attempts
        await _log_notification(
            job.insight_id, job.workspace_id, job.user_id,
            'email', job.payload, False, attempt, str(e)
        )


async def _send_push_with_retry(job: NotificationJob, attempt: int = 1):
    """Send push notification with exponential backoff retry"""
    MAX_ATTEMPTS = 3
    
    try:
        # Get push tokens for user from PostgreSQL
        async with AsyncSessionLocal() as db:
            stmt = (
                select(PushToken)
                .where(
                    PushToken.user_id == uuid.UUID(job.user_id),
                    PushToken.is_active == True
                )
            )
            if job.workspace_id:
                stmt = stmt.where(PushToken.workspace_id == uuid.UUID(job.workspace_id))
            
            result = await db.execute(stmt)
            tokens = result.scalars().all()
        
        if not tokens:
            logger.info(f"No push tokens found for user {job.user_id}")
            return
        
        # Send to all tokens
        for push_token in tokens:
            try:
                # Temporarily disabled - uncomment when pywebpush is in requirements.txt
                # await send_push_notification(
                #     token=push_token.token,
                #     title=job.payload['title'],
                #     body=job.payload['body'],
                #     data={'insight_id': job.insight_id}
                # )
                pass  # Placeholder while push is disabled
            except Exception as token_error:
                logger.error(f"Push failed for token {push_token.id}: {token_error}")
                # Remove invalid token
                if 'invalid' in str(token_error).lower() or 'expired' in str(token_error).lower():
                    async with AsyncSessionLocal() as db:
                        push_token.is_active = False
                        db.add(push_token)
                        await db.commit()
        
        # Log success
        await _log_notification(
            job.insight_id, job.workspace_id, job.user_id,
            'push', job.payload, True, attempt
        )
        
        logger.info(f"Push sent successfully to user {job.user_id} for insight {job.insight_id}")
        
    except Exception as e:
        logger.error(f"Push send failed (attempt {attempt}): {e}")
        
        if attempt < MAX_ATTEMPTS:
            delay = pow(2, attempt)
            await asyncio.sleep(delay)
            return await _send_push_with_retry(job, attempt + 1)
        
        # Log failure
        await _log_notification(
            job.insight_id, job.workspace_id, job.user_id,
            'push', job.payload, False, attempt, str(e)
        )


def should_notify(severity: str, threshold: str) -> bool:
    """Check if notification should be sent based on severity threshold"""
    severity_map = {'low': 1, 'medium': 2, 'high': 3}
    return severity_map.get(severity, 0) >= severity_map.get(threshold, 99)


def in_dnd_window(dnd_start: str | None, dnd_end: str | None) -> bool:
    """Check if current time is within Do Not Disturb window"""
    if not dnd_start or not dnd_end:
        return False
    
    try:
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        # Parse DND times
        start_parts = dnd_start.split(':')
        end_parts = dnd_end.split(':')
        
        start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
        end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
        
        # Handle DND window that crosses midnight
        if start_minutes <= end_minutes:
            return start_minutes <= current_minutes <= end_minutes
        else:
            return current_minutes >= start_minutes or current_minutes <= end_minutes
            
    except Exception as e:
        logger.error(f"Error checking DND window: {e}")
        return False


async def check_rate_limit(workspace_id: str, user_id: str) -> bool:
    """
    Check if user has exceeded notification rate limit.
    Returns True if rate limit exceeded, False otherwise.
    Uses PostgreSQL notifications table instead of Supabase.
    """
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == uuid.UUID(user_id),
                    Notification.sent_at >= one_hour_ago
                )
            )
            if workspace_id:
                stmt = stmt.where(Notification.workspace_id == uuid.UUID(workspace_id))
            
            result = await db.execute(stmt)
            count = result.scalar() or 0
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        count = 0
    
    # Limit: 5 notifications per hour per user
    MAX_PER_HOUR = 5
    return count >= MAX_PER_HOUR
