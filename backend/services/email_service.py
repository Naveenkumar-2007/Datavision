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
APP_URL = os.getenv("APP_URL", "https://datavision-ai-datavision.hf.space")


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
    """Render ultra-premium HTML email template for insight notification (DataVision Enterprise)"""
    
    # Modern Enterprise Gradient (Teal/Emerald)
    button_gradient = "linear-gradient(135deg, #0d9488 0%, #059669 100%)" 
    
    # Check if we should link to a specific chat context or general dashboard
    cta_text = "View Dashboard Insights"
    if not chart_payload:
        cta_text = "Discuss with AI Analyst"
        
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>{title}</title>
        <!--[if mso]>
        <style>
            table {{border-collapse:collapse;border:0;padding:0;margin:0;}}
            div, td {{font-family: Arial, sans-serif !important;}}
        </style>
        <![endif]-->
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f5; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <!-- Main Container -->
                    <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; border-radius: 16px; border: 1px solid #e4e4e7; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05); overflow: hidden;">
                        
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 48px; background: #fafafa; border-bottom: 1px solid #f4f4f5;">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td>
                                            <div style="display: inline-block; padding: 6px 12px; background: rgba(13, 148, 136, 0.1); border-radius: 20px; border: 1px solid rgba(13, 148, 136, 0.2); margin-bottom: 24px;">
                                                <span style="color: #0d9488; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">✨ AI Intelligence Digest</span>
                                            </div>
                                            <h1 style="margin: 0 0 12px 0; font-size: 32px; font-weight: 700; color: #18181b; letter-spacing: -0.02em; line-height: 1.2;">
                                                {title}
                                            </h1>
                                            <p style="margin: 0; font-size: 15px; color: #71717a; font-weight: 400;">
                                                Autonomous Insights powered by Nvidia Enterprise LLMs.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Content Body -->
                        <tr>
                            <td style="padding: 48px;">
                                <!-- LLM Generated Content -->
                                <div style="font-size: 16px; color: #3f3f46; line-height: 1.7; margin-bottom: 40px; font-weight: 400;">
                                    {body.replace(chr(10), '<br/>')}
                                </div>
                                
                                <!-- Call to Action -->
                                <table cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td align="center" style="padding-top: 16px; border-top: 1px solid #f4f4f5;">
                                            <table cellpadding="0" cellspacing="0" style="margin: 24px auto 0 auto;">
                                                <tr>
                                                    <td style="border-radius: 8px; background: {button_gradient};">
                                                        <a href="{APP_URL}/chat" 
                                                           style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px; box-shadow: 0 4px 14px 0 rgba(13, 148, 136, 0.39);">
                                                            {cta_text} &rarr;
                                                        </a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 32px 48px; background-color: #fafafa; border-top: 1px solid #f4f4f5; text-align: center;">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td align="center">
                                            <h2 style="margin: 0 0 12px 0; font-size: 18px; font-weight: 800; letter-spacing: -0.02em;">
                                                <span style="color: #0d9488;">Data</span><span style="color: #18181b;">Vision</span>
                                            </h2>
                                            <p style="margin: 0 0 16px 0; font-size: 13px; color: #71717a; line-height: 1.5;">
                                                This report was autonomously generated by your DataVision agents.<br/>
                                                If you wish to change your notification preferences, you can do so in your <a href="{APP_URL}/settings" style="color: #0d9488; text-decoration: underline;">account settings</a>.
                                            </p>
                                            <p style="margin: 0; font-size: 12px; color: #a1a1aa;">
                                                &copy; 2026 DataVision AI Analytics. All rights reserved.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
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


async def send_password_reset_email(to_email: str, reset_link: str) -> dict:
    """Send a branded password reset email"""
    
    if not RESEND_API_KEY:
        error_msg = "Email service not configured. Please add RESEND_API_KEY to your .env file."
        logger.warning(error_msg)
        raise Exception(error_msg)
    
    html_content = render_password_reset_template(reset_link)
    plain_text = f"""
DataVision Password Reset
========================

We received a request to reset your password for your DataVision account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

---
DataVision AI Analytics
{APP_URL}
"""
    
    logger.info(f"📧 Sending password reset email to {to_email}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "from": f"DataVision <{FROM_EMAIL}>",
                "to": [to_email],
                "subject": "🔐 Reset Your DataVision Password",
                "html": html_content,
                "text": plain_text,
            }
            
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            logger.info(f"📧 Resend response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"📧 Resend API error: {error_detail}")
                raise Exception(f"Resend API error ({response.status_code}): {error_detail}")
            
            result = response.json()
            logger.info(f"✅ Password reset email sent! ID: {result.get('id', 'unknown')}")
            return result
            
    except httpx.TimeoutException:
        error_msg = "Email request timed out"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email: {str(e)}")
        raise


def render_password_reset_template(reset_link: str) -> str:
    """Render branded HTML password reset email template"""
    
    return f'''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Reset Your Password - DataVision</title>
    <style type="text/css">
        body, td, div, p, a, input {{ font-family: 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif; }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0b; color: #e2e8f0;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0a0a0b;">
        <tr>
            <td align="center" style="padding: 40px 10px;">
                <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #141414; border-radius: 16px; overflow: hidden; border: 1px solid #262626; box-shadow: 0 4px 24px rgba(0,0,0,0.5); max-width: 600px;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #1a1a1a; padding: 40px 30px; border-bottom: 1px solid #262626; text-align: center;">
                            <div style="display: inline-block; padding: 6px 12px; border-radius: 50px; background-color: rgba(20, 184, 166, 0.1); border: 1px solid rgba(20, 184, 166, 0.2); margin-bottom: 16px;">
                                <span style="color: #2dd4bf; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">🔐 Password Reset</span>
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
                                Reset Your Password
                            </h2>
                            
                            <div style="color: #cccccc; font-size: 16px; line-height: 1.6; margin-bottom: 24px;">
                                <p style="margin: 0 0 16px 0;">Hi there! 👋</p>
                                <p style="margin: 0 0 16px 0;">We received a request to reset your password for your DataVision account.</p>
                                <p style="margin: 0 0 16px 0;">Click the button below to create a new password:</p>
                            </div>

                            <!-- Reset Button -->
                            <table cellpadding="0" cellspacing="0" style="margin: 25px 0;">
                                <tr>
                                    <td style="border-radius: 12px; background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%); box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);">
                                        <a href="{reset_link}" 
                                           style="display: inline-block; padding: 16px 36px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px; letter-spacing: 0.5px;">
                                            🔑 Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <div style="color: #888888; font-size: 14px; line-height: 1.6; margin-top: 24px; padding-top: 20px; border-top: 1px solid #262626;">
                                <p style="margin: 0 0 12px 0;"><strong>⏰ This link expires in 1 hour.</strong></p>
                                <p style="margin: 0 0 12px 0;">If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                                <p style="margin: 0; color: #666666; font-size: 12px;">
                                    If the button doesn't work, copy and paste this link into your browser:<br/>
                                    <span style="color: #2dd4bf; word-break: break-all;">{reset_link}</span>
                                </p>
                            </div>
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
                                <a href="{APP_URL}/settings" style="color: #2dd4bf; text-decoration: none;">Settings</a>
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

