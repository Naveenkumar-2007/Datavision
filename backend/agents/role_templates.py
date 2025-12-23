# Role Intelligence - Role-Based Response Formatting
"""
Adapts responses based on user role for personalized, relevant answers.
Executives get summaries, Analysts get detail, Managers get actionable insights.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import re


class UserRole(Enum):
    """User roles for response customization"""
    EXECUTIVE = "executive"  # CEO, CFO, CTO, VP - Want summaries
    MANAGER = "manager"      # Sales/Marketing/Ops Manager - Want actionable insights
    ANALYST = "analyst"      # Data/Business Analyst - Want detailed data
    OPERATOR = "operator"    # Support/Operations - Want quick facts


@dataclass
class RoleFormat:
    """Formatting rules for a specific role"""
    max_length: int
    format_style: str  # "bullet_points", "tables", "narrative"
    include_recommendations: bool
    include_charts: bool
    detail_level: str  # "summary", "standard", "detailed"
    comparison_style: str  # "percentage", "absolute", "both"
    time_horizon: str  # "current", "short_term", "long_term"
    greeting_style: str  # "formal", "professional", "casual"


# Role-specific formatting rules
ROLE_FORMATS: Dict[UserRole, RoleFormat] = {
    UserRole.EXECUTIVE: RoleFormat(
        max_length=400,
        format_style="bullet_points",
        include_recommendations=True,
        include_charts=True,
        detail_level="summary",
        comparison_style="percentage",
        time_horizon="current",
        greeting_style="formal",
    ),
    UserRole.MANAGER: RoleFormat(
        max_length=800,
        format_style="tables",
        include_recommendations=True,
        include_charts=True,
        detail_level="standard",
        comparison_style="both",
        time_horizon="short_term",
        greeting_style="professional",
    ),
    UserRole.ANALYST: RoleFormat(
        max_length=2000,
        format_style="tables",
        include_recommendations=False,
        include_charts=True,
        detail_level="detailed",
        comparison_style="absolute",
        time_horizon="long_term",
        greeting_style="professional",
    ),
    UserRole.OPERATOR: RoleFormat(
        max_length=300,
        format_style="bullet_points",
        include_recommendations=False,
        include_charts=False,
        detail_level="summary",
        comparison_style="absolute",
        time_horizon="current",
        greeting_style="casual",
    ),
}


def get_role_from_string(role_str: str) -> UserRole:
    """Convert string to UserRole enum"""
    role_str = role_str.lower().strip()
    
    # Map common titles to roles
    executive_titles = ["ceo", "cfo", "cto", "coo", "vp", "vice president", "director", "founder", "owner", "executive"]
    manager_titles = ["manager", "head", "lead", "supervisor", "team lead"]
    analyst_titles = ["analyst", "data", "researcher", "specialist"]
    operator_titles = ["support", "operations", "operator", "agent", "coordinator"]
    
    if role_str in ["executive"] or any(t in role_str for t in executive_titles):
        return UserRole.EXECUTIVE
    elif role_str in ["manager"] or any(t in role_str for t in manager_titles):
        return UserRole.MANAGER
    elif role_str in ["analyst"] or any(t in role_str for t in analyst_titles):
        return UserRole.ANALYST
    elif role_str in ["operator"] or any(t in role_str for t in operator_titles):
        return UserRole.OPERATOR
    
    # Default to analyst for unknown roles
    return UserRole.ANALYST


def get_role_format(role: UserRole) -> RoleFormat:
    """Get formatting rules for a role"""
    return ROLE_FORMATS.get(role, ROLE_FORMATS[UserRole.ANALYST])


def get_role_prompt_modifier(role: UserRole) -> str:
    """
    Get role-specific prompt modifier to inject into LLM system prompt.
    This shapes how the LLM responds based on the user's role.
    """
    role_format = get_role_format(role)
    
    if role == UserRole.EXECUTIVE:
        return f"""
═══════════════════════════════════════════════════════════════
                    EXECUTIVE RESPONSE MODE
═══════════════════════════════════════════════════════════════
The user is a C-level executive. Format responses accordingly:

FORMAT RULES:
• Lead with the KEY INSIGHT in bold (one sentence)
• Maximum 3-4 bullet points for supporting data
• Include ONE actionable recommendation
• Use PERCENTAGES for comparisons (e.g., "up 15%" not "+$150K")
• Keep total response under {role_format.max_length} characters

LANGUAGE:
• Use executive language: "bottom line", "key takeaway", "action required"
• Focus on: revenue impact, growth rate, risk, strategic decisions
• Avoid: granular details, raw numbers unless requested

STRUCTURE:
**[Key Insight in one sentence]**

• Supporting point 1
• Supporting point 2  
• Supporting point 3

