"""
Notification Service - Core delivery engine
Handles email and push notifications with retry logic and rate limiting
"""

import asyncio
from datetime import datetime, time as dt_time
from typing import Dict, Any, List
from utils.supabase_admin import get_supabase_admin, get_user_email
from services.email_service import send_insight_email
# Temporarily disabled - uncomment when pywebpush is in requirements.txt
# from services.push_service import send_push_notification
import logging

logger = logging.getLogger(__name__)

supabase = get_supabase_admin()


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
        user_email = await get_user_email(job.user_id)
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
        supabase.table('notifications_history').insert({
            'insight_id': job.insight_id,
            'workspace_id': job.workspace_id,
            'user_id': job.user_id,
            'channel': 'email',
            'payload': job.payload,
            'success': True,
            'attempt': attempt
        }).execute()
        
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
        supabase.table('notifications_history').insert({
            'insight_id': job.insight_id,
            'workspace_id': job.workspace_id,
            'user_id': job.user_id,
            'channel': 'email',
            'payload': job.payload,
            'success': False,
            'attempt': attempt,
            'error_message': str(e)
        }).execute()


async def _send_push_with_retry(job: NotificationJob, attempt: int = 1):
    """Send push notification with exponential backoff retry"""
    MAX_ATTEMPTS = 3
    
    try:
        # Get push tokens for user
        response = supabase.table('push_tokens').select('*').eq('workspace_id', job.workspace_id).eq('user_id', job.user_id).execute()
        
        if not response.data:
            logger.info(f"No push tokens found for user {job.user_id}")
            return
        
        # Send to all tokens
        for token_data in response.data:
            try:
                # Temporarily disabled - uncomment when pywebpush is in requirements.txt
                # await send_push_notification(
                #     token=token_data['token'],
                #     title=job.payload['title'],
                #     body=job.payload['body'],
                #     data={'insight_id': job.insight_id}
                # )
                pass  # Placeholder while push is disabled
            except Exception as token_error:
                logger.error(f"Push failed for token {token_data['id']}: {token_error}")
                # Remove invalid token
                if 'invalid' in str(token_error).lower() or 'expired' in str(token_error).lower():
                    supabase.table('push_tokens').delete().eq('id', token_data['id']).execute()
        
        # Log success
        supabase.table('notifications_history').insert({
            'insight_id': job.insight_id,
            'workspace_id': job.workspace_id,
            'user_id': job.user_id,
            'channel': 'push',
            'payload': job.payload,
            'success': True,
            'attempt': attempt
        }).execute()
        
        logger.info(f"Push sent successfully to user {job.user_id} for insight {job.insight_id}")
        
    except Exception as e:
        logger.error(f"Push send failed (attempt {attempt}): {e}")
        
        if attempt < MAX_ATTEMPTS:
            delay = pow(2, attempt)
            await asyncio.sleep(delay)
            return await _send_push_with_retry(job, attempt + 1)
        
        # Log failure
        supabase.table('notifications_history').insert({
            'insight_id': job.insight_id,
            'workspace_id': job.workspace_id,
            'user_id': job.user_id,
            'channel': 'push',
            'payload': job.payload,
            'success': False,
            'attempt': attempt,
            'error_message': str(e)
        }).execute()


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
    Check if user has exceeded notification rate limit
    Returns True if rate limit exceeded, False otherwise
    """
    # Check notifications sent in last hour
    from datetime import timedelta
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    response = supabase.table('notifications_history').select('id').eq('workspace_id', workspace_id).eq('user_id', user_id).gte('sent_at', one_hour_ago.isoformat()).execute()
    
    count = len(response.data) if response.data else 0
    
    # Limit: 5 notifications per hour per user
    MAX_PER_HOUR = 5
    return count >= MAX_PER_HOUR
