"""
🎨 CLAUDE-STYLE INTELLIGENT REPORT GENERATOR
=============================================

Generates professional reports using LLM for:
- Dynamic content based on user's data
- Real Plotly visualizations
- Intelligent insights and recommendations
- Multiple export formats

Like Claude's Artifacts - generates complete, actionable reports.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# LLM for intelligent content
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# LLM Visualizer for charts
try:
    from core.llm_visualizer import llm_visualize
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False


@dataclass
class ReportSection:
    """A section in the report"""
    title: str
    content: str
    section_type: str  # summary, insights, visualization, data_table, recommendations
    charts: List[Dict] = field(default_factory=list)
    data: Optional[Any] = None
    icon: str = "📄"


class ClaudeReportGenerator:
    """
    🎨 CLAUDE-STYLE INTELLIGENT REPORT GENERATOR
    
    Creates professional reports with:
    - LLM-generated insights tailored to the data
    - Real Plotly visualizations
    - Actionable recommendations
    - Beautiful HTML output
    """
    
    REPORTS_DIR = "storage/reports"
    MAX_ROWS_FOR_ANALYSIS = 1000  # Prevent slow processing
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.reports_dir = f"{self.REPORTS_DIR}/{user_id}"
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate(
        self,
        df: pd.DataFrame,
        report_type: str = "comprehensive",
        title: str = None,
        focus: str = None
    ) -> Dict[str, Any]:
        """
        Generate a Claude-style intelligent report.
        
        Args:
            df: User's DataFrame
            report_type: Type of report (comprehensive, executive, technical, trends)
            title: Optional custom title
            focus: Optional focus area (e.g., "sales performance", "anomalies")
            
        Returns:
            Report metadata with download URL and preview
        """
        if df is None or df.empty:
            return {"success": False, "error": "No data provided"}
        
        # Sample large datasets
        if len(df) > self.MAX_ROWS_FOR_ANALYSIS:
            logger.info(f"Sampling data from {len(df)} to {self.MAX_ROWS_FOR_ANALYSIS} rows")
            df = df.sample(n=self.MAX_ROWS_FOR_ANALYSIS, random_state=42)
        
        # Generate report title
        if not title:
            title = self._generate_title(df, report_type)
        
        # Build sections based on report type
        sections = self._build_sections(df, report_type, focus)
        
        # Generate HTML report
        result = self._generate_html_report(df, title, sections)
        
        return result
    
    def _generate_title(self, df: pd.DataFrame, report_type: str) -> str:
        """Generate intelligent title based on data."""
        if LLM_AVAILABLE:
            prompt = f"""Generate a professional report title for a {report_type} data analysis.
            
Data has {len(df)} rows with columns: {list(df.columns)[:10]}

Return ONLY the title, nothing else. Make it specific and professional."""
            try:
                title = llm_chat(prompt, temperature=0.5, max_tokens=50)
                return title.strip().replace('"', '')
            except:
                pass
        
        # Fallback
        return f"{report_type.title()} Data Analysis Report"
    
    def _build_sections(self, df: pd.DataFrame, report_type: str, focus: str) -> List[ReportSection]:
        """Build report sections with LLM-generated content."""
        sections = []
        
        # 1. Executive Summary (LLM-generated)
        sections.append(self._generate_executive_summary(df, focus))
        
        # 2. Key Metrics Dashboard
        sections.append(self._generate_metrics_section(df))
        
        # 3. Visualizations (Real Plotly charts)
        sections.append(self._generate_visualizations(df, focus))
        
        # 4. Data Quality Assessment
        sections.append(self._generate_quality_section(df))
        
        # 5. Trend Analysis (if applicable)
        if self._has_time_data(df):
            sections.append(self._generate_trends_section(df))
        
        # 6. AI Insights (LLM-generated)
        sections.append(self._generate_insights_section(df, focus))
        
        # 7. Recommendations (LLM-generated)
        sections.append(self._generate_recommendations_section(df, focus))
        
        return sections
    
    def _generate_executive_summary(self, df: pd.DataFrame, focus: str) -> ReportSection:
        """Generate LLM executive summary."""
        data_summary = self._get_data_summary(df)
        
        if LLM_AVAILABLE:
            prompt = f"""Write a professional executive summary for this data analysis report.

