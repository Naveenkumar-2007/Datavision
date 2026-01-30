"""
Signup Confirmation Email Service
Uses Resend API to send branded DataVision confirmation emails
"""

import os
import httpx
import secrets
from typing import Optional
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Email configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "insights@ai20insights.tech")
APP_URL = os.getenv("APP_URL", "https://killerkumar-ai-business-analyst.hf.space")

# Storage for pending confirmations
CONFIRMATIONS_DIR = Path(__file__).parent.parent / "storage" / "pending_confirmations"
CONFIRMATIONS_DIR.mkdir(parents=True, exist_ok=True)


async def send_confirmation_email(email: str, user_id: str) -> dict:
    """Send DataVision branded confirmation email using Resend API"""
    
    if not RESEND_API_KEY:
        error_msg = "RESEND_API_KEY not configured"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # Generate confirmation token
    token = secrets.token_urlsafe(32)
    
    # Store pending confirmation
    confirmation_data = {
        "user_id": user_id,
        "email": email,
        "token": token,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    
    token_file = CONFIRMATIONS_DIR / f"{token}.json"
    with open(token_file, 'w') as f:
        json.dump(confirmation_data, f)
    
    # Build confirmation URL - points to frontend which calls API
    confirmation_url = f"{APP_URL}/auth/confirm?token={token}"
    
    # HTML email template
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirm Your DataVision Account</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.08);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">
                                    DataVision
                                </h1>
                                <p style="margin: 8px 0 0 0; color: #14B8A6; font-size: 14px; font-weight: 600;">
                                    Autonomous Data Intelligence Platform
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 16px 0; color: #0f172a; font-size: 22px; font-weight: 700;">
                                    Welcome to DataVision! 👋
                                </h2>
                                
                                <p style="margin: 0 0 24px 0; color: #475569; line-height: 1.7; font-size: 15px;">
                                    Thank you for signing up. Click the button below to confirm your email address and get started with autonomous data intelligence.
                                </p>
                                
                                <!-- Button -->
                                <table cellpadding="0" cellspacing="0" style="margin: 25px 0;">
                                    <tr>
                                        <td style="border-radius: 8px; background: linear-gradient(135deg, #14B8A6 0%, #0D9488 100%);">
                                            <a href="{confirmation_url}" 
                                               style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 15px;">
                                                Confirm Your Email →
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 24px 0 0 0; color: #64748b; font-size: 13px; line-height: 1.6;">
                                    This link will expire in 24 hours. If you didn't create an account with DataVision, you can safely ignore this email.
                                </p>
                                
                                <div style="height: 1px; background: linear-gradient(to right, transparent, #e2e8f0, transparent); margin: 30px 0;"></div>
                                
                                <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                                    If the button doesn't work, copy and paste this URL into your browser:<br>
                                    <a href="{confirmation_url}" style="color: #14B8A6; word-break: break-all;">{confirmation_url}</a>
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                                <p style="margin: 0; color: #64748b; font-size: 13px;">
                                    © 2024 DataVision — Autonomous Data Intelligence Platform
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
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "from": f"DataVision <{FROM_EMAIL}>",
                "to": [email],
                "subject": "Confirm Your DataVision Account",
                "html": html_content,
                "text": f"Welcome to DataVision!\n\nClick this link to confirm your email: {confirmation_url}\n\nThis link expires in 24 hours.",
            }
            
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            logger.info(f"📧 Confirmation email response: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"📧 Resend API error: {error_detail}")
                return {"success": False, "error": error_detail}
            
            result = response.json()
            logger.info(f"✅ Confirmation email sent to {email}! ID: {result.get('id', 'unknown')}")
            return {"success": True, "email_id": result.get('id')}
            
    except Exception as e:
        logger.error(f"❌ Failed to send confirmation email: {str(e)}")
        return {"success": False, "error": str(e)}


async def verify_confirmation_token(token: str) -> dict:
    """Verify a confirmation token and return user info"""
    
    token_file = CONFIRMATIONS_DIR / f"{token}.json"
    
    if not token_file.exists():
        return {"success": False, "error": "Invalid or expired token"}
    
    try:
        with open(token_file, 'r') as f:
            data = json.load(f)
        
        # Check expiration
        expires_at = datetime.fromisoformat(data["expires_at"])
        if datetime.utcnow() > expires_at:
            token_file.unlink()  # Delete expired token
            return {"success": False, "error": "Token has expired"}
        
        # Token is valid - delete it (one-time use)
        token_file.unlink()
        
        return {
            "success": True,
            "user_id": data["user_id"],
            "email": data["email"]
        }
        
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return {"success": False, "error": str(e)}
