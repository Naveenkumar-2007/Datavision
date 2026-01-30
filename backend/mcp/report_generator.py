# Report Generator MCP - Downloadable Reports
"""
📄 REPORT GENERATOR MCP
========================

Generate professional downloadable reports like ChatGPT's Canvas.

Features:
- 📊 PDF Reports with charts and data
- 📝 Word Documents (DOCX)
- 📈 Excel Workbooks with formatted data
- 🌐 HTML Reports (interactive)
- 📧 Email-ready summaries
- 🎨 Professional styling

Usage:
    from mcp.report_generator import ReportGenerator
    generator = ReportGenerator()
    report_path = generator.generate_pdf(df, title="Sales Report")

Author: AI Business Analyst Team
Version: 1.0.0
"""

import os
import io
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats"""
    PDF = "pdf"
    WORD = "docx"
    EXCEL = "xlsx"
    HTML = "html"
    MARKDOWN = "md"
    JSON = "json"
    CSV = "csv"


@dataclass
class ReportSection:
    """A section in the report"""
    title: str
    content: str
    section_type: str  # text, table, chart, summary
    data: Optional[Any] = None


@dataclass
class ReportMetadata:
    """Metadata for the report"""
    title: str
    subtitle: Optional[str] = None
    author: str = "AI Business Analyst"
    created_at: datetime = None
    description: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []


class ReportGenerator:
    """
    📄 Professional Report Generator
    
    Creates downloadable reports in multiple formats:
    - PDF with charts and tables
    - Word documents
    - Excel workbooks
    - HTML for web viewing
    """
    
    # Report storage directory
    REPORTS_DIR = "storage/reports"
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.reports_dir = f"{self.REPORTS_DIR}/{user_id}"
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Color scheme
        self.colors = {
            'primary': '#f97316',
            'secondary': '#06b6d4',
            'success': '#22c55e',
            'warning': '#eab308',
            'danger': '#ef4444',
            'dark': '#1e293b',
            'light': '#f8fafc'
        }
    
    def generate(
        self,
        df: pd.DataFrame,
        query: str,
        title: str = None,
        format: ReportFormat = ReportFormat.HTML,
        include_charts: bool = True,
        include_summary: bool = True,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a downloadable report from data.
        
        Args:
            df: DataFrame with data
            query: User's original query
            title: Report title
            format: Output format (pdf, excel, html, etc.)
            include_charts: Whether to include visualizations
            include_summary: Whether to include executive summary
            include_recommendations: Whether to include AI recommendations
            
        Returns:
            Dict with report path and metadata
        """
        if df is None or df.empty:
            return {"success": False, "error": "No data provided"}
        
        # Generate title from query if not provided
        if not title:
            title = self._generate_title(query, df)
        
        # Create metadata
        metadata = ReportMetadata(
            title=title,
            subtitle=query[:100] if query else None,
            description=f"Generated from {len(df)} rows, {len(df.columns)} columns"
        )
        
        # Build report sections
        sections = self._build_sections(df, query, include_charts, include_summary, include_recommendations)
        
        # Generate in requested format
        generators = {
            ReportFormat.HTML: self._generate_html,
            ReportFormat.PDF: self._generate_pdf,
            ReportFormat.EXCEL: self._generate_excel,
            ReportFormat.WORD: self._generate_word,
            ReportFormat.MARKDOWN: self._generate_markdown,
            ReportFormat.JSON: self._generate_json,
            ReportFormat.CSV: self._generate_csv
        }
        
        generator = generators.get(format, self._generate_html)
        result = generator(df, metadata, sections)
        
        return result
    
    def _generate_title(self, query: str, df: pd.DataFrame) -> str:
        """Generate report title from query."""
        if query:
            # Extract key terms
            words = query.split()[:5]
            return " ".join(w.capitalize() for w in words) + " Analysis"
        return f"Data Report ({len(df)} records)"
    
    def _build_sections(
        self,
        df: pd.DataFrame,
        query: str,
        include_charts: bool,
        include_summary: bool,
        include_recommendations: bool
    ) -> List[ReportSection]:
        """Build report sections."""
        sections = []
        
        # 1. Executive Summary
        if include_summary:
            summary = self._generate_executive_summary(df, query)
            sections.append(ReportSection(
                title="Executive Summary",
                content=summary,
                section_type="summary"
            ))
        
        # 2. Data Overview
        overview = self._generate_data_overview(df)
        sections.append(ReportSection(
            title="Data Overview",
            content=overview,
            section_type="text"
        ))
        
        # 3. Key Statistics
        stats = self._generate_statistics_section(df)
        sections.append(ReportSection(
            title="Key Statistics",
            content=stats["text"],
            section_type="table",
            data=stats["table"]
        ))
        
        # 4. Charts/Visualizations
        if include_charts:
            chart_section = self._generate_chart_section(df)
            sections.append(ReportSection(
                title="Visualizations",
                content=chart_section["description"],
                section_type="chart",
                data=chart_section["charts"]
            ))
        
        # 5. Detailed Data Table
        sections.append(ReportSection(
            title="Data Table",
            content=f"First {min(100, len(df))} records of the dataset",
            section_type="table",
            data=df.head(100).to_dict('records')
        ))
        
        # 6. Recommendations
        if include_recommendations:
            recommendations = self._generate_recommendations(df, query)
            sections.append(ReportSection(
                title="AI Recommendations",
                content=recommendations,
                section_type="text"
            ))
        
        return sections
    
    def _generate_executive_summary(self, df: pd.DataFrame, query: str) -> str:
        """Generate executive summary."""
        num_rows = len(df)
        num_cols = len(df.columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        summary = f"""This report provides an analysis of {num_rows:,} records across {num_cols} variables.

**Key Highlights:**
"""
        # Add highlights for numeric columns
        for col in numeric_cols[:3]:
            try:
                mean_val = df[col].mean()
                max_val = df[col].max()
                min_val = df[col].min()
                summary += f"\n• **{col}**: Average {mean_val:,.2f} (Range: {min_val:,.2f} - {max_val:,.2f})"
            except:
                pass
        
        # Add category insights
        cat_cols = df.select_dtypes(include=['object']).columns[:2]
        for col in cat_cols:
            try:
                top_val = df[col].value_counts().index[0]
                top_count = df[col].value_counts().values[0]
                summary += f"\n• **{col}**: Most common value is '{top_val}' ({top_count:,} records)"
            except:
                pass
        
        return summary
    
    def _generate_data_overview(self, df: pd.DataFrame) -> str:
        """Generate data overview section."""
        overview = f"""**Dataset Statistics:**
- Total Records: {len(df):,}
- Total Columns: {len(df.columns)}
- Numeric Columns: {len(df.select_dtypes(include=[np.number]).columns)}
- Text Columns: {len(df.select_dtypes(include=['object']).columns)}
- Missing Values: {df.isna().sum().sum():,} ({df.isna().sum().sum() / df.size * 100:.1f}%)

**Columns:** {', '.join(df.columns[:15])}{'...' if len(df.columns) > 15 else ''}
"""
        return overview
    
    def _generate_statistics_section(self, df: pd.DataFrame) -> Dict:
        """Generate statistics section."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns[:10]
        
        stats_data = []
        for col in numeric_cols:
            try:
                stats_data.append({
                    "Column": col,
                    "Mean": f"{df[col].mean():,.2f}",
                    "Median": f"{df[col].median():,.2f}",
                    "Std Dev": f"{df[col].std():,.2f}",
                    "Min": f"{df[col].min():,.2f}",
                    "Max": f"{df[col].max():,.2f}"
                })
            except:
                pass
        
        return {
            "text": f"Statistical summary for {len(numeric_cols)} numeric columns:",
            "table": stats_data
        }
    
    def _generate_chart_section(self, df: pd.DataFrame) -> Dict:
        """Generate chart configurations for the report."""
        charts = []
        
        # Bar chart for categorical data
        cat_cols = df.select_dtypes(include=['object']).columns[:1]
        num_cols = df.select_dtypes(include=[np.number]).columns[:1]
        
        if len(cat_cols) > 0 and len(num_cols) > 0:
            cat_col, num_col = cat_cols[0], num_cols[0]
            grouped = df.groupby(cat_col)[num_col].sum().nlargest(10)
            
            charts.append({
                "type": "bar",
                "title": f"{num_col} by {cat_col}",
                "labels": grouped.index.tolist(),
                "values": grouped.values.tolist()
            })
        
        # Line chart for time series (if date column exists)
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
        if date_cols and len(num_cols) > 0:
            try:
                chart_data = df.groupby(date_cols[0])[num_cols[0]].mean().head(50)
                charts.append({
                    "type": "line",
                    "title": f"{num_cols[0]} Over Time",
                    "labels": chart_data.index.astype(str).tolist(),
                    "values": chart_data.values.tolist()
                })
            except:
                pass
        
        # Pie chart for distribution
        if len(cat_cols) > 0:
            dist = df[cat_cols[0]].value_counts().head(8)
            charts.append({
                "type": "pie",
                "title": f"Distribution of {cat_cols[0]}",
                "labels": dist.index.tolist(),
                "values": dist.values.tolist()
            })
        
        return {
            "description": f"Generated {len(charts)} visualizations based on data analysis.",
            "charts": charts
        }
    
    def _generate_recommendations(self, df: pd.DataFrame, query: str) -> str:
        """Generate AI recommendations."""
        recommendations = "**Based on the data analysis, here are our recommendations:**\n\n"
        
        # Check for missing data
        missing_pct = df.isna().sum().sum() / df.size * 100
        if missing_pct > 10:
            recommendations += f"1. **Data Quality**: {missing_pct:.1f}% of values are missing. Consider data cleaning before analysis.\n\n"
        
        # Check for outliers in numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_cols = []
        for col in numeric_cols[:5]:
            try:
                q1, q3 = df[col].quantile([0.25, 0.75])
                iqr = q3 - q1
                outliers = ((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum()
                if outliers > len(df) * 0.05:
                    outlier_cols.append(col)
            except:
                pass
        
        if outlier_cols:
            recommendations += f"2. **Outliers Detected**: Columns {', '.join(outlier_cols)} contain significant outliers. Review for data errors.\n\n"
        
        # Check for high cardinality categoricals
        for col in df.select_dtypes(include=['object']).columns[:5]:
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio > 0.5:
                recommendations += f"3. **High Cardinality**: Column '{col}' has many unique values ({df[col].nunique():,}). Consider grouping or encoding.\n\n"
                break
        
        # General recommendations
        recommendations += f"4. **Next Steps**: Consider creating a dashboard for ongoing monitoring of key metrics.\n\n"
        recommendations += f"5. **Further Analysis**: Explore correlations between numeric variables for deeper insights.\n"
        
        return recommendations
    
    # ==========================================================================
    # FORMAT-SPECIFIC GENERATORS
    # ==========================================================================
    
    def _generate_html(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        sections: List[ReportSection]
    ) -> Dict[str, Any]:
        """Generate HTML report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.html"
        filepath = os.path.join(self.reports_dir, filename)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background: #f8fafc;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
        .header {{
            background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']});
            color: white;
            padding: 60px 40px;
            border-radius: 16px;
            margin-bottom: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 0.95rem; }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .section h2 {{
            color: {self.colors['primary']};
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid {self.colors['primary']}20;
        }}
        .section p {{ margin-bottom: 15px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: {self.colors['primary']}10;
            color: {self.colors['primary']};
            font-weight: 600;
        }}
        tr:hover {{ background: #f8fafc; }}
        .chart-container {{
            margin: 30px 0;
            height: 300px;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; }}
        .download-btn {{
            display: inline-block;
            background: {self.colors['primary']};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 20px;
        }}
        .download-btn:hover {{ opacity: 0.9; }}
        .footer {{
            text-align: center;
            padding: 40px;
            color: #64748b;
            font-size: 0.9rem;
        }}
        @media print {{
            .download-btn {{ display: none; }}
            body {{ background: white; }}
            .section {{ box-shadow: none; border: 1px solid #e2e8f0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {metadata.title}</h1>
            <p class="meta">
                {metadata.subtitle if metadata.subtitle else ''}<br>
                Generated: {metadata.created_at.strftime('%Y-%m-%d %H:%M')} | 
                Author: {metadata.author}
            </p>
        </div>
"""
        
        # Add sections
        chart_id = 0
        for section in sections:
            html += f"""
        <div class="section">
            <h2>{section.title}</h2>
"""
            
            if section.section_type == "text" or section.section_type == "summary":
                # Convert markdown-like formatting to HTML
                content = section.content.replace('\n', '<br>')
                content = content.replace('**', '<strong>').replace('**', '</strong>')
                html += f"            <p>{content}</p>"
            
            elif section.section_type == "table" and section.data:
                if isinstance(section.data, list) and len(section.data) > 0:
                    html += "            <table>"
                    # Headers
                    headers = section.data[0].keys()
                    html += "                <tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
                    # Rows (limit to 50)
                    for row in section.data[:50]:
                        html += "<tr>" + "".join(f"<td>{v}</td>" for v in row.values()) + "</tr>"
                    html += "            </table>"
                    if len(section.data) > 50:
                        html += f"<p><em>Showing 50 of {len(section.data)} records</em></p>"
                else:
                    html += f"            <p>{section.content}</p>"
            
            elif section.section_type == "chart" and section.data:
                html += '            <div class="grid">'
                for chart in section.data[:4]:  # Limit to 4 charts
                    chart_id += 1
                    html += f'''
                <div class="chart-container">
                    <canvas id="chart{chart_id}"></canvas>
                </div>
'''
                html += '            </div>'
            
            html += """
        </div>
"""
        
        # Add chart scripts
        html += """
        <div class="section" style="text-align: center;">
            <button class="download-btn" onclick="window.print()">📄 Print / Save as PDF</button>
            <a href="#" class="download-btn" onclick="downloadCSV()">📊 Download Data (CSV)</a>
        </div>
        
        <div class="footer">
            <p>Generated by AI Business Analyst | Report ID: """ + timestamp + """</p>
        </div>
    </div>
    
    <script>
"""
        
        # Add chart initialization scripts
        chart_id = 0
        for section in sections:
            if section.section_type == "chart" and section.data:
                for chart in section.data[:4]:
                    chart_id += 1
                    chart_type = chart.get('type', 'bar')
                    labels = json.dumps(chart.get('labels', []))
                    values = json.dumps(chart.get('values', []))
                    title = chart.get('title', 'Chart')
                    
                    html += f"""
        new Chart(document.getElementById('chart{chart_id}'), {{
            type: '{chart_type}',
            data: {{
                labels: {labels},
                datasets: [{{
                    label: '{title}',
                    data: {values},
                    backgroundColor: '{self.colors["primary"]}',
                    borderColor: '{self.colors["primary"]}',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ title: {{ display: true, text: '{title}' }} }}
            }}
        }});
"""
        
        # CSV download function
        csv_data = df.head(1000).to_csv(index=False).replace('"', '\\"').replace('\n', '\\n')
        html += f"""
        function downloadCSV() {{
            const csv = "{csv_data}";
            const blob = new Blob([csv], {{ type: 'text/csv' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'data_export.csv';
            a.click();
        }}
    </script>
</body>
</html>
"""
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return {
            "success": True,
            "format": "html",
            "filename": filename,
            "filepath": filepath,
            "download_url": f"/api/v1/reports/download/{self.user_id}/{filename}",
            "preview_url": f"/api/v1/reports/preview/{self.user_id}/{filename}",
            "metadata": {
                "title": metadata.title,
                "created_at": metadata.created_at.isoformat(),
                "sections": len(sections)
            }
        }
    
    def _generate_excel(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        sections: List[ReportSection]
    ) -> Dict[str, Any]:
        """Generate Excel report with multiple sheets."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Sheet 1: Summary
                summary_data = {
                    "Metric": ["Total Rows", "Total Columns", "Missing Values", "Generated At"],
                    "Value": [len(df), len(df.columns), df.isna().sum().sum(), datetime.now().strftime('%Y-%m-%d %H:%M')]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Sheet 2: Statistics
                numeric_df = df.describe().T
                if not numeric_df.empty:
                    numeric_df.to_excel(writer, sheet_name='Statistics')
                
                # Sheet 3: Full Data
                df.head(10000).to_excel(writer, sheet_name='Data', index=False)
                
                # Sheet 4: Value Counts for categorical columns
                cat_cols = df.select_dtypes(include=['object']).columns[:5]
                if len(cat_cols) > 0:
                    for col in cat_cols:
                        counts = df[col].value_counts().head(50).reset_index()
                        counts.columns = [col, 'Count']
                        counts.to_excel(writer, sheet_name=f'{col[:25]}_dist', index=False)
            
            return {
                "success": True,
                "format": "excel",
                "filename": filename,
                "filepath": filepath,
                "download_url": f"/api/v1/reports/download/{self.user_id}/{filename}",
                "metadata": {"title": metadata.title, "sheets": 4}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_pdf(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        sections: List[ReportSection]
    ) -> Dict[str, Any]:
        """Generate PDF report (via HTML print)."""
        # Generate HTML first, then suggest print-to-PDF
        result = self._generate_html(df, metadata, sections)
        result["format"] = "pdf"
        result["note"] = "Open preview URL and use Print to save as PDF"
        return result
    
    def _generate_word(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        sections: List[ReportSection]
    ) -> Dict[str, Any]:
        """Generate Word document."""
        # Generate markdown that can be converted/copied
        result = self._generate_markdown(df, metadata, sections)
        result["format"] = "docx"
        result["note"] = "Download markdown and import to Word, or copy HTML content"
        return result
    
    def _generate_markdown(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        sections: List[ReportSection]
    ) -> Dict[str, Any]:
        """Generate Markdown report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.md"
        filepath = os.path.join(self.reports_dir, filename)
        
        md = f"""# {metadata.title}

**Generated:** {metadata.created_at.strftime('%Y-%m-%d %H:%M')}  
**Author:** {metadata.author}

---

"""
        
        for section in sections:
            md += f"## {section.title}\n\n"
            md += f"{section.content}\n\n"
            
            if section.section_type == "table" and section.data:
                if isinstance(section.data, list) and len(section.data) > 0:
                    headers = list(section.data[0].keys())
                    md += "| " + " | ".join(headers) + " |\n"
                    md += "| " + " | ".join(['---'] * len(headers)) + " |\n"
                    for row in section.data[:20]:
                        md += "| " + " | ".join(str(v) for v in row.values()) + " |\n"
                    md += "\n"
            
            md += "---\n\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)
        
        return {
            "success": True,
            "format": "markdown",
            "filename": filename,
            "filepath": filepath,
            "content": md,
            "download_url": f"/api/v1/reports/download/{self.user_id}/{filename}"
        }
    
    def _generate_json(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        sections: List[ReportSection]
    ) -> Dict[str, Any]:
        """Generate JSON report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        report = {
            "metadata": {
                "title": metadata.title,
                "subtitle": metadata.subtitle,
                "author": metadata.author,
                "created_at": metadata.created_at.isoformat(),
                "description": metadata.description
            },
            "summary": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()
            },
            "statistics": df.describe().to_dict(),
            "data": df.head(1000).to_dict(orient='records')
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        return {
            "success": True,
            "format": "json",
            "filename": filename,
            "filepath": filepath,
            "download_url": f"/api/v1/reports/download/{self.user_id}/{filename}"
        }
    
    def _generate_csv(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        sections: List[ReportSection]
    ) -> Dict[str, Any]:
        """Generate CSV export."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_export_{timestamp}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        
        df.to_csv(filepath, index=False)
        
        return {
            "success": True,
            "format": "csv",
            "filename": filename,
            "filepath": filepath,
            "rows": len(df),
            "download_url": f"/api/v1/reports/download/{self.user_id}/{filename}"
        }
    
    def list_reports(self) -> List[Dict]:
        """List all reports for this user."""
        reports = []
        
        if os.path.exists(self.reports_dir):
            for filename in os.listdir(self.reports_dir):
                filepath = os.path.join(self.reports_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    reports.append({
                        "filename": filename,
                        "format": filename.split('.')[-1],
                        "size_kb": round(stat.st_size / 1024, 2),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "download_url": f"/api/v1/reports/download/{self.user_id}/{filename}"
                    })
        
        return sorted(reports, key=lambda x: x['created_at'], reverse=True)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_report(
    df: pd.DataFrame,
    query: str = "",
    format: str = "html",
    user_id: str = "default"
) -> Dict[str, Any]:
    """Quick function to generate a report."""
    generator = ReportGenerator(user_id)
    report_format = ReportFormat(format) if format in [f.value for f in ReportFormat] else ReportFormat.HTML
    return generator.generate(df, query, format=report_format)


def generate_excel_report(df: pd.DataFrame, user_id: str = "default") -> Dict[str, Any]:
    """Generate Excel report."""
    generator = ReportGenerator(user_id)
    return generator.generate(df, "", format=ReportFormat.EXCEL)


def generate_pdf_report(df: pd.DataFrame, query: str = "", user_id: str = "default") -> Dict[str, Any]:
    """Generate PDF-ready HTML report."""
    generator = ReportGenerator(user_id)
    return generator.generate(df, query, format=ReportFormat.PDF)


def list_user_reports(user_id: str = "default") -> List[Dict]:
    """List all reports for a user."""
    generator = ReportGenerator(user_id)
    return generator.list_reports()


# Quick test
if __name__ == "__main__":
    # Test data
    test_df = pd.DataFrame({
        'category': ['Electronics', 'Clothing', 'Food', 'Electronics', 'Clothing'] * 20,
        'date': pd.date_range('2024-01-01', periods=100),
        'sales': np.random.randint(100, 1000, 100),
        'quantity': np.random.randint(1, 50, 100)
    })
    
    # Generate HTML report
    result = generate_report(test_df, "Analyze sales by category", format="html")
    print(f"Report generated: {result.get('filename')}")
    print(f"Download URL: {result.get('download_url')}")
