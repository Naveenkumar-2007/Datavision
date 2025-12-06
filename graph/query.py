# Graph query module
import networkx as nx
import pandas as pd
from pathlib import Path
from config.settings import Settings
from core.llm import chat


def load_graph(company_id: str):
    """Load company's knowledge graph from user-specific directory"""
    import pickle
    
    # First try user-specific graph directory
    user_graph_dir = Settings.STORAGE / "users" / company_id / "graph"
    user_path = user_graph_dir / f"{company_id}.gpickle"
    
    if user_path.exists():
        print(f"📂 Loading graph from: {user_path}")
        with open(user_path, 'rb') as f:
            return pickle.load(f)
    
    # Fallback to global graph directory
    path = Settings.GRAPH_DIR / f"{company_id}.gpickle"
    if path.exists():
        print(f"📂 Loading graph from: {path}")
        with open(path, 'rb') as f:
            return pickle.load(f)
    
    # Try old format
    old_path = Settings.GRAPH_DIR / f"{company_id}.pkl"
    if old_path.exists():
        print(f"📂 Loading graph from: {old_path}")
        with open(old_path, 'rb') as f:
            return pickle.load(f)
    
    print(f"⚠️ No graph found for {company_id}")
    return None


def graph_snapshot(company_id: str, max_nodes: int = None) -> str:
    """
    Generate a text representation of the graph for LLM context
    """
    G = load_graph(company_id)
    if not G:
        return "No graph data available."

    max_nodes = max_nodes or Settings.GRAPH_MAX_NODES
    
    # Get sample of nodes
    nodes = list(G.nodes(data=True))[:max_nodes]
    edges = list(G.edges(data=True))[:max_nodes]

    snapshot = f"Knowledge Graph Summary ({len(G.nodes())} total nodes, {len(G.edges())} edges):\n\n"
    
    # Group nodes by type
    node_types = {}
    for node, data in nodes:
        node_type = data.get("type", "unknown")
        if node_type not in node_types:
            node_types[node_type] = []
        node_types[node_type].append(f"{node} ({data.get('label', 'N/A')})")
    
    for ntype, items in node_types.items():
        snapshot += f"\n{ntype.upper()}S ({len(items)}):\n"
        snapshot += ", ".join(items[:20]) + "\n"
    
    # Sample relationships
    snapshot += f"\nRELATIONSHIPS (sample of {len(edges)}):\n"
    for src, dst, data in edges[:20]:
        rel = data.get("relation", "related_to")
        snapshot += f"- {src} --[{rel}]--> {dst}\n"

    return snapshot


def revenue_dataframe(company_id: str) -> pd.DataFrame:
    """
    Extract revenue/invoice data from graph as DataFrame
    """
    G = load_graph(company_id)
    if not G:
        return pd.DataFrame()

    rows = []
    for node, data in G.nodes(data=True):
        if data.get("type") == "invoice" or data.get("kind") == "invoice":
            invoice_id = node
            customer = None
            product = None
            date = None
            amount = 0.0

            # Find connected nodes
            for neighbor in G.neighbors(node):
                neighbor_data = G.nodes[neighbor]
                ntype = neighbor_data.get("type") or neighbor_data.get("kind")
                
                if ntype == "customer" or neighbor.startswith("customer:"):
                    customer = neighbor_data.get("label", neighbor.replace("customer:", ""))
                elif ntype == "product" or neighbor.startswith("product:"):
                    product = neighbor_data.get("label", neighbor.replace("product:", ""))
                elif ntype == "date" or neighbor.startswith("date:"):
                    date = neighbor_data.get("label", neighbor.replace("date:", ""))
            
            # Get amount from invoice node itself
            amount = data.get("amount", 0.0)
            
            if customer and product and date:
                rows.append({
                    "invoice": invoice_id,
                    "customer": customer,
                    "product": product,
                    "date": date,
                    "amount": float(amount) if amount else 0.0
                })

    return pd.DataFrame(rows)


