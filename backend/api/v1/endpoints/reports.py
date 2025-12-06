"""
Real Reports from uploaded data - NO FAKE CONTENT
Generated from actual processed files
Enterprise-grade multi-currency support
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback
from datetime import datetime
import pandas as pd

from graph.query import revenue_dataframe
from config.settings import Settings
from utils.paths import get_user_paths, STORAGE_BASE
from utils.currency import (
    detect_currency, 
    format_currency, 
    get_currency_symbol,
    load_currency_metadata,
    save_currency_metadata
)

router = APIRouter()


class ReportRequest(BaseModel):
    userId: str
    reportType: str
    dateRange: Optional[str] = "all"
    format: str = "json"


def get_user_currency(user_id: str, df: pd.DataFrame = None) -> str:
    """Get currency for user - from metadata or detect from data."""
    paths = get_user_paths(user_id)
    
    # Try stored metadata first
    stored = load_currency_metadata(user_id, STORAGE_BASE)
    if stored:
        return stored
    
    # Detect from data
    if df is not None and not df.empty:
        currency = detect_currency(df, paths.get("files"))
        save_currency_metadata(user_id, currency, STORAGE_BASE)
        return currency
    
    return 'USD'


def generate_revenue_report(user_id: str, df: pd.DataFrame) -> dict:
    """Generate REAL revenue report"""
    if df is None or df.empty:
        return {
            "title": "Revenue Report",
            "error": "No data available",
            "sections": []
        }
    
    sections = []
    currency = get_user_currency(user_id, df)
    
    # Clean amount column
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount' if 'total_amount' in df.columns else None
    if amount_col:
        df[amount_col] = df[amount_col].astype(str).str.replace(r'[₹$€£¥,\s]', '', regex=True)
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        total_revenue = float(df[amount_col].sum())
    else:
        total_revenue = 0
    
    total_invoices = len(df)
    avg_invoice = total_revenue / total_invoices if total_invoices > 0 else 0
    
    sections.append({
        "title": "Revenue Summary",
        "content": f"""
Total Revenue: {format_currency(total_revenue, currency)}
Total Invoices: {total_invoices:,}
Average Invoice: {format_currency(avg_invoice, currency)}

Based on {total_invoices} invoices from uploaded files.
Currency: {currency}
        """.strip(),
        "data": {
            "totalRevenue": total_revenue,
            "totalInvoices": total_invoices,
            "avgInvoice": avg_invoice,
            "currency": currency
        }
    })
    
    if 'date' in df.columns:
        try:
            df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
            df_dated = df[df['date_parsed'].notna()].copy()
            
            if not df_dated.empty:
                date_range = f"{df_dated['date_parsed'].min().date()} to {df_dated['date_parsed'].max().date()}"
                monthly = df_dated.groupby(df_dated['date_parsed'].dt.to_period('M'))['amount'].sum()
                
                monthly_text = "\n".join([f"- {period}: {format_currency(amount, currency)}" for period, amount in monthly.items()])
                
                sections.append({
                    "title": "Time Analysis",
                    "content": f"Date Range: {date_range}\n\nMonthly Revenue:\n{monthly_text}"
                })
        except:
            pass
    
    if 'product' in df.columns:
        product_revenue = df.groupby('product')['amount'].sum().sort_values(ascending=False).head(5)
        product_text = "\n".join([f"- {prod}: {format_currency(amt, currency)}" for prod, amt in product_revenue.items()])
        
        sections.append({
            "title": "Top 5 Products",
            "content": product_text
        })
    
    if 'customer' in df.columns:
        customer_revenue = df.groupby('customer')['amount'].sum().sort_values(ascending=False).head(5)
        customer_text = "\n".join([f"- {cust}: {format_currency(amt, currency)}" for cust, amt in customer_revenue.items()])
        
        sections.append({
            "title": "Top 5 Customers",
            "content": customer_text
        })
    
    return {
        "title": "Revenue Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "real_uploaded_files",
        "sections": sections
    }

def generate_customer_report(user_id: str, df: pd.DataFrame) -> dict:
    if df is None or df.empty or 'customer' not in df.columns:
        return {
            "title": "Customer Report",
            "error": "No customer data",
            "sections": []
        }
    
    sections = []
    currency = get_user_currency(user_id, df)
    
    # Clean amount column
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount' if 'total_amount' in df.columns else None
    if amount_col:
        df[amount_col] = df[amount_col].astype(str).str.replace(r'[₹$€£¥,\s]', '', regex=True)
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        total_revenue = float(df[amount_col].sum())
    else:
        total_revenue = 0
    
    unique_customers = int(df['customer'].nunique())
    avg_customer_value = total_revenue / unique_customers if unique_customers > 0 else 0
    
    sections.append({
        "title": "Customer Overview",
        "content": f"""
