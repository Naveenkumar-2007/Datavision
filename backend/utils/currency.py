"""
Shared currency detection and formatting utilities
Enterprise-grade multi-currency support for $50K product
Detects: USD, EUR, GBP, INR, JPY, AUD, CAD, CHF, CNY, SGD
"""

import pandas as pd
from pathlib import Path
import re
import json
from typing import Optional, Dict, Any, List


# Comprehensive currency configuration
CURRENCY_CONFIG = {
    'USD': {'symbol': '$', 'name': 'US Dollar', 'locale': 'en-US', 'keywords': ['usd', 'dollar', 'us$', 'united states']},
    'EUR': {'symbol': '€', 'name': 'Euro', 'locale': 'de-DE', 'keywords': ['eur', 'euro', '€']},
    'GBP': {'symbol': '£', 'name': 'British Pound', 'locale': 'en-GB', 'keywords': ['gbp', 'pound', 'sterling', '£', 'british']},
    'INR': {'symbol': '₹', 'name': 'Indian Rupee', 'locale': 'en-IN', 'keywords': ['inr', 'rupee', 'rupees', '₹', 'indian', 'india']},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen', 'locale': 'ja-JP', 'keywords': ['jpy', 'yen', '¥', 'japan']},
    'AUD': {'symbol': 'A$', 'name': 'Australian Dollar', 'locale': 'en-AU', 'keywords': ['aud', 'australian', 'australia']},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar', 'locale': 'en-CA', 'keywords': ['cad', 'canadian', 'canada']},
    'CHF': {'symbol': 'CHF', 'name': 'Swiss Franc', 'locale': 'de-CH', 'keywords': ['chf', 'franc', 'swiss']},
    'CNY': {'symbol': '¥', 'name': 'Chinese Yuan', 'locale': 'zh-CN', 'keywords': ['cny', 'yuan', 'rmb', 'chinese', 'china']},
    'SGD': {'symbol': 'S$', 'name': 'Singapore Dollar', 'locale': 'en-SG', 'keywords': ['sgd', 'singapore']},
}

# Currency symbol to code mapping
SYMBOL_TO_CODE = {
    '$': 'USD',
    '€': 'EUR',
    '£': 'GBP',
    '₹': 'INR',
    '¥': 'JPY',  # Could be JPY or CNY - needs context
    'A$': 'AUD',
    'C$': 'CAD',
    'S$': 'SGD',
}


def detect_currency_from_value(value: str) -> Optional[str]:
    """Detect currency from a single value string."""
    if not isinstance(value, str):
        value = str(value)
    
    # Check for currency symbols at start
    value = value.strip()
    
    # Check specific multi-char symbols first
    if value.startswith('A$') or 'AUD' in value.upper():
        return 'AUD'
    if value.startswith('C$') or 'CAD' in value.upper():
        return 'CAD'
    if value.startswith('S$') or 'SGD' in value.upper():
        return 'SGD'
    if value.startswith('CHF') or 'CHF' in value.upper():
        return 'CHF'
    
    # Check single char symbols
    if '€' in value:
        return 'EUR'
    if '£' in value:
        return 'GBP'
    if '₹' in value:
        return 'INR'
    if '$' in value and not any(x in value for x in ['A$', 'C$', 'S$']):
        return 'USD'
    if '¥' in value:
        # Distinguish between JPY and CNY based on value magnitude
        # JPY typically has no decimal, CNY does
        return 'JPY' if '.' not in value else 'CNY'
    
    return None


def detect_currency_from_column_names(columns: List[str]) -> Optional[str]:
    """Detect currency from column names."""
    col_text = ' '.join(columns).lower()
    
    for code, config in CURRENCY_CONFIG.items():
        if any(kw in col_text for kw in config['keywords']):
            return code
    
    return None


def detect_currency_from_filename(filename: str) -> Optional[str]:
    """Detect currency from filename."""
    filename_lower = filename.lower()
    
    for code, config in CURRENCY_CONFIG.items():
        if any(kw in filename_lower for kw in config['keywords']):
            return code
    
    return None