def query_graph(company_id: str, question: str) -> str:
    """
    🟧 GraphRAG: Advanced knowledge graph analysis
    Provides pattern detection, trend analysis, and relationship insights
    """
    print(f"🟧 query_graph called: company_id={company_id}, question={question[:50]}...")
    
    G = load_graph(company_id)
    print(f"🟧 Graph loaded: G={G}, nodes={G.number_of_nodes() if G else 0}")
    
    if not G or G.number_of_nodes() == 0:
        print(f"⚠️ No graph available for {company_id}")
        return """**No Knowledge Graph Available**

To enable GraphRAG analysis:
1. Upload business files (CSV, Excel, PDF) in Data Hub
2. Files are automatically processed into knowledge graph
3. Graph connects: Customers ↔ Products ↔ Invoices ↔ Dates

GraphRAG excels at:
• **Trend Analysis** - "Why did revenue drop?"
• **Pattern Detection** - "What patterns do you see?"
• **Correlation Discovery** - "Which customers buy premium products?"
• **Seasonal Insights** - "What are the seasonal trends?"

Upload files to unlock GraphRAG insights!"""
    
    # Get rich context from graph
    snapshot = graph_snapshot(company_id, max_nodes=100)
    
    # Extract revenue insights
    df = revenue_dataframe(company_id)
    revenue_insights = ""
    
    if df is not None and not df.empty:
        amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
        
        try:
            # Calculate key metrics
            total_revenue = df[amount_col].sum()
            avg_order = df[amount_col].mean()
            num_customers = df['customer'].nunique() if 'customer' in df.columns else 0
            num_products = df['product'].nunique() if 'product' in df.columns else 0
            
            revenue_insights = f"""
**Revenue Data Summary:**
• Total Revenue: ${total_revenue:,.2f}
• Average Order Value: ${avg_order:,.2f}
• Unique Customers: {num_customers}
• Product Variety: {num_products}
• Total Transactions: {len(df)}

"""
            
            # Time-based trends
            if 'date' in df.columns:
                df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
                df_dated = df[df['date_parsed'].notna()].copy()
                
                if not df_dated.empty:
                    df_dated['month'] = df_dated['date_parsed'].dt.to_period('M')
                    monthly_revenue = df_dated.groupby('month')[amount_col].sum()
                    
                    if len(monthly_revenue) >= 2:
                        latest_month_revenue = monthly_revenue.iloc[-1]
                        prev_month_revenue = monthly_revenue.iloc[-2]
                        change_pct = ((latest_month_revenue - prev_month_revenue) / prev_month_revenue * 100)
                        
                        trend = "📈 INCREASE" if change_pct > 0 else "📉 DECREASE"
                        revenue_insights += f"""**Monthly Trend Analysis:**
• Latest Month: ${latest_month_revenue:,.2f}
• Previous Month: ${prev_month_revenue:,.2f}
• Change: {change_pct:+.1f}% {trend}

"""
            
            # Top performers
            if 'customer' in df.columns:
                top_customer_rev = df.groupby('customer')[amount_col].sum().sort_values(ascending=False).head(3)
                revenue_insights += "**Top 3 Customers:**\n"
                for i, (cust, rev) in enumerate(top_customer_rev.items(), 1):
                    revenue_insights += f"  {i}. {cust}: ${rev:,.2f}\n"
                revenue_insights += "\n"
            
            if 'product' in df.columns:
                top_product_rev = df.groupby('product')[amount_col].sum().sort_values(ascending=False).head(3)
                revenue_insights += "**Top 3 Products:**\n"
                for i, (prod, rev) in enumerate(top_product_rev.items(), 1):
                    revenue_insights += f"  {i}. {prod}: ${rev:,.2f}\n"
                revenue_insights += "\n"
                
        except Exception as e:
            print(f"Revenue insights error: {e}")
    
    # Graph structure insights
    graph_structure = f"""
**Knowledge Graph Structure:**
• Total Entities: {G.number_of_nodes():,} nodes
• Relationships: {G.number_of_edges():,} connections
• Average Connections: {G.number_of_edges() / G.number_of_nodes():.1f} per entity
"""
    
    # Enterprise-grade system prompt for $50k product
    system_prompt = """You are an elite business intelligence analyst from a $50,000 enterprise AI product.

**Your Expertise:**
- Pattern Recognition: Identify trends, correlations, anomalies
- Causal Analysis: Explain WHY things happened (not just WHAT)
- Predictive Insights: Forecast future trends from historical patterns
- Actionable Recommendations: Provide strategic business advice

**Output Format:**
Use professional markdown formatting:
📊 **Key Findings**
📈 **Trend Analysis** 
🔍 **Deep Insights**
💡 **Business Recommendations**

**Requirements:**
- Be specific with numbers and percentages
- Explain causation, not just correlation
- Reference actual data points from the graph
- Provide clear, actionable insights
- Use business terminology (not technical jargon)"""
    
    prompt = f"""{graph_structure}

{revenue_insights}

{snapshot}

**Business Question:** {question}

**Your Task:** Analyze the knowledge graph and revenue data to provide comprehensive business intelligence. Focus on:
1. **Pattern Detection** - What trends emerge from the data?
2. **Causal Analysis** - WHY are these patterns occurring?
3. **Correlations** - How do customers, products, and time periods relate?
4. **Strategic Insights** - What should leadership know?

Provide a professional, data-driven analysis worthy of a $50,000 enterprise product."""

    print(f"🟧 Calling LLM with prompt length: {len(prompt)}")
    print(f"🟧 System prompt length: {len(system_prompt)}")
    print(f"🟧 Revenue insights included: {len(revenue_insights)} chars")
    print(f"🟧 Graph snapshot included: {len(snapshot)} chars")
    
    try:
        result = chat(prompt, system=system_prompt, max_tokens=2000)
        print(f"🟧 LLM returned result: type={type(result)}, length={len(result) if result else 0}")
        print(f"🟧 Result preview: {result[:100] if result else 'NONE'}")
        
        if not result or not isinstance(result, str) or result.strip() == "":
            print("⚠️ chat() returned empty/invalid result, using fallback")
            result = f"""**Knowledge Graph Analysis**

Based on the knowledge graph with {G.number_of_nodes()} entities and {G.number_of_edges()} relationships:

{revenue_insights if revenue_insights else 'No revenue data available yet.'}

**Graph Structure:**
The knowledge graph contains connections between customers, products, and transactions. Upload more business files to enable deeper pattern analysis."""
        
        return result
        
    except Exception as e:
        print(f"❌ Error calling chat(): {e}")
        import traceback
        traceback.print_exc()
        return f"Error analyzing graph: {str(e)}"


