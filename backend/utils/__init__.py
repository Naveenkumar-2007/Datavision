# Backend utilities
from utils.paths import get_user_paths, STORAGE_BASE
from utils.currency import (
    detect_currency, 
    format_currency, 
    detect_and_save_user_currency,
    get_currency_symbol,
    load_currency_metadata,
    save_currency_metadata,
    CURRENCY_CONFIG,
    # Multi-currency support
    EXCHANGE_RATES_TO_USD,
    convert_to_usd,
    convert_from_usd,
    get_exchange_rate,
    calculate_currency_breakdown,
    detect_currency_from_amount_string
)

__all__ = [
    'get_user_paths', 
    'STORAGE_BASE', 
    'detect_currency', 
    'format_currency',
    'detect_and_save_user_currency',
    'get_currency_symbol',
    'load_currency_metadata',
    'save_currency_metadata',
    'CURRENCY_CONFIG',
    # Multi-currency support
    'EXCHANGE_RATES_TO_USD',
    'convert_to_usd',
    'convert_from_usd',
    'get_exchange_rate',
    'calculate_currency_breakdown',
    'detect_currency_from_amount_string'
]