DATA OVERVIEW:
{data_summary}

{f'FOCUS AREA: {focus}' if focus else ''}

Write 3-4 paragraphs covering:
1. What this data represents
2. Key findings at a glance
3. Most important metrics
4. Overall data health

Be specific, use actual numbers from the data. Professional tone."""

            try:
                content = llm_chat(prompt, temperature=0.5, max_tokens=500)
            except:
                content = self._fallback_summary(df)
        else:
            content = self._fallback_summary(df)
        
        return ReportSection(
            title="Executive Summary",
            content=content,
            section_type="summary",
            icon="📋"
        )
    
    def _generate_metrics_section(self, df: pd.DataFrame) -> ReportSection:
        """Generate key metrics dashboard."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        metrics = []
        for col in numeric_cols[:6]:
            metrics.append({
                "name": col,
                "value": f"{df[col].mean():,.2f}",
                "min": f"{df[col].min():,.2f}",
                "max": f"{df[col].max():,.2f}",
                "trend": "↑" if df[col].iloc[-1] > df[col].iloc[0] else "↓" if len(df) > 1 else "→"
            })
        
        content = f"**{len(df):,} records** analyzed across **{len(df.columns)} variables**.\n\n"
        content += "### Key Metrics:\n"
        for m in metrics:
            content += f"- **{m['name']}**: {m['value']} (Range: {m['min']} - {m['max']}) {m['trend']}\n"
        
        return ReportSection(
            title="Key Metrics Dashboard",
            content=content,
            section_type="metrics",
            data=metrics,
            icon="📊"
        )
    
    def _generate_visualizations(self, df: pd.DataFrame, focus: str) -> ReportSection:
        """Generate real Plotly visualizations."""
        charts = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # 1. Bar chart - if we have categorical and numeric data
        if categorical_cols and numeric_cols:
            try:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                grouped = df.groupby(cat_col)[num_col].mean().nlargest(10)
                
                chart = {
                    "data": [{
                        "type": "bar",
                        "x": grouped.index.tolist(),
                        "y": [round(v, 2) for v in grouped.values.tolist()],
                        "marker": {"color": "#f97316"}
                    }],
                    "layout": {
                        "title": f"Average {num_col} by {cat_col}",
                        "template": "plotly_white",
                        "height": 350,
                        "margin": {"l": 50, "r": 30, "t": 50, "b": 80}
                    }
                }
                charts.append(chart)
            except:
                pass
        
        # 2. Pie chart - distribution
        if categorical_cols:
            try:
                cat_col = categorical_cols[0]
                dist = df[cat_col].value_counts().head(8)
                
                chart = {
                    "data": [{
                        "type": "pie",
                        "labels": dist.index.tolist(),
                        "values": dist.values.tolist(),
                        "marker": {"colors": ["#f97316", "#06b6d4", "#22c55e", "#8b5cf6", "#ec4899", "#eab308", "#ef4444", "#64748b"]}
                    }],
                    "layout": {
                        "title": f"Distribution of {cat_col}",
                        "template": "plotly_white",
                        "height": 350
                    }
                }
                charts.append(chart)
            except:
                pass
        
        # 3. Scatter plot - correlation
        if len(numeric_cols) >= 2:
            try:
                x_col, y_col = numeric_cols[0], numeric_cols[1]
                sample = df.sample(min(200, len(df)))
                
                chart = {
                    "data": [{
                        "type": "scatter",
                        "mode": "markers",
                        "x": sample[x_col].tolist(),
                        "y": sample[y_col].tolist(),
                        "marker": {"color": "#06b6d4", "size": 8, "opacity": 0.7}
                    }],
                    "layout": {
                        "title": f"{x_col} vs {y_col}",
                        "xaxis": {"title": x_col},
                        "yaxis": {"title": y_col},
                        "template": "plotly_white",
                        "height": 350
                    }
                }
                charts.append(chart)
            except:
                pass
        
        # 4. Line chart - if time data exists
        if self._has_time_data(df) and numeric_cols:
            try:
                time_col = self._get_time_column(df)
                num_col = numeric_cols[0]
                time_data = df.groupby(time_col)[num_col].mean().head(50)
                
                chart = {
                    "data": [{
                        "type": "scatter",
                        "mode": "lines+markers",
                        "x": [str(x) for x in time_data.index.tolist()],
                        "y": [round(v, 2) for v in time_data.values.tolist()],
                        "line": {"color": "#22c55e", "width": 2}
                    }],
                    "layout": {
                        "title": f"{num_col} Trend Over Time",
                        "template": "plotly_white",
                        "height": 350
                    }
                }
                charts.append(chart)
            except:
                pass
        
        content = f"Generated **{len(charts)} visualizations** based on your data characteristics."
        
        return ReportSection(
            title="Data Visualizations",
            content=content,
            section_type="visualization",
            charts=charts,
            icon="📈"
        )
    
    def _generate_quality_section(self, df: pd.DataFrame) -> ReportSection:
        """Generate data quality assessment."""
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100
        duplicates = df.duplicated().sum()
        
        quality_score = 100
        quality_score -= min(missing_pct * 2, 30)  # Up to -30 for missing
        quality_score -= min((duplicates / len(df)) * 100, 20)  # Up to -20 for duplicates
        
        issues = []
        if missing_pct > 5:
            issues.append(f"⚠️ {missing_pct:.1f}% missing values detected")
        if duplicates > 0:
            issues.append(f"⚠️ {duplicates:,} duplicate rows found")
        
        content = f"""### Data Quality Score: **{max(0, int(quality_score))}/100**

**Quality Metrics:**
- Total Records: {len(df):,}
- Total Fields: {len(df.columns)}
- Missing Values: {missing_cells:,} ({missing_pct:.1f}%)
- Duplicate Rows: {duplicates:,}

"""
        if issues:
            content += "**Issues Found:**\n" + "\n".join(f"- {i}" for i in issues)
        else:
            content += "✅ **No significant quality issues detected**"
        
        return ReportSection(
            title="Data Quality Assessment",
            content=content,
            section_type="quality",
            data={"score": int(quality_score), "issues": issues},
            icon="🔍"
        )
    
    def _generate_trends_section(self, df: pd.DataFrame) -> ReportSection:
        """Generate trends analysis section."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        trends = []
        for col in numeric_cols[:5]:
            try:
                first_half = df[col].iloc[:len(df)//2].mean()
                second_half = df[col].iloc[len(df)//2:].mean()
                change = ((second_half - first_half) / first_half) * 100 if first_half != 0 else 0
                direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                trends.append(f"- **{col}**: {direction} {abs(change):.1f}% {'increase' if change > 0 else 'decrease' if change < 0 else 'stable'}")
            except:
                pass
        
        content = "### Trend Analysis\n\n" + "\n".join(trends) if trends else "No significant trends detected."
        
        return ReportSection(
            title="Trend Analysis",
            content=content,
            section_type="trends",
            icon="📈"
        )
    
    def _generate_insights_section(self, df: pd.DataFrame, focus: str) -> ReportSection:
        """Generate LLM-powered insights."""
        data_summary = self._get_data_summary(df)
        
        if LLM_AVAILABLE:
            prompt = f"""Analyze this dataset and provide 5 key insights.