Total Customers: {unique_customers:,}
Total Revenue: {format_currency(total_revenue, currency)}
Average Customer Value: {format_currency(avg_customer_value, currency)}
Currency: {currency}
        """.strip(),
        "data": {
            "totalCustomers": unique_customers,
            "totalRevenue": total_revenue,
            "avgCustomerValue": avg_customer_value,
            "currency": currency
        }
    })
    
    if amount_col:
        customer_stats = df.groupby('customer').agg({
            amount_col: ['sum', 'count', 'mean']
        }).reset_index()
        
        customer_stats.columns = ['customer', 'total_revenue', 'order_count', 'avg_order']
        customer_stats = customer_stats.sort_values('total_revenue', ascending=False)
        
        top_10 = customer_stats.head(10)
        customer_text = []
        customer_data = []
        for _, row in top_10.iterrows():
            customer_text.append(
                f"- {row['customer']}: {format_currency(row['total_revenue'], currency)} ({int(row['order_count'])} orders)"
            )
            customer_data.append({
                "name": row['customer'],
                "revenue": float(row['total_revenue']),
                "orders": int(row['order_count']),
                "avgOrder": float(row['avg_order'])
            })
        
        sections.append({
            "title": "Top 10 Customers",
            "content": "\n".join(customer_text),
            "data": customer_data
        })
    
    return {
        "title": "Customer Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "real_uploaded_files",
        "currency": currency,
        "sections": sections
    }

def generate_product_report(user_id: str, df: pd.DataFrame) -> dict:
    if df is None or df.empty or 'product' not in df.columns:
        return {
            "title": "Product Report",
            "error": "No product data",
            "sections": []
        }
    
    sections = []
    currency = get_user_currency(user_id, df)
    
    # Clean amount column
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount' if 'total_amount' in df.columns else None
    if amount_col:
        df[amount_col] = df[amount_col].astype(str).str.replace(r'[₹$€£¥,\s]', '', regex=True)
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        total_revenue = float(df[amount_col].sum())
    else:
        total_revenue = 0
    
    unique_products = int(df['product'].nunique())
    total_units = len(df)
    
    sections.append({
        "title": "Product Overview",
        "content": f"""
Total Products: {unique_products:,}
Total Revenue: {format_currency(total_revenue, currency)}
Units Sold: {total_units:,}
Currency: {currency}
        """.strip(),
        "data": {
            "totalProducts": unique_products,
            "totalRevenue": total_revenue,
            "unitsSold": total_units,
            "currency": currency
        }
    })
    
    if amount_col:
        product_stats = df.groupby('product').agg({
            amount_col: ['sum', 'count', 'mean']
        }).reset_index()
        
        product_stats.columns = ['product', 'total_revenue', 'units_sold', 'avg_price']
        product_stats = product_stats.sort_values('total_revenue', ascending=False)
        
        top_10 = product_stats.head(10)
        product_text = []
        product_data = []
        for _, row in top_10.iterrows():
            product_text.append(
                f"- {row['product']}: {format_currency(row['total_revenue'], currency)} ({int(row['units_sold'])} units)"
            )
            product_data.append({
                "name": row['product'],
                "revenue": float(row['total_revenue']),
                "units": int(row['units_sold']),
                "avgPrice": float(row['avg_price'])
            })
        
        sections.append({
            "title": "Top 10 Products",
            "content": "\n".join(product_text),
            "data": product_data
        })
    
    return {
        "title": "Product Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "real_uploaded_files",
        "currency": currency,
        "sections": sections
    }

def generate_executive_report(user_id: str, df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "title": "Executive Summary",
            "error": "No data",
            "sections": []
        }
    
    sections = []
    currency = get_user_currency(user_id, df)
    
    # Clean amount column
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount' if 'total_amount' in df.columns else None
    if amount_col:
        df[amount_col] = df[amount_col].astype(str).str.replace(r'[₹$€£¥,\s]', '', regex=True)
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        total_revenue = float(df[amount_col].sum())
    else:
        total_revenue = 0
    
    total_invoices = len(df)
    unique_customers = int(df['customer'].nunique()) if 'customer' in df.columns else 0
    unique_products = int(df['product'].nunique()) if 'product' in df.columns else 0
    avg_transaction = total_revenue / total_invoices if total_invoices > 0 else 0
    
    sections.append({
        "title": "Key Metrics",
        "content": f"""