def detect_currency(
    df: pd.DataFrame = None, 
    files_path: Path = None,
    filename: str = None,
    metadata_path: Path = None,
    skip_metadata: bool = False
) -> str:
    """
    Enterprise-grade currency detection using multiple strategies.
    
    Priority order (FIXED - data values take precedence):
    1. Stored metadata (from previous detection) - only if skip_metadata=False
    2. Currency column in DataFrame (explicit currency field)
    3. Currency SYMBOLS in amount values (₹, $, €, £, ¥) - MOST RELIABLE
    4. Column name hints (amount_usd, price_eur, etc.)
    5. Filename hints (only as fallback)
    6. Files in directory (only as fallback)
    
    When skip_metadata=True (during file upload/rebuild):
    - Skip stored metadata, always detect fresh from data
    
    Args:
        df: DataFrame with amount data
        files_path: Path to user's files directory
        filename: Specific filename being processed
        metadata_path: Path to stored currency metadata
        skip_metadata: If True, skip reading stored metadata (for fresh detection)
        
    Returns:
        Currency code: 'USD', 'EUR', 'GBP', 'INR', 'JPY', etc.
    """
    detected_currencies = []
    
    # STRATEGY 1: Check stored metadata (skip during upload/rebuild)
    if not skip_metadata and metadata_path and metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                meta = json.load(f)
                if 'currency' in meta:
                    print(f"💰 Using stored currency from metadata: {meta['currency']}")
                    return meta['currency']
        except:
            pass
    
    # STRATEGY 2: Check for explicit currency column
    if df is not None and not df.empty:
        currency_cols = [c for c in df.columns if 'currency' in c.lower()]
        if currency_cols:
            currency_val = df[currency_cols[0]].iloc[0]
            if isinstance(currency_val, str) and currency_val.upper() in CURRENCY_CONFIG:
                print(f"💰 Detected from currency column: {currency_val.upper()}")
                return currency_val.upper()
    
    # STRATEGY 3: Detect from amount values - THIS IS THE HIGHEST PRIORITY FOR ACTUAL DATA
    # Currency symbols in data are the most reliable indicator
    if df is not None and not df.empty:
        amount_cols = [c for c in df.columns if any(
            term in c.lower() for term in ['amount', 'total', 'price', 'revenue', 'sales', 'value', 'cost']
        )]
        
        for col in amount_cols:
            # Sample first 100 non-null values
            sample = df[col].dropna().head(100).astype(str)
            for val in sample:
                detected = detect_currency_from_value(val)
                if detected:
                    detected_currencies.append(detected)
                    print(f"💰 Detected {detected} from value '{val[:20]}' in column '{col}'")
                    # If we found a currency symbol in the data, this is highly reliable
                    # Return immediately - data symbols are the most trustworthy
                    return detected
    
    # STRATEGY 4: Check column names for currency hints
    if df is not None and not df.empty:
        col_currency = detect_currency_from_column_names(list(df.columns))
        if col_currency:
            print(f"💰 Detected from column names: {col_currency}")
            detected_currencies.append(col_currency)
    
    # STRATEGY 5: Check specific filename (only as fallback)
    if filename and not detected_currencies:
        file_currency = detect_currency_from_filename(filename)
        if file_currency:
            print(f"💰 Detected from filename '{filename}': {file_currency}")
            detected_currencies.append(file_currency)
    
    # STRATEGY 6: Check all files in directory (only as fallback)
    if files_path and files_path.exists() and not detected_currencies:
        try:
            for f in files_path.glob('*'):
                if f.is_file():
                    file_currency = detect_currency_from_filename(f.name)
                    if file_currency:
                        detected_currencies.append(file_currency)
        except:
            pass
    
    # Return most common detected currency, or USD as fallback (most common global currency)
    if detected_currencies:
        from collections import Counter
        most_common = Counter(detected_currencies).most_common(1)[0][0]
        print(f"💰 Final detected currency: {most_common}")
        return most_common
    
    print(f"💰 No currency detected, defaulting to USD")
    return 'USD'  # Default fallback - USD is most common globally


