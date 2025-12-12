# Graph schema definitions
KEYS = {
    "customer": ["customer", "client", "buyer", "name", "customer_name", "client_name", "buyer_name", "cust", "user_name", "username", "user"],
    "product": ["product", "item", "goods", "service", "product_name", "item_name", "sku", "prod"],
    "invoice": ["invoice", "bill", "order", "transaction", "inv", "order_id", "transaction_id", "invoice_no", "invoice_number", "bill_no", "order_no", "invoice_id"],
    "date": ["date", "order_date", "invoice_date", "transaction_date", "purchase_date", "sale_date", "created", "created_at", "dt"],
    "amount": ["total", "amount", "price", "value", "revenue", "sales", "total_amount", "total_price", "grand_total", "sum", "net", "gross", "cost", "subtotal", "total_value", "sale_amount", "invoice_amount", "amount_eur", "amount_usd", "amount_inr", "eur", "usd", "inr"]
}

def detect_schema(columns):
    """Detect which columns map to which graph entities"""
    out = {}
    columns_lower = {col: col.lower().strip() for col in columns}
    
    for col, col_lower in columns_lower.items():
        for k, vals in KEYS.items():
            # First try exact match
            if col_lower in vals:
                out[k] = col
                break
            # Then try partial match (key in column name)
            for v in vals:
                if v in col_lower:
                    if k not in out:  # Don't override exact matches
                        out[k] = col
                    break
    
    print(f"📋 Schema detection: columns={list(columns)}, detected={out}")
    return out
