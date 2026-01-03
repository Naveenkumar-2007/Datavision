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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DataVision Intelligence Alert</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #0a0a0b; color: #e2e8f0;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0b; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #141414; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.4); border: 1px solid #262626;">
                        <!-- Professional Header with Gradient -->
                        <tr>
                            <td style="background: linear-gradient(180deg, #111827 0%, #141414 100%); padding: 40px 30px; text-align: center; border-bottom: 1px solid #262626;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <div style="display: inline-block; background: rgba(20, 184, 166, 0.1); padding: 8px 16px; border-radius: 50px; margin-bottom: 20px; border: 1px solid rgba(20, 184, 166, 0.2);">
                                                <span style="color: #2dd4bf; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;">Business Intelligence</span>
                                            </div>
                                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 800; line-height: 1.2; letter-spacing: -0.5px; background: linear-gradient(to right, #2dd4bf, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                                                DataVision
                                            </h1>
                                            <p style="margin: 12px 0 0 0; color: #94a3b8; font-size: 15px;">
                                                Universal Data Intelligence Platform
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Content Section -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <!-- Insight Badge -->
                                <div style="display: inline-block; background: rgba(245, 158, 11, 0.1); color: #fbbf24; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; margin-bottom: 24px; border: 1px solid rgba(245, 158, 11, 0.2);">
                                    📊 New Insight Available
                                </div>
                                
                                <!-- Title -->
                                <h2 style="margin: 0 0 20px 0; color: #f8fafc; font-size: 24px; font-weight: 700; line-height: 1.4;">
                                    {title}
                                </h2>
                                
                                <!-- Body Content -->
                                <p style="margin: 0 0 24px 0; color: #cbd5e1; line-height: 1.8; font-size: 16px;">
                                    {body}
                                </p>
                                
                                <!-- Action Button -->
                                {action_button}
                                
                                <!-- Divider -->
                                <div style="height: 1px; background: #262626; margin: 30px 0;"></div>
                                
                                <!-- Additional Info -->
                                <p style="margin: 0; color: #64748b; font-size: 13px; line-height: 1.6;">
                                    💡 This insight was generated by our AI analytics engine based on your latest business data. 
                                    <a href="{APP_URL}/chat" style="color: #2dd4bf; text-decoration: none; font-weight: 600;">Ask questions</a> or 
                                    <a href="{APP_URL}" style="color: #2dd4bf; text-decoration: none; font-weight: 600;">view your dashboard</a> for more details.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px; background: #111111; border-top: 1px solid #262626;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0 0 12px 0; color: #e2e8f0; font-size: 14px; font-weight: 600;">
                                                DataVision
                                            </p>
                                            <p style="margin: 0 0 16px 0; color: #64748b; font-size: 13px;">
                                                Universal Data Intelligence • Predictive Analytics • AI Insights
                                            </p>
                                            <p style="margin: 0; font-size: 12px;">
                                                <a href="{APP_URL}" style="color: #2dd4bf; text-decoration: none; margin: 0 10px;">Dashboard</a>
                                                <span style="color: #475569;">|</span>
                                                <a href="{APP_URL}/settings/notifications" style="color: #94a3b8; text-decoration: none; margin: 0 10px;">Notification Settings</a>
                                                <span style="color: #475569;">|</span>
                                                <a href="{APP_URL}/help" style="color: #94a3b8; text-decoration: none; margin: 0 10px;">Help Center</a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Email Footer Text -->
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 24px;">
                        <tr>
                            <td style="text-align: center; padding: 0 30px;">
                                <p style="margin: 0; color: #64748b; font-size: 12px; line-height: 1.6;">
                                    You're receiving this email because you have notifications enabled for AI-generated insights.
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