def detect_currency_from_files(files_path: Path) -> Dict[str, str]:
    """
    Detect currency for each file in a directory.
    Returns a mapping of filename -> currency code.
    """
    result = {}
    
    if not files_path or not files_path.exists():
        return result
    
    for file in files_path.glob('*'):
        if file.is_file() and file.suffix.lower() in ['.csv', '.xlsx', '.xls']:
            try:
                if file.suffix.lower() == '.csv':
                    df = pd.read_csv(file, nrows=100)
                else:
                    df = pd.read_excel(file, nrows=100)
                
                currency = detect_currency(df=df, filename=file.name)
                result[file.name] = currency
            except:
                result[file.name] = detect_currency_from_filename(file.name) or 'USD'
    
    return result


def format_currency(amount: float, currency: str = 'INR', include_code: bool = False) -> str:
    """
    Format amount with proper currency symbol and locale formatting.
    
    Args:
        amount: Numeric amount
        currency: Currency code
        include_code: Whether to include currency code after symbol
        
    Returns:
        Formatted string with currency symbol
    """
    config = CURRENCY_CONFIG.get(currency, CURRENCY_CONFIG['INR'])
    symbol = config['symbol']
    
    # Format number with thousands separator
    if currency == 'INR':
        # Indian numbering system (lakhs, crores)
        formatted = format_indian_number(amount)
    elif currency == 'JPY':
        # Yen typically has no decimal places
        formatted = f"{amount:,.0f}"
    else:
        formatted = f"{amount:,.2f}"
    
    result = f"{symbol}{formatted}"
    
    if include_code:
        result = f"{result} {currency}"
    
    return result


def format_indian_number(num: float) -> str:
    """Format number in Indian numbering system (lakhs, crores)."""
    if num < 1000:
        return f"{num:.2f}"
    
    # Convert to string with 2 decimal places
    num_str = f"{num:.2f}"
    parts = num_str.split('.')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else "00"
    
    # Apply Indian formatting
    result = ""
    length = len(integer_part)
    
    if length <= 3:
        result = integer_part
    else:
        # Last 3 digits
        result = integer_part[-3:]
        remaining = integer_part[:-3]
        
        # Group remaining in pairs
        while remaining:
            if len(remaining) <= 2:
                result = remaining + "," + result
                break
            else:
                result = remaining[-2:] + "," + result
                remaining = remaining[:-2]
    
    return f"{result}.{decimal_part}"


def get_currency_symbol(currency: str = 'USD') -> str:
    """Get currency symbol for code."""
    config = CURRENCY_CONFIG.get(currency, CURRENCY_CONFIG['USD'])
    return config['symbol']


def get_currency_info(currency: str = 'USD') -> Dict[str, Any]:
    """Get full currency information."""
    return CURRENCY_CONFIG.get(currency, CURRENCY_CONFIG['USD'])


def parse_currency_value(value: str, detected_currency: str = None) -> tuple:
    """
    Parse a currency string into numeric value and currency code.
    
    Args:
        value: String like "$1,234.56" or "€1.234,56" or "₹1,23,456"
        detected_currency: Already detected currency code
        
    Returns:
        Tuple of (numeric_value, currency_code)
    """
    if not isinstance(value, str):
        try:
            return (float(value), detected_currency or 'USD')
        except:
            return (0.0, detected_currency or 'USD')
    
    # Detect currency from value
    currency = detect_currency_from_value(value) or detected_currency or 'USD'
    
    # Remove currency symbols and whitespace
    clean = re.sub(r'[₹$€£¥A$C$S$CHF\s]', '', value)
    
    # Handle European format (1.234,56) vs US format (1,234.56)
    if ',' in clean and '.' in clean:
        # If comma comes after dot, it's European format
        if clean.rfind(',') > clean.rfind('.'):
            clean = clean.replace('.', '').replace(',', '.')
        else:
            clean = clean.replace(',', '')
    elif ',' in clean and '.' not in clean:
        # Could be European decimal or US thousands
        # If single comma with 2 digits after, treat as decimal
        parts = clean.split(',')
        if len(parts) == 2 and len(parts[1]) == 2:
            clean = clean.replace(',', '.')
        else:
            clean = clean.replace(',', '')
    
    try:
        return (float(clean), currency)
    except:
        return (0.0, currency)


