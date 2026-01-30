# MCP Alert Engine Module
"""
Smart Alert and Notification Engine for MCP Integration.

Features:
- Threshold-based alerts
- Anomaly detection alerts
- Trend-based alerts
- Scheduled monitoring
- Alert prioritization
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import json


class AlertPriority(Enum):
    """Priority levels for alerts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    TREND = "trend"
    COMPARISON = "comparison"
    MISSING_DATA = "missing_data"
    CUSTOM = "custom"


@dataclass
class Alert:
    """A single alert"""
    id: str
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    metric: str
    current_value: Any
    threshold_value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    suggested_action: Optional[str] = None


@dataclass
class AlertRule:
    """Definition of an alert rule"""
    name: str
    metric: str
    condition: str  # 'gt', 'lt', 'eq', 'gte', 'lte', 'change_pct', 'anomaly'
    threshold: Any
    priority: AlertPriority = AlertPriority.MEDIUM
    message_template: str = ""
    enabled: bool = True


class AlertEngine:
    """
    Enterprise Alert Engine MCP.
    
    Provides intelligent alerting:
    - Threshold monitoring
    - Anomaly detection
    - Trend analysis
    - Smart prioritization
    """
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alert_history: List[Alert] = []
        self._alert_counter = 0
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule"""
        self.rules.append(rule)
    
    def add_rules(self, rules: List[Dict]) -> None:
        """Add multiple rules from dict definitions"""
        for rule_dict in rules:
            rule = AlertRule(
                name=rule_dict.get('name', 'Unnamed Rule'),
                metric=rule_dict.get('metric', ''),
                condition=rule_dict.get('condition', 'gt'),
                threshold=rule_dict.get('threshold', 0),
                priority=AlertPriority(rule_dict.get('priority', 'medium')),
                message_template=rule_dict.get('message', ''),
                enabled=rule_dict.get('enabled', True)
            )
            self.rules.append(rule)
    
    def evaluate(
        self,
        data: Any,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Evaluate data against all rules and generate alerts.
        
        Args:
            data: DataFrame or dict with metrics
            context: Additional context (previous values, etc.)
            
        Returns:
            Generated alerts
        """
        try:
            import pandas as pd
            import numpy as np
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)
            
            alerts = []
            context = context or {}
            
            # Evaluate each rule
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                if rule.metric not in df.columns:
                    continue
                
                # Get current value (use latest or aggregate)
                if df[rule.metric].dtype in ['int64', 'float64']:
                    current_value = df[rule.metric].iloc[-1] if len(df) > 0 else 0
                else:
                    current_value = df[rule.metric].iloc[-1] if len(df) > 0 else None
                
                # Evaluate condition
                triggered = self._evaluate_condition(
                    current_value,
                    rule.condition,
                    rule.threshold,
                    context.get(f'{rule.metric}_previous')
                )
                
                if triggered:
                    alert = self._create_alert(rule, current_value, context)
                    alerts.append(alert)
                    self.alert_history.append(alert)
            
            # Run automatic anomaly detection
            anomaly_alerts = self._detect_anomalies(df, context)
            alerts.extend(anomaly_alerts)
            
            # Run trend alerts
            trend_alerts = self._detect_concerning_trends(df, context)
            alerts.extend(trend_alerts)
            
            # Sort by priority
            priority_order = {
                AlertPriority.CRITICAL: 0,
                AlertPriority.HIGH: 1,
                AlertPriority.MEDIUM: 2,
                AlertPriority.LOW: 3
            }
            alerts.sort(key=lambda a: priority_order[a.priority])
            
            return {
                "success": True,
                "alerts": [self._alert_to_dict(a) for a in alerts],
                "alert_count": len(alerts),
                "critical_count": sum(1 for a in alerts if a.priority == AlertPriority.CRITICAL),
                "high_count": sum(1 for a in alerts if a.priority == AlertPriority.HIGH),
                "summary": self._generate_summary(alerts)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _evaluate_condition(
        self,
        current: Any,
        condition: str,
        threshold: Any,
        previous: Optional[Any] = None
    ) -> bool:
        """Evaluate a single condition"""
        try:
            if current is None:
                return False
            
            if condition == 'gt':
                return current > threshold
            elif condition == 'lt':
                return current < threshold
            elif condition == 'eq':
                return current == threshold
            elif condition == 'gte':
                return current >= threshold
            elif condition == 'lte':
                return current <= threshold
            elif condition == 'change_pct' and previous is not None:
                if previous == 0:
                    return False
                change = ((current - previous) / abs(previous)) * 100
                return abs(change) > abs(threshold)
            elif condition == 'drop_pct' and previous is not None:
                if previous == 0:
                    return False
                change = ((current - previous) / abs(previous)) * 100
                return change < -abs(threshold)
            elif condition == 'increase_pct' and previous is not None:
                if previous == 0:
                    return False
                change = ((current - previous) / abs(previous)) * 100
                return change > abs(threshold)
            
            return False
            
        except Exception:
            return False
    
    def _create_alert(
        self,
        rule: AlertRule,
        current_value: Any,
        context: Dict
    ) -> Alert:
        """Create an alert from a triggered rule"""
        self._alert_counter += 1
        
        message = rule.message_template or f"{rule.metric} triggered: {current_value} {rule.condition} {rule.threshold}"
        
        # Generate suggested action
        action = self._suggest_action(rule, current_value)
        
        return Alert(
            id=f"alert_{self._alert_counter}",
            type=AlertType.THRESHOLD,
            priority=rule.priority,
            title=rule.name,
            message=message,
            metric=rule.metric,
            current_value=current_value,
            threshold_value=rule.threshold,
            suggested_action=action,
            metadata={"rule_condition": rule.condition}
        )
    
    def _suggest_action(self, rule: AlertRule, current_value: Any) -> str:
        """Generate suggested action for an alert"""
        actions = {
            'revenue': "Review sales pipeline and customer acquisition strategies",
            'churn': "Analyze customer feedback and implement retention campaigns",
            'cost': "Review expense categories and identify optimization opportunities",
            'inventory': "Check supply chain status and reorder thresholds",
            'performance': "Schedule performance review meeting with stakeholders",
            'error': "Check system logs and contact technical support",
        }
        
        metric_lower = rule.metric.lower()
        for key, action in actions.items():
            if key in metric_lower:
                return action
        
        return f"Monitor {rule.metric} closely and investigate root cause"
    
    def _detect_anomalies(self, df, context: Dict) -> List[Alert]:
        """Automatically detect anomalies in numeric columns"""
        import numpy as np
        
        alerts = []
        
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            if len(df) < 5:  # Need minimum data points
                continue
            
            values = df[col].dropna().values
            if len(values) < 5:
                continue
            
            mean = np.mean(values)
            std = np.std(values)
            
            if std == 0:
                continue
            
            # Check latest value
            latest = values[-1]
            z_score = abs((latest - mean) / std)
            
            if z_score > 3:  # Significant anomaly
                self._alert_counter += 1
                alerts.append(Alert(
                    id=f"alert_{self._alert_counter}",
                    type=AlertType.ANOMALY,
                    priority=AlertPriority.HIGH,
                    title=f"Anomaly Detected: {col}",
                    message=f"{col} value {latest:,.2f} is {z_score:.1f} standard deviations from mean ({mean:,.2f})",
                    metric=col,
                    current_value=latest,
                    threshold_value=mean,
                    suggested_action="Investigate sudden change in this metric",
                    metadata={"z_score": z_score, "mean": mean, "std": std}
                ))
            elif z_score > 2:  # Moderate anomaly
                self._alert_counter += 1
                alerts.append(Alert(
                    id=f"alert_{self._alert_counter}",
                    type=AlertType.ANOMALY,
                    priority=AlertPriority.MEDIUM,
                    title=f"Unusual Value: {col}",
                    message=f"{col} shows unusual value {latest:,.2f} (z-score: {z_score:.1f})",
                    metric=col,
                    current_value=latest,
                    metadata={"z_score": z_score}
                ))
        
        return alerts
    
    def _detect_concerning_trends(self, df, context: Dict) -> List[Alert]:
        """Detect concerning trends in time series data"""
        import numpy as np
        
        alerts = []
        
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            if len(df) < 3:
                continue
            
            values = df[col].dropna().values
            if len(values) < 3:
                continue
            
            # Calculate trend (simple linear regression slope)
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            # Calculate percentage change over series
            if values[0] != 0:
                total_change = ((values[-1] - values[0]) / abs(values[0])) * 100
            else:
                continue
            
            # Alert on significant negative trends
            if total_change < -20 and slope < 0:
                self._alert_counter += 1
                alerts.append(Alert(
                    id=f"alert_{self._alert_counter}",
                    type=AlertType.TREND,
                    priority=AlertPriority.HIGH if total_change < -30 else AlertPriority.MEDIUM,
                    title=f"Declining Trend: {col}",
                    message=f"{col} has declined {abs(total_change):.1f}% over the period",
                    metric=col,
                    current_value=values[-1],
                    threshold_value=values[0],
                    suggested_action="Analyze factors contributing to the decline",
                    metadata={"change_pct": total_change, "slope": slope}
                ))
        
        return alerts
    
    def _alert_to_dict(self, alert: Alert) -> Dict:
        """Convert alert to dictionary"""
        return {
            "id": alert.id,
            "type": alert.type.value,
            "priority": alert.priority.value,
            "title": alert.title,
            "message": alert.message,
            "metric": alert.metric,
            "current_value": alert.current_value,
            "threshold_value": alert.threshold_value,
            "timestamp": alert.timestamp.isoformat(),
            "suggested_action": alert.suggested_action,
            "metadata": alert.metadata
        }
    
    def _generate_summary(self, alerts: List[Alert]) -> str:
        """Generate human-readable summary"""
        if not alerts:
            return "✅ No alerts - all metrics within normal ranges"
        
        critical = sum(1 for a in alerts if a.priority == AlertPriority.CRITICAL)
        high = sum(1 for a in alerts if a.priority == AlertPriority.HIGH)
        
        if critical > 0:
            return f"🚨 {critical} critical alert(s) require immediate attention"
        elif high > 0:
            return f"⚠️ {high} high-priority alert(s) detected"
        else:
            return f"ℹ️ {len(alerts)} alert(s) for review"


# Convenience functions for direct MCP calls
def evaluate_alerts(data, rules=None, context=None):
    """Evaluate data and generate alerts"""
    engine = AlertEngine()
    if rules:
        engine.add_rules(rules)
    return engine.evaluate(data, context)


def detect_anomalies(data):
    """Quick anomaly detection"""
    engine = AlertEngine()
    result = engine.evaluate(data)
    return {
        "anomalies": [a for a in result.get("alerts", []) if a.get("type") == "anomaly"],
        "count": sum(1 for a in result.get("alerts", []) if a.get("type") == "anomaly")
    }


def create_threshold_alert(metric, condition, threshold, priority="medium"):
    """Create a simple threshold alert rule"""
    return {
        "name": f"{metric} {condition} {threshold}",
        "metric": metric,
        "condition": condition,
        "threshold": threshold,
        "priority": priority
    }


# Quick test
if __name__ == "__main__":
    import pandas as pd
    
    # Test data with anomaly
    test_data = pd.DataFrame({
        "revenue": [100000, 105000, 98000, 102000, 150000],  # Last value is anomaly
        "customers": [500, 520, 510, 505, 515],
        "churn_rate": [0.05, 0.06, 0.07, 0.08, 0.12]  # Increasing trend
    })
    
    # Define rules
    rules = [
        {"name": "High Revenue", "metric": "revenue", "condition": "gt", "threshold": 120000, "priority": "high"},
        {"name": "High Churn", "metric": "churn_rate", "condition": "gt", "threshold": 0.10, "priority": "critical"},
    ]
    
    result = evaluate_alerts(test_data, rules)
    
    print("Alert Evaluation Result:")
    print(f"  Summary: {result['summary']}")
    print(f"  Total Alerts: {result['alert_count']}")
    print(f"\nAlerts:")
    for alert in result['alerts']:
        print(f"  [{alert['priority']}] {alert['title']}: {alert['message']}")
        if alert.get('suggested_action'):
            print(f"    → Action: {alert['suggested_action']}")