DATA:
{data_summary}

{f'Focus on: {focus}' if focus else ''}

Provide 5 specific, actionable insights based on actual values in the data.
Format each as a bullet point starting with an emoji.
Be specific with numbers and percentages."""

            try:
                content = llm_chat(prompt, temperature=0.5, max_tokens=400)
            except:
                content = self._fallback_insights(df)
        else:
            content = self._fallback_insights(df)
        
        return ReportSection(
            title="AI-Generated Insights",
            content=content,
            section_type="insights",
            icon="💡"
        )
    
    def _generate_recommendations_section(self, df: pd.DataFrame, focus: str) -> ReportSection:
        """Generate LLM-powered recommendations."""
        data_summary = self._get_data_summary(df)
        
        if LLM_AVAILABLE:
            prompt = f"""Based on this data analysis, provide actionable recommendations.

DATA SUMMARY:
{data_summary}

Provide 4-5 specific, actionable recommendations.
Consider data quality, patterns found, and potential improvements.
Format as numbered list. Be specific and practical."""

            try:
                content = llm_chat(prompt, temperature=0.5, max_tokens=400)
            except:
                content = self._fallback_recommendations(df)
        else:
            content = self._fallback_recommendations(df)
        
        return ReportSection(
            title="Recommendations",
            content=content,
            section_type="recommendations",
            icon="🎯"
        )
    
    def _generate_html_report(self, df: pd.DataFrame, title: str, sections: List[ReportSection]) -> Dict[str, Any]:
        """Generate beautiful HTML report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"claude_report_{timestamp}.html"
        filepath = os.path.join(self.reports_dir, filename)
        
        html = self._build_html(title, sections, timestamp)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return {
            "success": True,
            "format": "html",
            "filename": filename,
            "filepath": filepath,
            "download_url": f"/api/v1/reports/download/{self.user_id}/{filename}",
            "preview_url": f"/api/v1/reports/preview/{self.user_id}/{filename}",
            "title": title,
            "sections": len(sections),
            "generated_at": datetime.now().isoformat()
        }
    
    def _build_html(self, title: str, sections: List[ReportSection], timestamp: str) -> str:
        """Build the HTML content."""
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #1e293b;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            min-height: 100vh;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 50px 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(249,115,22,0.3) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .header h1 {{ 
            font-size: 2.2rem; 
            margin-bottom: 10px;
            position: relative;
        }}
        .header .meta {{ 
            opacity: 0.8; 
            font-size: 0.95rem;
            position: relative;
        }}
        .section {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            border: 1px solid rgba(0,0,0,0.05);
        }}
        .section h2 {{
            color: #0f172a;
            font-size: 1.4rem;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid #f97316;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section h2 .icon {{ font-size: 1.3rem; }}
        .content {{ 
            color: #475569;
            font-size: 1rem;
        }}
        .content p {{ margin-bottom: 12px; }}
        .content strong {{ color: #0f172a; }}
        .content h3 {{ color: #0f172a; margin: 20px 0 10px; font-size: 1.1rem; }}
        .content ul, .content ol {{ padding-left: 24px; margin: 12px 0; }}
        .content li {{ margin-bottom: 8px; }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 24px;
            margin: 20px 0;
        }}
        .chart-box {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #e2e8f0;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }}
        .metric-card .value {{ font-size: 1.8rem; font-weight: 700; }}
        .metric-card .label {{ font-size: 0.85rem; opacity: 0.9; margin-top: 4px; }}
        .quality-score {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #22c55e;
            color: white;
            padding: 8px 20px;
            border-radius: 30px;
            font-weight: 600;
            font-size: 1.1rem;
        }}
        .quality-score.warning {{ background: #eab308; }}
        .quality-score.danger {{ background: #ef4444; }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            font-size: 0.9rem;
        }}
        .actions {{
            display: flex;
            gap: 12px;
            justify-content: center;
            margin: 30px 0;
        }}
        .btn {{
            padding: 12px 28px;
            border-radius: 10px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            border: none;
            font-size: 0.95rem;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: #f97316;
            color: white;
        }}
        .btn-primary:hover {{ background: #ea580c; }}
        .btn-secondary {{
            background: #e2e8f0;
            color: #1e293b;
        }}
        .btn-secondary:hover {{ background: #cbd5e1; }}
        @media print {{
            .actions {{ display: none; }}
            body {{ background: white; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <p class="meta">
                Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | 
                Powered by AI Business Analyst
            </p>
        </div>
'''
        
        # Add sections
        chart_id = 0
        for section in sections:
            html += f'''
        <div class="section">
            <h2><span class="icon">{section.icon}</span> {section.title}</h2>
            <div class="content">
'''
            
            # Format content (markdown-like)
            content = section.content
            # Convert markdown to HTML
            content = content.replace('**', '<strong>').replace('**', '</strong>')
            content = content.replace('###', '<h3>').replace('\n\n', '</p><p>')
            content = content.replace('\n- ', '</li><li>').replace('\n• ', '</li><li>')
            if '<li>' in content:
                content = '<ul><li>' + content + '</li></ul>'
            content = f'<p>{content}</p>'
            html += content
            
            # Add charts if present
            if section.charts:
                html += '<div class="chart-grid">'
                for chart in section.charts:
                    chart_id += 1
                    html += f'''
                <div class="chart-box">
                    <div id="chart{chart_id}"></div>
                </div>
'''
                html += '</div>'
            
            html += '''
            </div>
        </div>
'''
        
        # Actions
        html += '''
        <div class="actions">
            <button class="btn btn-primary" onclick="window.print()">📄 Print / Save as PDF</button>
            <button class="btn btn-secondary" onclick="window.history.back()">← Back</button>
        </div>
        
        <div class="footer">
            <p>Generated by AI Business Analyst | Claude-Style Report Engine</p>
        </div>
    </div>
    
    <script>
'''
        
        # Add Plotly chart scripts
        chart_id = 0
        for section in sections:
            for chart in section.charts:
                chart_id += 1
                chart_json = json.dumps(chart, default=str)
                html += f'''
        var chartData{chart_id} = {chart_json};
        Plotly.newPlot('chart{chart_id}', chartData{chart_id}.data, chartData{chart_id}.layout, {{responsive: true}});
'''
        
        html += '''
    </script>
</body>
</html>'''
        
        return html
    
    # Helper methods
    def _get_data_summary(self, df: pd.DataFrame) -> str:
        """Get data summary for LLM."""
        summary = f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
        summary += f"Column names: {list(df.columns)}\n\n"
        
        numeric = df.select_dtypes(include=[np.number])
        for col in numeric.columns[:5]:
            summary += f"{col}: mean={df[col].mean():.2f}, min={df[col].min():.2f}, max={df[col].max():.2f}\n"
        
        categorical = df.select_dtypes(include=['object'])
        for col in categorical.columns[:3]:
            top = df[col].value_counts().head(3)
            summary += f"{col}: {dict(top)}\n"
        
        return summary
    
    def _has_time_data(self, df: pd.DataFrame) -> bool:
        """Check if data has time/date column."""
        time_keywords = ['date', 'time', 'day', 'month', 'year', 'timestamp']
        return any(kw in col.lower() for col in df.columns for kw in time_keywords)
    
    def _get_time_column(self, df: pd.DataFrame) -> str:
        """Get the time column name."""
        time_keywords = ['date', 'time', 'day', 'month', 'year', 'timestamp']
        for col in df.columns:
            if any(kw in col.lower() for kw in time_keywords):
                return col
        return df.columns[0]
    
    def _fallback_summary(self, df: pd.DataFrame) -> str:
        return f"""This report analyzes **{len(df):,} records** across **{len(df.columns)} variables**.

The dataset contains {len(df.select_dtypes(include=[np.number]).columns)} numeric columns and {len(df.select_dtypes(include=['object']).columns)} categorical columns.

Key data points have been analyzed to provide insights and recommendations."""
    
    def _fallback_insights(self, df: pd.DataFrame) -> str:
        insights = []
        numeric = df.select_dtypes(include=[np.number])
        if not numeric.empty:
            col = numeric.columns[0]
            insights.append(f"📊 The average {col} is {df[col].mean():,.2f}")
            insights.append(f"📈 Maximum {col} reached {df[col].max():,.2f}")
        insights.append(f"📋 Dataset contains {len(df):,} records")
        return "\n".join(insights)
    
    def _fallback_recommendations(self, df: pd.DataFrame) -> str:
        return """1. **Monitor key metrics** - Set up dashboards for ongoing tracking
2. **Address data quality** - Fix missing values and duplicates
3. **Explore correlations** - Analyze relationships between variables
4. **Automate reporting** - Schedule regular report generation"""


def generate_claude_report(df: pd.DataFrame, user_id: str = "default", **kwargs) -> Dict[str, Any]:
    """Quick function to generate Claude-style report."""
    generator = ClaudeReportGenerator(user_id)
    return generator.generate(df, **kwargs)


__all__ = ['ClaudeReportGenerator', 'generate_claude_report']
