"""
Real-time Exchange Rate Service
Uses free exchange rate API with 1-hour caching
"""

import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Optional
import os


# Cache for exchange rates
_rate_cache: Dict = {
    "rates": {},
    "base": "USD",
    "last_updated": None
}

# Cache duration in hours
CACHE_DURATION_HOURS = 1


async def get_exchange_rates(base_currency: str = "USD") -> Dict[str, float]:
    """
    Fetch real-time exchange rates from free API
    Results are cached for 1 hour to minimize API calls
    
    Args:
        base_currency: Base currency code (default: USD)
        
    Returns:
        Dictionary of currency codes to exchange rates
    """
    global _rate_cache
    
    # Check if cache is valid
    if (
        _rate_cache["last_updated"] 
        and _rate_cache["base"] == base_currency
        and datetime.now() - _rate_cache["last_updated"] < timedelta(hours=CACHE_DURATION_HOURS)
    ):
        print(f"📊 Using cached exchange rates for {base_currency}")
        return _rate_cache["rates"]
    
    try:
        # Free API options (no API key required):
        # 1. exchangerate-api.com (free tier)
        # 2. open.er-api.com (free tier)
        
        async with aiohttp.ClientSession() as session:
            # Using open.er-api.com (no API key needed)
            url = f"https://open.er-api.com/v6/latest/{base_currency}"
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("result") == "success":
                        rates = data.get("rates", {})
                        
                        # Update cache
                        _rate_cache = {
                            "rates": rates,
                            "base": base_currency,
                            "last_updated": datetime.now()
                        }
                        
                        print(f"✅ Fetched fresh exchange rates for {base_currency}")
                        return rates
                    else:
                        print(f"⚠️ API returned error: {data.get('error-type')}")
                else:
                    print(f"⚠️ API returned status {response.status}")
                    
    except Exception as e:
        print(f"❌ Failed to fetch exchange rates: {e}")
    
    # Return fallback rates if API fails
    return get_fallback_rates(base_currency)


def get_fallback_rates(base: str = "USD") -> Dict[str, float]:
    """
    Fallback exchange rates when API is unavailable
    These are approximate rates and should be updated periodically
    """
    # Approximate rates as of Dec 2024
    usd_rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "INR": 84.50,
        "JPY": 154.0,
        "AUD": 1.54,
        "CAD": 1.42,
        "CHF": 0.88,
        "CNY": 7.24,
        "SGD": 1.35,
        "AED": 3.67,
        "SAR": 3.75,
    }
    
    if base == "USD":
        return usd_rates
    
    # Convert to requested base
    if base in usd_rates:
        base_rate = usd_rates[base]
        return {
            currency: rate / base_rate 
            for currency, rate in usd_rates.items()
        }
    
    return usd_rates


async def convert_currency(
    amount: float, 
    from_currency: str, 
    to_currency: str
) -> float:
    """
    Convert amount from one currency to another
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        
    Returns:
        Converted amount
    """
    if from_currency == to_currency:
        return amount
    
    rates = await get_exchange_rates(from_currency)
    rate = rates.get(to_currency, 1.0)
    
    return round(amount * rate, 2)


def get_cache_status() -> Dict:
    """Get current cache status for debugging"""
    return {
        "cached": _rate_cache["last_updated"] is not None,
        "base": _rate_cache["base"],
        "last_updated": _rate_cache["last_updated"].isoformat() if _rate_cache["last_updated"] else None,
        "rates_count": len(_rate_cache["rates"]),
        "cache_duration_hours": CACHE_DURATION_HOURS
    }


# Popular currency pairs for display
POPULAR_CURRENCIES = ["USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD", "CHF", "CNY", "SGD", "AED"]
