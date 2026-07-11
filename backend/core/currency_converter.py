# Currency Conversion Utility
"""
Multi-Currency Conversion System

Features:
- 40+ supported currencies
- Exchange rates (updated periodically)
- Auto-detection of currency from data
- Conversion to user's preferred currency

Usage:
    from core.currency_converter import convert_currency, get_currency_symbol
    
    # Convert amount
    usd_amount = convert_currency(1000, "INR", "USD")
    
    # Get symbol
    symbol = get_currency_symbol("INR")  # Returns "₹"
"""

from typing import Optional, Dict, Tuple
from datetime import datetime


# Currency symbols and codes
CURRENCY_INFO: Dict[str, dict] = {
    # Major Currencies
    "USD": {"symbol": "$", "name": "US Dollar", "region": "Americas"},
    "EUR": {"symbol": "€", "name": "Euro", "region": "Europe"},
    "GBP": {"symbol": "£", "name": "British Pound", "region": "Europe"},
    "JPY": {"symbol": "¥", "name": "Japanese Yen", "region": "Asia"},
    "CHF": {"symbol": "Fr", "name": "Swiss Franc", "region": "Europe"},
    "CAD": {"symbol": "C$", "name": "Canadian Dollar", "region": "Americas"},
    "AUD": {"symbol": "A$", "name": "Australian Dollar", "region": "Oceania"},
    
    # Asian Currencies
    "INR": {"symbol": "₹", "name": "Indian Rupee", "region": "Asia"},
    "CNY": {"symbol": "¥", "name": "Chinese Yuan", "region": "Asia"},
    "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar", "region": "Asia"},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar", "region": "Asia"},
    "KRW": {"symbol": "₩", "name": "South Korean Won", "region": "Asia"},
    "THB": {"symbol": "฿", "name": "Thai Baht", "region": "Asia"},
    "MYR": {"symbol": "RM", "name": "Malaysian Ringgit", "region": "Asia"},
    "IDR": {"symbol": "Rp", "name": "Indonesian Rupiah", "region": "Asia"},
    "PHP": {"symbol": "₱", "name": "Philippine Peso", "region": "Asia"},
    "VND": {"symbol": "₫", "name": "Vietnamese Dong", "region": "Asia"},
    "BDT": {"symbol": "৳", "name": "Bangladeshi Taka", "region": "Asia"},
    "PKR": {"symbol": "₨", "name": "Pakistani Rupee", "region": "Asia"},
    
    # Middle East & Africa
    "AED": {"symbol": "د.إ", "name": "UAE Dirham", "region": "Middle East"},
    "SAR": {"symbol": "﷼", "name": "Saudi Riyal", "region": "Middle East"},
    "ZAR": {"symbol": "R", "name": "South African Rand", "region": "Africa"},
    "EGP": {"symbol": "E£", "name": "Egyptian Pound", "region": "Africa"},
    "NGN": {"symbol": "₦", "name": "Nigerian Naira", "region": "Africa"},
    
    # Americas
    "BRL": {"symbol": "R$", "name": "Brazilian Real", "region": "Americas"},
    "MXN": {"symbol": "Mex$", "name": "Mexican Peso", "region": "Americas"},
    "ARS": {"symbol": "AR$", "name": "Argentine Peso", "region": "Americas"},
    "CLP": {"symbol": "CLP$", "name": "Chilean Peso", "region": "Americas"},
    "COP": {"symbol": "COL$", "name": "Colombian Peso", "region": "Americas"},
    
    # Europe
    "SEK": {"symbol": "kr", "name": "Swedish Krona", "region": "Europe"},
    "NOK": {"symbol": "kr", "name": "Norwegian Krone", "region": "Europe"},
    "DKK": {"symbol": "kr", "name": "Danish Krone", "region": "Europe"},
    "PLN": {"symbol": "zł", "name": "Polish Zloty", "region": "Europe"},
    "CZK": {"symbol": "Kč", "name": "Czech Koruna", "region": "Europe"},
    "RUB": {"symbol": "₽", "name": "Russian Ruble", "region": "Europe"},
    "TRY": {"symbol": "₺", "name": "Turkish Lira", "region": "Europe"},
    
    # Oceania
    "NZD": {"symbol": "NZ$", "name": "New Zealand Dollar", "region": "Oceania"},
}