def detect_and_save_user_currency(user_id: str, files_path: Path, storage_base: Path) -> str:
    """
    Consolidated function to detect currency from all user files and save to metadata.
    ALWAYS detects fresh from data - ignores stored metadata.
    
    Args:
        user_id: User identifier
        files_path: Path to user's files directory
        storage_base: Base storage path for metadata
        
    Returns:
        Detected currency code (defaults to INR)
    """
    from collections import Counter
    
    if not files_path or not files_path.exists():
        return 'INR'
    
    detected_currencies = []
    
    for file in files_path.glob('*'):
        if file.is_file():
            ext = file.suffix.lower()
            if ext not in ['.csv', '.xlsx', '.xls']:
                continue
                
            try:
                df = None
                if ext == '.csv':
                    df = pd.read_csv(file, nrows=100)
                elif ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(file, nrows=100)
                
                if df is not None and not df.empty:
                    # skip_metadata=True to always detect fresh from actual data
                    currency = detect_currency(df=df, filename=file.name, skip_metadata=True)
                    detected_currencies.append(currency)
                    print(f"💰 Detected {currency} from {file.name}")
            except Exception as e:
                print(f"⚠️ Error detecting currency from {file.name}: {e}")
    
    if detected_currencies:
        most_common = Counter(detected_currencies).most_common(1)[0][0]
        save_currency_metadata(user_id, most_common, storage_base)
        print(f"✅ Saved currency {most_common} for user {user_id}")
        return most_common
    
    print(f"⚠️ No currency detected from files, defaulting to USD")
    return 'USD'  # Default to USD for global compatibility


def save_currency_metadata(user_id: str, currency: str, storage_base: Path):
    """Save detected currency to user metadata."""
    meta_path = storage_base / user_id / "metadata.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {}
    if meta_path.exists():
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
        except:
            pass
    
    metadata['currency'] = currency
    metadata['updated_at'] = pd.Timestamp.now().isoformat()
    
    with open(meta_path, 'w') as f:
        json.dump(metadata, f)


def load_currency_metadata(user_id: str, storage_base: Path) -> Optional[str]:
    """Load stored currency from user metadata."""
    meta_path = storage_base / user_id / "metadata.json"
    
    if meta_path.exists():
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
                return metadata.get('currency')
        except:
            pass
    
    return None


# ============================================================================
# MULTI-CURRENCY SUPPORT - Exchange Rates and Breakdown
# ============================================================================

# Exchange rates to USD (approximate rates - should be updated for production)
# Last updated: December 2024
EXCHANGE_RATES_TO_USD = {
    'USD': 1.0,
    'EUR': 1.05,      # 1 EUR = 1.05 USD
    'GBP': 1.27,      # 1 GBP = 1.27 USD
    'INR': 0.012,     # 1 INR = 0.012 USD (1 USD = ~83 INR)
    'JPY': 0.0067,    # 1 JPY = 0.0067 USD (1 USD = ~149 JPY)
    'AUD': 0.65,      # 1 AUD = 0.65 USD
    'CAD': 0.74,      # 1 CAD = 0.74 USD
    'CHF': 1.13,      # 1 CHF = 1.13 USD
    'CNY': 0.14,      # 1 CNY = 0.14 USD
    'SGD': 0.74,      # 1 SGD = 0.74 USD
}


def convert_to_usd(amount: float, from_currency: str) -> float:
    """
    Convert amount from any supported currency to USD.
    
    Args:
        amount: Amount in source currency
        from_currency: Source currency code (e.g., 'INR', 'EUR')
        
    Returns:
        Amount in USD
    """
    rate = EXCHANGE_RATES_TO_USD.get(from_currency, 1.0)
    return round(amount * rate, 2)