def get_graph_stats(company_id: str) -> dict:
    """
    Get graph statistics for dashboard
    """
    G = load_graph(company_id)
    if not G:
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "customers": 0,
            "products": 0,
            "invoices": 0
        }
    
    stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "customers": 0,
        "products": 0,
        "invoices": 0
    }
    
    for node, data in G.nodes(data=True):
        ntype = data.get("type") or data.get("kind", "")
        if ntype == "customer" or node.startswith("customer:"):
            stats["customers"] += 1
        elif ntype == "product" or node.startswith("product:"):
            stats["products"] += 1
        elif ntype == "invoice" or node.startswith("invoice:"):
            stats["invoices"] += 1
    
    return stats


def get_graph_analysis(company_id: str, question: str) -> str:
    """
    🟧 Clean graph-based analysis for Graph Mode
    Returns structured analysis directly from knowledge graph data
    """
    G = load_graph(company_id)
    if not G or G.number_of_nodes() == 0:
        return None
    
    df = revenue_dataframe(company_id)
    if df is None or df.empty:
        return None
    
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    question_lower = question.lower()
    
    analysis = []
    
    # Total/Revenue queries
    if any(word in question_lower for word in ['total', 'revenue', 'sales', 'overall', 'sum']):
        total = df[amount_col].sum()
        avg = df[amount_col].mean()
        count = len(df)
        analysis.append(f"**Total Revenue:** ${total:,.2f}")
        analysis.append(f"**Total Transactions:** {count:,}")
        analysis.append(f"**Average Order Value:** ${avg:,.2f}")
    
    # Customer queries
    if any(word in question_lower for word in ['customer', 'client', 'buyer', 'who', 'top']):
        if 'customer' in df.columns:
            customer_rev = df.groupby('customer')[amount_col].sum().sort_values(ascending=False)
            analysis.append("\n**Customer Revenue Breakdown:**")
            for i, (cust, rev) in enumerate(customer_rev.head(5).items(), 1):
                pct = (rev / df[amount_col].sum()) * 100
                analysis.append(f"  {i}. **{cust}**: ${rev:,.2f} ({pct:.1f}%)")
    
    # Product queries
    if any(word in question_lower for word in ['product', 'item', 'goods', 'selling']):
        if 'product' in df.columns:
            product_rev = df.groupby('product')[amount_col].sum().sort_values(ascending=False)
            analysis.append("\n**Product Performance:**")
            for i, (prod, rev) in enumerate(product_rev.head(5).items(), 1):
                pct = (rev / df[amount_col].sum()) * 100
                analysis.append(f"  {i}. **{prod}**: ${rev:,.2f} ({pct:.1f}%)")
    
    # Monthly/Time queries
    if any(word in question_lower for word in ['month', 'trend', 'time', 'period', 'when', 'growth']):
        if 'date' in df.columns:
            df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
            df_dated = df[df['date_parsed'].notna()].copy()
            
            if not df_dated.empty:
                df_dated['month'] = df_dated['date_parsed'].dt.strftime('%B %Y')
                monthly = df_dated.groupby('month')[amount_col].sum()
                
                analysis.append("\n**Monthly Revenue Trend:**")
                for month, rev in monthly.items():
                    analysis.append(f"  • **{month}**: ${rev:,.2f}")
                
                if len(monthly) >= 2:
                    first_val = monthly.iloc[0]
                    last_val = monthly.iloc[-1]
                    change = ((last_val - first_val) / first_val) * 100
                    trend = "📈 Growing" if change > 0 else "📉 Declining"
                    analysis.append(f"\n**Trend:** {trend} ({change:+.1f}% change)")
    
    # Comparison queries
    if any(word in question_lower for word in ['compare', 'vs', 'versus', 'difference', 'between']):
        analysis.append("\n**Comparison Analysis:**")
        if 'customer' in df.columns:
            top_cust = df.groupby('customer')[amount_col].sum().nlargest(2)
            if len(top_cust) >= 2:
                c1, v1 = list(top_cust.items())[0]
                c2, v2 = list(top_cust.items())[1]
                diff = v1 - v2
                analysis.append(f"  • **{c1}** vs **{c2}**: ${diff:,.2f} difference")
        
        if 'product' in df.columns:
            top_prod = df.groupby('product')[amount_col].sum().nlargest(2)
            if len(top_prod) >= 2:
                p1, v1 = list(top_prod.items())[0]
                p2, v2 = list(top_prod.items())[1]
                diff = v1 - v2
                analysis.append(f"  • **{p1}** vs **{p2}**: ${diff:,.2f} difference")
    
    return "\n".join(analysis) if analysis else None


def get_graph_summary(company_id: str) -> str:
    """
    Get a clean summary of the knowledge graph for display
    """
    G = load_graph(company_id)
    if not G or G.number_of_nodes() == 0:
        return "No graph data available."
    
    stats = get_graph_stats(company_id)
    df = revenue_dataframe(company_id)
    
    summary_parts = [
        "**Knowledge Graph Structure:**",
        f"• **Entities:** {stats['total_nodes']:,} nodes",
        f"• **Relationships:** {stats['total_edges']:,} connections",
        f"• **Customers:** {stats['customers']:,}",
        f"• **Products:** {stats['products']:,}",
        f"• **Invoices:** {stats['invoices']:,}"
    ]
    
    if df is not None and not df.empty:
        amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
        total = df[amount_col].sum()
        summary_parts.append(f"\n**Data Coverage:**")
        summary_parts.append(f"• **Total Revenue:** ${total:,.2f}")
        summary_parts.append(f"• **Transactions:** {len(df):,}")
    
    return "\n".join(summary_parts)