💡 **Recommendation:** [One clear action]
"""
    
    elif role == UserRole.MANAGER:
        return f"""
═══════════════════════════════════════════════════════════════
                    MANAGER RESPONSE MODE
═══════════════════════════════════════════════════════════════
The user is a Manager. Format responses accordingly:

FORMAT RULES:
• Lead with the answer, then provide context
• Use TABLES for data breakdowns (customers, products, metrics)
• Include comparison to targets/benchmarks
• Provide actionable next steps
• Keep total response under {role_format.max_length} characters

LANGUAGE:
• Use operational language: "target", "performance", "action items"
• Focus on: team metrics, period-over-period, achievable goals
• Show both percentage AND absolute values

STRUCTURE:
**[Direct Answer]**

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| ... | ... | ... | ✅/⚠️/❌ |

**Action Items:**
1. [Specific action]
2. [Specific action]
"""

    elif role == UserRole.ANALYST:
        return f"""
═══════════════════════════════════════════════════════════════
                    ANALYST RESPONSE MODE
═══════════════════════════════════════════════════════════════
The user is a Data/Business Analyst. Format responses accordingly:

FORMAT RULES:
• Provide COMPLETE data tables with all rows
• Include methodology notes where relevant
• Show RAW NUMBERS, not just percentages
• Include sample sizes and confidence levels
• Maximum {role_format.max_length} characters allowed for detail

DATA REQUIREMENTS:
• Full breakdown by dimension (customer, product, time)
• Statistical context (mean, median, outliers)
• Include ALL available data points in tables

STRUCTURE:
**[Summary Finding]**

| Dimension | Value | % of Total | Notes |
|-----------|-------|------------|-------|
| ... (all rows) | ... | ... | ... |

**Methodology:** [How this was calculated]
**Data Source:** [Source files]
"""

    else:  # OPERATOR
        return f"""
═══════════════════════════════════════════════════════════════
                    OPERATOR RESPONSE MODE
═══════════════════════════════════════════════════════════════
The user is an Operator/Support. Format responses accordingly:

FORMAT RULES:
• QUICK FACTS only - no fluff
• Maximum 3 bullet points
• Numbers only, no charts
• Keep under {role_format.max_length} characters

STRUCTURE:
• **[Fact 1]**
• **[Fact 2]**
• **[Fact 3]**
"""


def format_response_for_role(response: str, role: UserRole) -> str:
    """
    Post-process LLM response to fit role-specific format.
    Applies length limits and style adjustments.
    """
    role_format = get_role_format(role)
    
    # Apply length limit (with some buffer)
    max_len = role_format.max_length + 200  # Buffer for formatting
    if len(response) > max_len:
        # Truncate at a natural break point
        truncated = response[:max_len]
        
        # Find last complete sentence or bullet
        last_period = truncated.rfind('.')
        last_bullet = truncated.rfind('\n•')
        last_pipe = truncated.rfind('|')
        
        cut_point = max(last_period, last_bullet, last_pipe)
        if cut_point > max_len // 2:
            response = truncated[:cut_point + 1]
            if not response.strip().endswith(('.', '|')):
                response += "..."
    
    # Remove recommendations if role doesn't need them
    if not role_format.include_recommendations:
        response = re.sub(r'\n\n?💡\s*\*\*Recommendation:?\*\*.*?(?=\n\n|\n#{|$)', '', response, flags=re.DOTALL)
        response = re.sub(r'\n\n?\*\*Recommendation:?\*\*.*?(?=\n\n|\n#{|$)', '', response, flags=re.DOTALL)
    
    # For executive role, convert tables to bullet points if too detailed
    if role == UserRole.EXECUTIVE:
        # Count table rows
        table_rows = len(re.findall(r'^\|[^|]+\|', response, re.MULTILINE))
        if table_rows > 5:  # Too many rows for executive
            # Keep header and top 3 data rows only
            lines = response.split('\n')
            new_lines = []
            table_section = False
            row_count = 0
            for line in lines:
                if line.strip().startswith('|'):
                    table_section = True
                    row_count += 1
                    if row_count <= 4:  # Header + separator + 2 data rows
                        new_lines.append(line)
                    elif row_count == 5:
                        new_lines.append("| ... | *see details below* |")
                else:
                    if table_section and row_count > 4:
                        table_section = False
                    new_lines.append(line)
            response = '\n'.join(new_lines)
    
    return response.strip()


def get_role_greeting(role: UserRole, company_name: str = "Your Company") -> str:
    """Get appropriate greeting for user role"""
    role_format = get_role_format(role)
    
    if role_format.greeting_style == "formal":
        return f"Analysis for {company_name}:"
    elif role_format.greeting_style == "professional":
        return f"Here's what I found:"
    else:
        return "Quick update:"
