# Graph schema definitions
KEYS = {
    "customer": ["customer", "client"],
    "product": ["product", "item"],
    "invoice": ["invoice", "bill", "order"],
    "date": ["date"],
    "amount": ["total", "amount", "price"]
}

def detect_schema(columns):
    out = {}
    for col in columns:
        c = col.lower()
        for k, vals in KEYS.items():
            if any(v in c for v in vals):
                out[k] = col
    return out