Total Revenue: {format_currency(total_revenue, currency)}
Transactions: {total_invoices:,}
Customers: {unique_customers:,}
Products: {unique_products:,}
Avg Transaction: {format_currency(avg_transaction, currency)}
Currency: {currency}
        """.strip(),
        "data": {
            "totalRevenue": total_revenue,
            "transactions": total_invoices,
            "customers": unique_customers,
            "products": unique_products,
            "avgTransaction": avg_transaction,
            "currency": currency
        }
    })
    
    if 'customer' in df.columns and amount_col:
        customer_revenue = df.groupby('customer')[amount_col].sum()
        top_customer = customer_revenue.idxmax()
        top_customer_revenue = customer_revenue.max()
        
        sections.append({
            "title": "Top Customer",
            "content": f"{top_customer}: {format_currency(top_customer_revenue, currency)}",
            "data": {"name": top_customer, "revenue": float(top_customer_revenue)}
        })
    
    if 'product' in df.columns and amount_col:
        product_revenue = df.groupby('product')[amount_col].sum()
        top_product = product_revenue.idxmax()
        top_product_revenue = product_revenue.max()
        
        sections.append({
            "title": "Top Product",
            "content": f"{top_product}: {format_currency(top_product_revenue, currency)}",
            "data": {"name": top_product, "revenue": float(top_product_revenue)}
        })
    
    return {
        "title": "Executive Summary",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "real_uploaded_files",
        "currency": currency,
        "sections": sections
    }

@router.post("/generate")
async def generate_report(request: ReportRequest):
    """Generate REAL report from uploaded data"""
    try:
        user_id = request.userId
        report_type = request.reportType
        
        paths = get_user_paths(user_id)
        Settings.GRAPH_DIR = paths["graph"]
        
        df = revenue_dataframe(user_id)
        
        if report_type == "revenue" or report_type == "weekly" or report_type == "monthly":
            report = generate_revenue_report(user_id, df)
        elif report_type == "customer":
            report = generate_customer_report(user_id, df)
        elif report_type == "product":
            report = generate_product_report(user_id, df)
        elif report_type == "executive" or report_type == "quarterly":
            report = generate_executive_report(user_id, df)
        else:
            report = generate_executive_report(user_id, df)
        
        report["reportType"] = report_type
        report["userId"] = user_id
        
        return report
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list/{user_id}")
async def list_reports(user_id: str):
    try:
        paths = get_user_paths(user_id)
        Settings.GRAPH_DIR = paths["graph"]
        
        try:
            df = revenue_dataframe(user_id)
            has_data = df is not None and not df.empty
        except:
            has_data = False
        
        reports = [
            {
                "id": "revenue",
                "name": "Revenue Analysis",
                "description": "Revenue breakdown from uploaded files",
                "available": has_data
            },
            {
                "id": "customer",
                "name": "Customer Analysis",
                "description": "Customer insights from uploaded files",
                "available": has_data
            },
            {
                "id": "product",
                "name": "Product Performance",
                "description": "Product analysis from uploaded files",
                "available": has_data
            },
            {
                "id": "executive",
                "name": "Executive Summary",
                "description": "Overview from uploaded files",
                "available": has_data
            }
        ]
        
        return {
            "reports": reports,
            "hasData": has_data,
            "message": "Upload files to generate reports" if not has_data else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
