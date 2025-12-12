"""
Push Service - Send web push notifications
Uses pywebpush library with VAPID authentication
"""

import os
import json
from pywebpush import webpush, WebPushException
import logging

logger = logging.getLogger(__name__)

# VAPID keys (generate with: webpush.generate_vapid_keys())
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {"sub": "mailto:admin@ai-business-analyst.com"}


async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict = None
):
    """Send push notification to a specific token"""
    
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        logger.warning("VAPID keys not configured, skipping push send")
        return
    
    try:
        # Parse subscription (token is JSON string)
        subscription_info = json.loads(token)
        
        # Create notification payload
        notification_payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/logo.png",
            "badge": "/badge.png",
            "data": data or {},
            "actions": [
                {"action": "open", "title": "View Dashboard"},
                {"action": "dismiss", "title": "Dismiss"}
            ]
        })
        
        # Send push notification
        webpush(
            subscription_info=subscription_info,
            data=notification_payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        
        logger.info(f"Push notification sent: {title}")
        
    except WebPushException as e:
        logger.error(f"WebPush error: {e}")
        # Check if token is invalid/expired
        if e.response and e.response.status_code in [404, 410]:
            raise Exception("Token invalid or expired")
        raise
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        raise


def generate_vapid_keys():
    """
    Utility to generate VAPID key pair
    Run this once and store keys in environment variables
    """
    from py_vapid import Vapid
    from cryptography.hazmat.primitives import serialization
    
    vapid = Vapid()
    vapid.generate_keys()
    
    # Serialize public key
    public_key = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Serialize private key
    private_key = vapid.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    import base64
    public_key_b64 = base64.urlsafe_b64encode(public_key).decode('utf-8').rstrip('=')
    private_key_str = private_key.decode('utf-8')
    
    print("\n" + "="*60)
    print("VAPID Keys Generated Successfully!")
    print("="*60)
    print("\nAdd these to your .env files:\n")
    print("Backend (.env):")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print(f"VAPID_PRIVATE_KEY={private_key_str}")
    print(f"\nFrontend (.env):")
    print(f"VITE_VAPID_PUBLIC_KEY={public_key_b64}")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Run to generate VAPID keys
    generate_vapid_keys()
