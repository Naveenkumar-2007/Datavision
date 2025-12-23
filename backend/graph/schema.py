# Graph schema definitions
# UNIVERSAL - Works with ANY data domain (Sales, HR, Healthcare, Education, etc.)
KEYS = {
    # ENTITY 1: Main grouping entity (Customer/Department/Region/etc.)
    "customer": [
        # Sales/Business
        "customer", "client", "buyer", "customer_name", "client_name", "buyer_name", 
        "cust", "user_name", "username", "user", "email", "contact", "company", "account",
        # HR/Employee
        "department", "dept", "team", "division", "unit", "group", "section", "branch",
        # Healthcare
        "patient", "doctor", "hospital", "clinic", "facility",
        # Education
        "student", "teacher", "school", "course", "class", "subject",
        # General
        "region", "area", "zone", "territory", "location", "city", "country", "state"
    ],
    # ENTITY 2: Item/Product/Role
    "product": [
        # Sales/Business
        "product", "item", "goods", "service", "product_name", "item_name", "sku", 
        "prod", "description", "details", "category", "type",
        # HR/Employee
        "role", "position", "job", "job_title", "title", "designation", "level", "grade",
        # Healthcare
        "treatment", "procedure", "medication", "diagnosis", "specialty",
        # Education
        "subject", "topic", "module", "program", "major"
    ],
    # ENTITY 3: Individual record identifier
    "invoice": [
        # Sales/Business
        "invoice", "bill", "order", "transaction", "inv", "order_id", "transaction_id", 
        "invoice_no", "invoice_number", "bill_no", "order_no", "invoice_id", "ref", "reference",
        # HR/Employee
        "employee", "emp", "employee_id", "emp_id", "staff", "staff_id", "worker", "name",
        # Healthcare
        "patient_id", "record_id", "case_id", "visit_id",
        # Education
        "student_id", "enrollment_id", "registration_id",
        # General
        "id", "record", "entry", "row_id"
    ],
    # DATE
    "date": [
        "date", "order_date", "invoice_date", "transaction_date", "purchase_date", "sale_date", 
        "created", "created_at", "dt", "time", "timestamp", "year", "month", "day",
        "hire_date", "join_date", "start_date", "end_date", "birth_date", "dob",
        "admission_date", "discharge_date", "visit_date"
    ],
    # AMOUNT/VALUE
    "amount": [
        # Sales/Business
        "total", "amount", "price", "value", "revenue", "sales", "total_amount", 
        "total_price", "grand_total", "sum", "net", "gross", "cost", "subtotal", 
        "total_value", "sale_amount", "invoice_amount", "charge", "payment",
        "amount_eur", "amount_usd", "amount_inr", "eur", "usd", "inr",
        # HR/Employee
        "salary", "wage", "pay", "compensation", "income", "earnings", "bonus", 
        "commission", "allowance", "ctc", "package",
        # Healthcare
        "bill_amount", "treatment_cost", "fee", "charges",
        # Education
        "score", "marks", "grade", "percentage", "gpa", "cgpa", "tuition", "fees"
    ]
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
