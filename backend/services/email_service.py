"""
Email Service - Send notification emails
Uses Resend API (can be swapped for SendGrid, AWS SES, etc.)
"""

import os
import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Email configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
# FROM_EMAIL must be from a verified domain in Resend
# User has verified: ai20insights.tech
FROM_EMAIL = os.getenv("FROM_EMAIL", "insights@ai20insights.tech")
APP_URL = os.getenv("APP_URL", "https://killerkumar-ai-business-analyst.hf.space")


async def send_insight_email(
    to_email: str,
    title: str,
    body: str,
    chart_payload: Optional[dict] = None,
    workspace_id: str = None
):
    """Send insight notification email"""
    html_content = render_insight_email_template(title, body, chart_payload, workspace_id)
    
    if not RESEND_API_KEY:
        error_msg = "Email service not configured. Please add RESEND_API_KEY to your .env file to enable email functionality."
        logger.warning(error_msg)
        raise Exception(error_msg)
    
    # Log configuration for debugging
    logger.info(f"📧 Sending email from {FROM_EMAIL} to {to_email}")
    logger.info(f"📧 RESEND_API_KEY present: {bool(RESEND_API_KEY)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "from": f"DataVision <{FROM_EMAIL}>",
                "to": [to_email],
                "subject": f"📊 DataVision: {title}",
                "html": html_content,
                "text": render_plain_text_email(title, body),
            }
            
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            # Log response for debugging
            logger.info(f"📧 Resend response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"📧 Resend API error: {error_detail}")
                raise Exception(f"Resend API error ({response.status_code}): {error_detail}")
            
            result = response.json()
            logger.info(f"✅ Email sent successfully! ID: {result.get('id', 'unknown')}")
            return result
            
    except httpx.TimeoutException:
        error_msg = "Email request timed out"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        logger.error(f"❌ Failed to send email: {str(e)}")
        raise


def render_insight_email_template(
    title: str,
    body: str,
    chart_payload: Optional[dict],
    workspace_id: str
) -> str:
    """Render premium HTML email template for insight notification (DataVision Dark Theme)"""
    
    # Build action button based on chart availability
    action_button = ""
    # DataVision Gradient: Teal to Amber
    button_gradient = "linear-gradient(135deg, #0d9488 0%, #d97706 100%)" 
    
    if chart_payload:
        action_button = f'''
        <table cellpadding="0" cellspacing="0" style="margin: 25px 0;">
            <tr>
                <td style="border-radius: 12px; background: {button_gradient}; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);">
                    <a href="{APP_URL}/chat" 
                       style="display: inline-block; padding: 16px 36px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px; letter-spacing: 0.5px;">
                        View Insights in Dashboard →
                    </a>
                </td>
            </tr>
        </table>
        '''
    else:
        action_button = f'''
        <table cellpadding="0" cellspacing="0" style="margin: 25px 0;">
            <tr>
                <td style="border-radius: 12px; background: {button_gradient}; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);">
                    <a href="{APP_URL}/chat" 
                       style="display: inline-block; padding: 16px 36px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px; letter-spacing: 0.5px;">
                        Discuss with AI Analyst →
                    </a>
                </td>
            </tr>
        </table>
        '''
    
    return f'''

    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>DataVision Intelligence Alert</title>
        <style type="text/css">
            body, td, div, p, a, input {{ font-family: 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif; }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0a0a0b; color: #e2e8f0;">
        <!-- Wrapper Table (Forces Background) -->
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0a0a0b;">
            <tr>
                <td align="center" style="padding: 40px 10px;">
                    <!-- Main Card -->
                    <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #141414; border-radius: 16px; overflow: hidden; border: 1px solid #262626; box-shadow: 0 4px 24px rgba(0,0,0,0.5); max-width: 600px;">
                        
                        <!-- Header with Gradient Border Top -->
                        <tr>
                            <td style="background-color: #1a1a1a; padding: 40px 30px; border-bottom: 1px solid #262626; text-align: center;">
                                <div style="display: inline-block; padding: 6px 12px; border-radius: 50px; background-color: rgba(20, 184, 166, 0.1); border: 1px solid rgba(20, 184, 166, 0.2); margin-bottom: 16px;">
                                    <span style="color: #2dd4bf; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">AI Analyst Insight</span>
                                </div>
                                <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff;">
                                    <span style="color: #2dd4bf;">Data</span><span style="color: #f59e0b;">Vision</span>
                                </h1>
                            </td>
                        </tr>

                        <!-- Content Body -->
                        <tr>
                            <td style="padding: 40px 30px; background-color: #141414;">
                                <h2 style="margin: 0 0 16px 0; font-size: 22px; font-weight: 700; color: #ffffff;">
                                    {title}
                                </h2>
                                
                                <div style="color: #cccccc; font-size: 16px; line-height: 1.6; margin-bottom: 24px;">
                                    {body.replace(chr(10), '<br/>')}
                                </div>

                                <!-- Action Button -->
                                {action_button}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #0f0f0f; padding: 24px; text-align: center; border-top: 1px solid #262626;">
                                <p style="margin: 0; color: #64748b; font-size: 13px;">
                                    &copy; 2026 DataVision AI. All rights reserved.
                                </p>
                                <p style="margin: 8px 0 0 0; font-size: 12px; color: #475569;">
                                    <a href="{APP_URL}" style="color: #2dd4bf; text-decoration: none;">Dashboard</a> &bull; 
                                    <a href="{APP_URL}/settings" style="color: #2dd4bf; text-decoration: none;">Unsubscribe</a>
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''


# Alternative: Plain text version for email clients that don't support HTML
def render_plain_text_email(title: str, body: str) -> str:
    """Render plain text version of email"""
    return f"""
AI INSIGHT DETECTED
==================

{title}

{body}

View in dashboard: {APP_URL}/dashboard

---
DataVision - Universal Data Intelligence
Manage your notification preferences: {APP_URL}/settings/notifications
"""
