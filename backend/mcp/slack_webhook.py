"""
Slack MCP Tool - FREE (Webhook-based)
======================================

Send messages to Slack using incoming webhooks.
FREE - only requires creating a webhook URL in Slack settings.

No paid API access needed!

Setup:
1. Go to your Slack workspace
2. Create an app at https://api.slack.com/apps
3. Enable "Incoming Webhooks"
4. Create a webhook URL for your channel
5. Set SLACK_WEBHOOK_URL environment variable

This is the FREE tier approach - no Bot Token needed.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class SlackMessage:
    """A Slack message"""
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class SlackWebhookMCP:
    """
    Slack integration using FREE incoming webhooks.
    
    No paid API subscription required - just create a webhook URL.
    """
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
        
    def is_configured(self) -> bool:
        """Check if Slack webhook is configured"""
        return bool(self.webhook_url)
    
    def send_message(
        self, 
        text: str,
        blocks: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Slack via webhook.
        
        Args:
            text: Plain text message (required as fallback)
            blocks: Optional Block Kit blocks for rich formatting
            
        Returns:
            {"success": bool, "error": str if failed}
        """
        
        if not self.is_configured():
            logger.warning("Slack webhook not configured")
            return {
                "success": False, 
                "error": "SLACK_WEBHOOK_URL not set. Please configure it to use Slack integration."
            }
        
        payload = {"text": text}
        
        if blocks:
            payload["blocks"] = blocks
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack message sent successfully")
                return {"success": True}
            else:
                logger.error(f"Slack error: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"Slack request error: {e}")
            return {"success": False, "error": str(e)}
    
    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a formatted alert to Slack.
        
        Args:
            title: Alert title
            message: Alert message
            severity: "info", "warning", "error", "success"
            details: Optional key-value details to include
        """
        
        # Color based on severity
        color_map = {
            "info": "#2196F3",
            "warning": "#FFC107",
            "error": "#F44336",
            "success": "#4CAF50"
        }
        color = color_map.get(severity, "#2196F3")
        
        # Emoji based on severity
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅"
        }
        emoji = emoji_map.get(severity, "ℹ️")
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        # Add details if provided
        if details:
            fields = []
            for key, value in list(details.items())[:10]:  # Limit to 10 fields
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:* {value}"
                })
            
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        return self.send_message(f"{emoji} {title}: {message}", blocks)
    
    def send_insight(
        self,
        insight_title: str,
        insight_text: str,
        metric_name: str = None,
        metric_value: str = None,
        change_percent: float = None,
        chart_url: str = None
    ) -> Dict[str, Any]:
        """
        Send a business insight to Slack with rich formatting.
        """
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 DataVision Insight",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{insight_title}*\n\n{insight_text}"
                }
            }
        ]
        
        # Add metric if provided
        if metric_name and metric_value:
            change_emoji = ""
            if change_percent:
                if change_percent > 0:
                    change_emoji = f"📈 +{change_percent:.1f}%"
                else:
                    change_emoji = f"📉 {change_percent:.1f}%"
            
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{metric_name}*\n{metric_value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Change*\n{change_emoji}" if change_emoji else ""
                    }
                ]
            })
        
        # Add chart if provided
        if chart_url:
            blocks.append({
                "type": "image",
                "image_url": chart_url,
                "alt_text": insight_title
            })
        
        blocks.append({"type": "divider"})
        
        return self.send_message(f"📊 {insight_title}", blocks)
    
    def send_daily_summary(
        self,
        metrics: List[Dict[str, Any]],
        highlights: List[str],
        alerts: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send a daily business summary to Slack.
        
        Args:
            metrics: List of {"name": str, "value": str, "change": str}
            highlights: List of key highlights
            alerts: Optional list of alerts/warnings
        """
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📈 Daily Business Summary",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Key Metrics*"
                }
            }
        ]
        
        # Add metrics
        for metric in metrics[:6]:  # Limit to 6
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{metric.get('name', '')}*"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"{metric.get('value', '')} ({metric.get('change', '')})"
                    }
                ]
            })
        
        # Add highlights
        if highlights:
            highlight_text = "\n".join([f"• {h}" for h in highlights[:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*✨ Highlights*\n{highlight_text}"
                }
            })
        
        # Add alerts
        if alerts:
            alert_text = "\n".join([f"• {a}" for a in alerts[:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Alerts*\n{alert_text}"
                }
            })
        
        blocks.append({"type": "divider"})
        
        return self.send_message("📈 Daily Business Summary from DataVision", blocks)


# MCP Tool Interface
class SlackMCPTool:
    """
    MCP-compatible interface for Slack.
    """
    
    name = "slack"
    description = "Send messages to Slack channels using webhooks (FREE)"
    
    def __init__(self, webhook_url: str = None):
        self.slack = SlackWebhookMCP(webhook_url)
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Slack action.
        
        Actions:
        - send: Send a simple message
        - alert: Send an alert
        - insight: Send a business insight
        - summary: Send daily summary
        """
        
        if not self.slack.is_configured():
            return {
                "success": False,
                "error": "Slack not configured. Set SLACK_WEBHOOK_URL environment variable.",
                "setup_help": "Go to https://api.slack.com/apps, create an app, enable Incoming Webhooks, and copy the URL."
            }
        
        try:
            if action == "send":
                return self.slack.send_message(
                    text=params.get("text", ""),
                    blocks=params.get("blocks")
                )
            
            elif action == "alert":
                return self.slack.send_alert(
                    title=params.get("title", "Alert"),
                    message=params.get("message", ""),
                    severity=params.get("severity", "info"),
                    details=params.get("details")
                )
            
            elif action == "insight":
                return self.slack.send_insight(
                    insight_title=params.get("title", ""),
                    insight_text=params.get("text", ""),
                    metric_name=params.get("metric_name"),
                    metric_value=params.get("metric_value"),
                    change_percent=params.get("change_percent")
                )
            
            elif action == "summary":
                return self.slack.send_daily_summary(
                    metrics=params.get("metrics", []),
                    highlights=params.get("highlights", []),
                    alerts=params.get("alerts", [])
                )
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}


# Convenience functions
def send_to_slack(message: str, webhook_url: str = None) -> bool:
    """Quick send to Slack"""
    slack = SlackWebhookMCP(webhook_url)
    result = slack.send_message(message)
    return result.get("success", False)


def send_slack_alert(
    title: str, 
    message: str, 
    severity: str = "info",
    webhook_url: str = None
) -> bool:
    """Send an alert to Slack"""
    slack = SlackWebhookMCP(webhook_url)
    result = slack.send_alert(title, message, severity)
    return result.get("success", False)


# Test
if __name__ == "__main__":
    # Test (requires SLACK_WEBHOOK_URL to be set)
    slack = SlackWebhookMCP()
    
    if slack.is_configured():
        # Test simple message
        result = slack.send_message("🚀 DataVision test message!")
        print(f"Simple message: {result}")
        
        # Test alert
        result = slack.send_alert(
            title="Test Alert",
            message="This is a test alert from DataVision",
            severity="info",
            details={"Source": "Test Script", "Time": "Now"}
        )
        print(f"Alert: {result}")
    else:
        print("Slack not configured. Set SLACK_WEBHOOK_URL to test.")
        print("Note: This is FREE - just create an incoming webhook in Slack!")