def convert_from_usd(amount: float, to_currency: str) -> float:
    """
    Convert amount from USD to any supported currency.
    
    Args:
        amount: Amount in USD
        to_currency: Target currency code
        
    Returns:
        Amount in target currency
    """
    rate = EXCHANGE_RATES_TO_USD.get(to_currency, 1.0)
    if rate == 0:
        return 0.0
    return round(amount / rate, 2)


def get_exchange_rate(from_currency: str, to_currency: str = 'USD') -> float:
    """Get exchange rate between two currencies."""
    from_rate = EXCHANGE_RATES_TO_USD.get(from_currency, 1.0)
    to_rate = EXCHANGE_RATES_TO_USD.get(to_currency, 1.0)
    
    if to_rate == 0:
        return 0.0
    return from_rate / to_rate


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Convert amount between any two supported currencies.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        
    Returns:
        Converted amount
    """
    if from_currency == to_currency:
        return amount
        
    # Convert to USD first (base currency)
    usd_amount = convert_to_usd(amount, from_currency)
    
    # Then convert from USD to target
    return convert_from_usd(usd_amount, to_currency)


def calculate_currency_breakdown(amounts_by_currency: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate multi-currency breakdown with USD equivalent.
    
    Args:
        amounts_by_currency: Dict mapping currency codes to total amounts
                            e.g., {'INR': 1000000, 'USD': 5000}
    
    Returns:
        Dict with breakdown and USD equivalent:
        {
            'breakdown': [
                {'currency': 'INR', 'amount': 1000000, 'symbol': '₹', 'formatted': '₹10,00,000', 'usd_equivalent': 12000},
                {'currency': 'USD', 'amount': 5000, 'symbol': '$', 'formatted': '$5,000', 'usd_equivalent': 5000}
            ],
            'total_usd_equivalent': 17000,
            'primary_currency': 'INR',  # Currency with highest original amount
            'currencies_count': 2
        }
    """
    breakdown = []
    total_usd = 0.0
    primary_currency = 'USD'
    max_amount = 0
    
    for currency, amount in amounts_by_currency.items():
        if amount <= 0:
            continue
            
        symbol = get_currency_symbol(currency)
        formatted = format_currency(amount, currency)
        usd_equivalent = convert_to_usd(amount, currency)
        
        breakdown.append({
            'currency': currency,
            'amount': round(amount, 2),
            'symbol': symbol,
            'formatted': formatted,
            'usd_equivalent': round(usd_equivalent, 2),
            'name': CURRENCY_CONFIG.get(currency, {}).get('name', currency)
        })
        
        total_usd += usd_equivalent
        
        # Track primary currency (highest amount in original currency)
        if amount > max_amount:
            max_amount = amount
            primary_currency = currency
    
    # Sort breakdown by USD equivalent (highest first)
    breakdown.sort(key=lambda x: x['usd_equivalent'], reverse=True)
    
    return {
        'breakdown': breakdown,
        'total_usd_equivalent': round(total_usd, 2),
        'total_usd_formatted': format_currency(total_usd, 'USD'),
        'primary_currency': primary_currency,
        'currencies_count': len(breakdown)
    }


def detect_currency_from_amount_string(value: str) -> tuple:
    """
    Extract currency and numeric amount from a string like '$100.50' or '₹1,234'.
    
    Args:
        value: String containing currency symbol and amount
        
    Returns:
        Tuple of (numeric_amount, currency_code)
    """
    if not isinstance(value, str):
        try:
            return (float(value), 'USD')
        except:
            return (0.0, 'USD')
    
    value = value.strip()
    
    # Detect currency
    currency = detect_currency_from_value(value)
    if not currency:
        currency = 'USD'
    
    # Extract numeric value
    clean = re.sub(r'[₹$€£¥A$C$S$CHF\s,]', '', value)
    clean = clean.replace(' ', '')
    
    try:
        amount = float(clean)
    except:
        amount = 0.0
    
    return (amount, currency)
