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
FROM_EMAIL = "insights@ai20insights.tech"  # Your professional domain
APP_URL = "https://naveen-2007-ai-business-analyst.hf.space"  # Your production website


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
        logger.warning("RESEND_API_KEY not configured, skipping email send")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": f"AI Business Analyst <{FROM_EMAIL}>",
                    "to": [to_email],
                    "subject": f"🤖 AI Insight: {title}",
                    "html": html_content,
                    "text": render_plain_text_email(title, body),  # Plain text version
                    "reply_to": FROM_EMAIL,
                    "headers": {
                        "X-Entity-Ref-ID": workspace_id or "default",
                    }
                }
            )
            response.raise_for_status()
            logger.info(f"Email sent to {to_email}: {title}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise


def render_insight_email_template(
    title: str,
    body: str,
    chart_payload: Optional[dict],
    workspace_id: str
) -> str:
    """Render premium HTML email template for insight notification"""
    
    # Build action button based on chart availability
    action_button = ""
    if chart_payload:
        action_button = f'''
        <table cellpadding="0" cellspacing="0" style="margin: 25px 0;">
            <tr>
                <td style="border-radius: 8px; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);">
                    <a href="{APP_URL}/chat" 
                       style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px;">
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
                <td style="border-radius: 8px; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);">
                    <a href="{APP_URL}/chat" 
                       style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px;">
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
        <title>Business Intelligence Alert</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.08);">
                        <!-- Professional Header with Gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 40px 30px; text-align: center;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <div style="display: inline-block; background: rgba(249, 115, 22, 0.15); padding: 12px 24px; border-radius: 50px; margin-bottom: 16px;">
                                                <span style="color: #f97316; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Business Intelligence</span>
                                            </div>
                                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; line-height: 1.3;">
                                                AI Business Analyst
                                            </h1>
                                            <p style="margin: 12px 0 0 0; color: #cbd5e1; font-size: 15px;">
                                                Enterprise Analytics Platform
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
                                <div style="display: inline-block; background: #fef3c7; color: #92400e; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; margin-bottom: 20px;">
                                    📊 New Insight Available
                                </div>
                                
                                <!-- Title -->
                                <h2 style="margin: 0 0 16px 0; color: #0f172a; font-size: 22px; font-weight: 700; line-height: 1.4;">
                                    {title}
                                </h2>
                                
                                <!-- Body Content -->
                                <p style="margin: 0 0 24px 0; color: #475569; line-height: 1.7; font-size: 15px;">
                                    {body}
                                </p>
                                
                                <!-- Action Button -->
                                {action_button}
                                
                                <!-- Divider -->
                                <div style="height: 1px; background: linear-gradient(to right, transparent, #e2e8f0, transparent); margin: 30px 0;"></div>
                                
                                <!-- Additional Info -->
                                <p style="margin: 0; color: #64748b; font-size: 13px; line-height: 1.6;">
                                    💡 This insight was generated by our AI analytics engine based on your latest business data. 
                                    <a href="{APP_URL}/chat" style="color: #f97316; text-decoration: none; font-weight: 600;">Ask questions</a> or 
                                    <a href="{APP_URL}" style="color: #f97316; text-decoration: none; font-weight: 600;">view your dashboard</a> for more details.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px; background: #f8fafc; border-top: 1px solid #e2e8f0;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0 0 12px 0; color: #0f172a; font-size: 14px; font-weight: 600;">
                                                AI Business Analyst Enterprise
                                            </p>
                                            <p style="margin: 0 0 16px 0; color: #64748b; font-size: 13px;">
                                                Advanced Analytics • Predictive Insights • Business Intelligence
                                            </p>
                                            <p style="margin: 0; font-size: 12px;">
                                                <a href="{APP_URL}" style="color: #f97316; text-decoration: none; margin: 0 10px;">Dashboard</a>
                                                <span style="color: #cbd5e1;">|</span>
                                                <a href="{APP_URL}/settings/notifications" style="color: #64748b; text-decoration: none; margin: 0 10px;">Notification Settings</a>
                                                <span style="color: #cbd5e1;">|</span>
                                                <a href="{APP_URL}/help" style="color: #64748b; text-decoration: none; margin: 0 10px;">Help Center</a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Email Footer Text -->
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                        <tr>
                            <td style="text-align: center; padding: 0 30px;">
                                <p style="margin: 0; color: #94a3b8; font-size: 12px; line-height: 1.6;">
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
AI Business Analyst Enterprise
Manage your notification preferences: {APP_URL}/settings/notifications
"""