# Exchange rates to USD (updated Dec 2024, approximate values)
# These are approximate and should be updated via API for production
RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.05,    # 1 EUR = 1.05 USD
    "GBP": 1.27,    # 1 GBP = 1.27 USD
    "JPY": 0.0067,  # 1 JPY = 0.0067 USD
    "CHF": 1.13,    # 1 CHF = 1.13 USD
    "CAD": 0.74,    # 1 CAD = 0.74 USD
    "AUD": 0.65,    # 1 AUD = 0.65 USD
    
    "INR": 0.01136,  # 1 INR = 0.01136 USD (₹88 = $1 - Dec 2024)
    "CNY": 0.14,    # 1 CNY = 0.14 USD
    "HKD": 0.13,    # 1 HKD = 0.13 USD
    "SGD": 0.74,    # 1 SGD = 0.74 USD
    "KRW": 0.00072, # 1 KRW = 0.00072 USD
    "THB": 0.028,   # 1 THB = 0.028 USD
    "MYR": 0.21,    # 1 MYR = 0.21 USD
    "IDR": 0.000062,# 1 IDR = 0.000062 USD
    "PHP": 0.017,   # 1 PHP = 0.017 USD
    "VND": 0.000039,# 1 VND = 0.000039 USD
    "BDT": 0.0083,  # 1 BDT = 0.0083 USD
    "PKR": 0.0036,  # 1 PKR = 0.0036 USD
    
    "AED": 0.27,    # 1 AED = 0.27 USD
    "SAR": 0.27,    # 1 SAR = 0.27 USD
    "ZAR": 0.054,   # 1 ZAR = 0.054 USD
    "EGP": 0.020,   # 1 EGP = 0.020 USD
    "NGN": 0.00062, # 1 NGN = 0.00062 USD
    
    "BRL": 0.17,    # 1 BRL = 0.17 USD
    "MXN": 0.049,   # 1 MXN = 0.049 USD
    "ARS": 0.00098, # 1 ARS = 0.00098 USD
    "CLP": 0.00099, # 1 CLP = 0.00099 USD
    "COP": 0.00023, # 1 COP = 0.00023 USD
    
    "SEK": 0.091,   # 1 SEK = 0.091 USD
    "NOK": 0.089,   # 1 NOK = 0.089 USD
    "DKK": 0.14,    # 1 DKK = 0.14 USD
    "PLN": 0.24,    # 1 PLN = 0.24 USD
    "CZK": 0.042,   # 1 CZK = 0.042 USD
    "RUB": 0.010,   # 1 RUB = 0.010 USD
    "TRY": 0.029,   # 1 TRY = 0.029 USD
    
    "NZD": 0.59,    # 1 NZD = 0.59 USD
}


def get_currency_symbol(currency_code: str) -> str:
    """Get the symbol for a currency code"""
    info = CURRENCY_INFO.get(currency_code.upper(), {})
    return info.get("symbol", currency_code)


def get_currency_name(currency_code: str) -> str:
    """Get the full name for a currency code"""
    info = CURRENCY_INFO.get(currency_code.upper(), {})
    return info.get("name", currency_code)


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> float:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: The amount to convert
        from_currency: Source currency code (e.g., "INR")
        to_currency: Target currency code (e.g., "USD")
        
    Returns:
        Converted amount in target currency
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # If same currency, return as-is
    if from_currency == to_currency:
        return amount
    
    # Get rates
    from_rate = RATES_TO_USD.get(from_currency, 1.0)
    to_rate = RATES_TO_USD.get(to_currency, 1.0)
    
    # Convert: source -> USD -> target
    usd_amount = amount * from_rate
    target_amount = usd_amount / to_rate
    
    return target_amount


