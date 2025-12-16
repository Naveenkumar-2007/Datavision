# Graph query module
import networkx as nx
import pandas as pd
import json
from pathlib import Path
from config.settings import Settings
from utils.paths import STORAGE_BASE
from core.llm import chat


def get_user_currency(user_id: str) -> tuple:
    """Get user's detected currency symbol and code from metadata"""
    try:
        metadata_path = STORAGE_BASE / user_id / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                code = data.get('currency', 'INR')
                symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹', 'JPY': '¥'}
                return symbols.get(code, '₹'), code
    except Exception as e:
        print(f"⚠️ Currency detection error: {e}")
    return '₹', 'INR'  # Default to INR


def load_graph(company_id: str):
    """Load company's knowledge graph from user-specific directory"""
    import pickle
    
    # First try user-specific graph directory (Consolidated storage)
    user_graph_dir = STORAGE_BASE / company_id / "graph"
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
    Extract revenue/invoice data from graph as DataFrame.
    Works with or without date information.
    Includes currency and source_file per invoice for enterprise tracking.
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
            currency = data.get("currency", "USD")  # Get currency from invoice node
            source_file = data.get("source_file", "Unknown")  # Get source file from invoice node

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
            
            # Allow partial data - don't strictly require both customer and product
            if amount > 0 or customer or product:
                rows.append({
                    "invoice": invoice_id,
                    "customer": customer if customer else "Unknown Customer",
                    "product": product if product else "General Item",
                    "date": date if date else "Unknown Date",
                    "amount": float(amount) if amount else 0.0,
                    "currency": currency,
                    "source_file": source_file  # Track which file this record came from
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
    
    # Get user's currency
    currency_symbol, currency_code = get_user_currency(company_id)
    
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
• Total Revenue: {currency_symbol}{total_revenue:,.2f}
• Average Order Value: {currency_symbol}{avg_order:,.2f}
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
• Latest Month: {currency_symbol}{latest_month_revenue:,.2f}
• Previous Month: {currency_symbol}{prev_month_revenue:,.2f}
• Change: {change_pct:+.1f}% {trend}

"""
            
            # ALL customer data (not just top 3)
            if 'customer' in df.columns:
                all_customer_rev = df.groupby('customer')[amount_col].sum().sort_values(ascending=False)
                customer_orders = df.groupby('customer').size()
                
                # Top customers
                revenue_insights += "**Top Customers by Revenue:**\n"
                for i, (cust, rev) in enumerate(all_customer_rev.head(3).items(), 1):
                    orders = customer_orders.get(cust, 0)
                    revenue_insights += f"  {i}. {cust}: {currency_symbol}{rev:,.2f} ({orders} orders)\n"
                
                # Lowest customer
                lowest_customer = all_customer_rev.sort_values(ascending=True).head(1)
                if len(lowest_customer) > 0:
                    lowest_name = lowest_customer.index[0]
                    lowest_rev = lowest_customer.iloc[0]
                    lowest_orders = customer_orders.get(lowest_name, 0)
                    revenue_insights += f"\n**Lowest-Spending Customer:**\n"
                    revenue_insights += f"  • {lowest_name}: {currency_symbol}{lowest_rev:,.2f} ({lowest_orders} orders)\n"
                
                # Complete customer table
                revenue_insights += "\n**All Customers (Complete Data):**\n"
                revenue_insights += f"| Customer | Revenue ({currency_symbol}) | Orders |\n"
                revenue_insights += "|----------|-------------|--------|\n"
                for cust, rev in all_customer_rev.items():
                    orders = customer_orders.get(cust, 0)
                    revenue_insights += f"| {cust} | {rev:,.2f} | {orders} |\n"
                revenue_insights += "\n"
            
            if 'product' in df.columns:
                all_product_rev = df.groupby('product')[amount_col].sum().sort_values(ascending=False)
                product_counts = df.groupby('product').size()
                
                # Top products
                revenue_insights += "**Top Products by Revenue:**\n"
                for i, (prod, rev) in enumerate(all_product_rev.head(3).items(), 1):
                    count = product_counts.get(prod, 0)
                    revenue_insights += f"  {i}. {prod}: {currency_symbol}{rev:,.2f} ({count} sales)\n"
                
                # Lowest product
                lowest_products = all_product_rev.sort_values(ascending=True)
                if len(lowest_products) > 0:
                    lowest_name = lowest_products.index[0]
                    lowest_rev = lowest_products.iloc[0]
                    lowest_count = product_counts.get(lowest_name, 0)
                    revenue_insights += f"\n**Lowest-Performing Product:**\n"
                    revenue_insights += f"  • {lowest_name}: {currency_symbol}{lowest_rev:,.2f} ({lowest_count} sales)\n"
                
                # Complete product table
                revenue_insights += "\n**All Products (Complete Data):**\n"
                revenue_insights += f"| Product | Revenue ({currency_symbol}) | Sales |\n"
                revenue_insights += "|---------|-------------|-------|\n"
                for prod, rev in all_product_rev.items():
                    count = product_counts.get(prod, 0)
                    revenue_insights += f"| {prod} | {rev:,.2f} | {count} |\n"
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
    
    # Get user's currency
    currency_symbol, currency_code = get_user_currency(company_id)
    
    analysis = []
    
    # Total/Revenue queries
    if any(word in question_lower for word in ['total', 'revenue', 'sales', 'overall', 'sum']):
        total = df[amount_col].sum()
        avg = df[amount_col].mean()
        count = len(df)
        analysis.append(f"**Total Revenue:** {currency_symbol}{total:,.2f}")
        analysis.append(f"**Total Transactions:** {count:,}")
        analysis.append(f"**Average Order Value:** {currency_symbol}{avg:,.2f}")
    
    # Customer queries - handle both top and bottom performers
    if any(word in question_lower for word in ['customer', 'client', 'buyer', 'who', 'top', 'lowest', 'minimum', 'least', 'bottom', 'worst', 'smallest', 'min']):
        if 'customer' in df.columns:
            customer_rev = df.groupby('customer')[amount_col].sum()
            customer_orders = df.groupby('customer').size()
            
            # Check if asking for lowest/minimum/least
            is_lowest_query = any(word in question_lower for word in ['lowest', 'minimum', 'least', 'bottom', 'worst', 'smallest', 'min'])
            
            if is_lowest_query:
                # Sort ascending for lowest
                customer_rev_sorted = customer_rev.sort_values(ascending=True)
                analysis.append("\n**Lowest-Spending Customers:**")
                lowest_cust = customer_rev_sorted.iloc[0]
                lowest_name = customer_rev_sorted.index[0]
                lowest_orders = customer_orders.get(lowest_name, 0)
                analysis.append(f"  🔻 **{lowest_name}**: {currency_symbol}{lowest_cust:,.2f} ({lowest_orders} orders) - LOWEST")
                analysis.append("\n**All Customers (Low to High):**")
                for i, (cust, rev) in enumerate(customer_rev_sorted.items(), 1):
                    orders = customer_orders.get(cust, 0)
                    pct = (rev / df[amount_col].sum()) * 100
                    marker = " ← LOWEST" if i == 1 else ""
                    analysis.append(f"  {i}. **{cust}**: {currency_symbol}{rev:,.2f} ({orders} orders, {pct:.1f}%){marker}")
            else:
                # Sort descending for top
                customer_rev_sorted = customer_rev.sort_values(ascending=False)
                analysis.append("\n**Top Customers by Revenue:**")
                for i, (cust, rev) in enumerate(customer_rev_sorted.head(5).items(), 1):
                    orders = customer_orders.get(cust, 0)
                    pct = (rev / df[amount_col].sum()) * 100
                    analysis.append(f"  {i}. **{cust}**: {currency_symbol}{rev:,.2f} ({orders} orders, {pct:.1f}%)")
            
            # Always include complete customer summary for context
            analysis.append("\n**Complete Customer Data:**")
            analysis.append(f"| Customer | Revenue ({currency_symbol}) | Orders |")
            analysis.append("|----------|---------|--------|")
            for cust, rev in customer_rev.sort_values(ascending=False).items():
                orders = customer_orders.get(cust, 0)
                analysis.append(f"| {cust} | {rev:,.2f} | {orders} |")
    
    # Product queries - handle both top and lowest performers
    if any(word in question_lower for word in ['product', 'item', 'goods', 'selling', 'performance', 'perform']):
        if 'product' in df.columns:
            product_rev = df.groupby('product')[amount_col].sum()
            product_counts = df.groupby('product').size()
            
            # Check if asking for lowest/minimum/least
            is_lowest_query = any(word in question_lower for word in ['lowest', 'minimum', 'least', 'bottom', 'worst', 'smallest', 'min', 'poor', 'bad'])
            
            if is_lowest_query:
                # Sort ascending for lowest
                product_rev_sorted = product_rev.sort_values(ascending=True)
                analysis.append("\n**Lowest-Performing Products:**")
                lowest_prod = product_rev_sorted.iloc[0]
                lowest_name = product_rev_sorted.index[0]
                lowest_count = product_counts.get(lowest_name, 0)
                analysis.append(f"  🔻 **{lowest_name}**: {currency_symbol}{lowest_prod:,.2f} ({lowest_count} sales) - LOWEST")
                analysis.append("\n**All Products (Low to High):**")
                for i, (prod, rev) in enumerate(product_rev_sorted.items(), 1):
                    count = product_counts.get(prod, 0)
                    pct = (rev / df[amount_col].sum()) * 100
                    marker = " ← LOWEST" if i == 1 else ""
                    analysis.append(f"  {i}. **{prod}**: {currency_symbol}{rev:,.2f} ({count} sales, {pct:.1f}%){marker}")
            else:
                # Sort descending for top
                product_rev_sorted = product_rev.sort_values(ascending=False)
                analysis.append("\n**Top Products by Revenue:**")
                for i, (prod, rev) in enumerate(product_rev_sorted.head(5).items(), 1):
                    count = product_counts.get(prod, 0)
                    pct = (rev / df[amount_col].sum()) * 100
                    analysis.append(f"  {i}. **{prod}**: {currency_symbol}{rev:,.2f} ({count} sales, {pct:.1f}%)")
            
            # Always include complete product summary for context
            analysis.append("\n**Complete Product Data:**")
            analysis.append(f"| Product | Revenue ({currency_symbol}) | Sales |")
            analysis.append("|---------|---------|-------|")
            for prod, rev in product_rev.sort_values(ascending=False).items():
                count = product_counts.get(prod, 0)
                analysis.append(f"| {prod} | {rev:,.2f} | {count} |")
    
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
                    analysis.append(f"  • **{month}**: {currency_symbol}{rev:,.2f}")
                
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
                analysis.append(f"  • **{c1}** vs **{c2}**: {currency_symbol}{diff:,.2f} difference")
        
        if 'product' in df.columns:
            top_prod = df.groupby('product')[amount_col].sum().nlargest(2)
            if len(top_prod) >= 2:
                p1, v1 = list(top_prod.items())[0]
                p2, v2 = list(top_prod.items())[1]
                diff = v1 - v2
                analysis.append(f"  • **{p1}** vs **{p2}**: {currency_symbol}{diff:,.2f} difference")
    
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
    
    # Get user's currency
    currency_symbol, currency_code = get_user_currency(company_id)
    
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
        summary_parts.append(f"• **Total Revenue:** {currency_symbol}{total:,.2f}")
        summary_parts.append(f"• **Transactions:** {len(df):,}")
    
    return "\n".join(summary_parts)