def format_currency(amount: float, currency_code: str, decimal_places: int = 2) -> str:
    """
    Format an amount with the appropriate currency symbol.
    
    Args:
        amount: The amount to format
        currency_code: Currency code (e.g., "INR")
        decimal_places: Number of decimal places
        
    Returns:
        Formatted string like "₹1,234.56"
    """
    symbol = get_currency_symbol(currency_code)
    
    # Format with thousands separator
    if abs(amount) >= 10000000:  # 1 crore+
        formatted = f"{amount/10000000:,.2f} Cr"
    elif abs(amount) >= 100000:  # 1 lakh+
        formatted = f"{amount/100000:,.2f} L"
    else:
        formatted = f"{amount:,.{decimal_places}f}"
    
    return f"{symbol}{formatted}"


def detect_currency_from_text(text: str) -> Optional[str]:
    """
    Detect currency from text containing currency symbols or codes.
    
    Args:
        text: Text that may contain currency indicators
        
    Returns:
        Detected currency code or None
    """
    text_upper = text.upper()
    
    # Check for currency codes
    for code in CURRENCY_INFO.keys():
        if code in text_upper:
            return code
    
    # Check for symbols
    symbol_map = {
        "₹": "INR", "RS": "INR", "RS.": "INR", "INR": "INR",
        "$": "USD", "USD": "USD",
        "€": "EUR", "EUR": "EUR",
        "£": "GBP", "GBP": "GBP",
        "¥": "JPY",  # Could be JPY or CNY
        "₩": "KRW",
        "฿": "THB",
        "₱": "PHP",
        "₫": "VND",
        "৳": "BDT",
        "₨": "PKR",
        "₦": "NGN",
        "₽": "RUB",
        "₺": "TRY",
    }
    
    for symbol, code in symbol_map.items():
        if symbol in text:
            return code
    
    return None


import pandas as pd
def convert_dataframe_currency(
    df, 
    amount_column: str, 
    target_currency: str,
    source_currency: Optional[str] = None,
    currency_column: Optional[str] = None
) -> 'pd.DataFrame':
    """
    Convert a DataFrame's amount column to target currency.
    
    Args:
        df: DataFrame with amounts
        amount_column: Column name containing amounts
        target_currency: Currency to convert to
        source_currency: Source currency (if uniform)
        currency_column: Column containing per-row currency codes
        
    Returns:
        DataFrame with converted amounts
    """
    import pandas as pd
    
    df = df.copy()
    
    if currency_column and currency_column in df.columns:
        # Per-row conversion
        df[f'{amount_column}_converted'] = df.apply(
            lambda row: convert_currency(
                row[amount_column],
                row[currency_column],
                target_currency
            ),
            axis=1
        )
        df[f'{amount_column}_currency'] = target_currency
    elif source_currency:
        # Uniform conversion
        df[f'{amount_column}_converted'] = df[amount_column].apply(
            lambda x: convert_currency(x, source_currency, target_currency)
        )
        df[f'{amount_column}_currency'] = target_currency
    else:
        # No conversion, just copy
        df[f'{amount_column}_converted'] = df[amount_column]
        df[f'{amount_column}_currency'] = target_currency
    
    return df


def get_all_currencies() -> list:
    """Get list of all supported currencies"""
    return [
        {
            "code": code,
            "symbol": info["symbol"],
            "name": info["name"],
            "region": info["region"]
        }
        for code, info in CURRENCY_INFO.items()
    ]


# Quick test
if __name__ == "__main__":
    # Test conversions
    print(f"100 USD = {convert_currency(100, 'USD', 'INR'):.2f} INR")
    print(f"10000 INR = {convert_currency(10000, 'INR', 'USD'):.2f} USD")
    print(f"100 EUR = {convert_currency(100, 'EUR', 'INR'):.2f} INR")
    
    # Test formatting
    print(f"Formatted: {format_currency(5000000, 'INR')}")
    print(f"Formatted: {format_currency(50000, 'USD')}")
    
    # Test detection
    print(f"Detected: {detect_currency_from_text('Price: ₹1,234')}")
    print(f"Detected: {detect_currency_from_text('Amount: $500')}")
