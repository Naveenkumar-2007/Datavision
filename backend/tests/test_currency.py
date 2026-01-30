"""
Tests for currency detection and formatting utilities
"""
import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile


class TestCurrencyConfig:
    """Test currency configuration constants"""
    
    def test_currency_config_has_all_currencies(self):
        """Test that all 10 supported currencies are configured"""
        from utils.currency import CURRENCY_CONFIG
        
        expected = ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SGD']
        assert sorted(CURRENCY_CONFIG.keys()) == sorted(expected)
    
    def test_currency_config_has_required_fields(self):
        """Test that each currency has symbol, name, locale, keywords"""
        from utils.currency import CURRENCY_CONFIG
        
        for code, config in CURRENCY_CONFIG.items():
            assert 'symbol' in config, f"{code} missing symbol"
            assert 'name' in config, f"{code} missing name"
            assert 'locale' in config, f"{code} missing locale"
            assert 'keywords' in config, f"{code} missing keywords"
    
    def test_currency_symbols(self):
        """Test common currency symbols"""
        from utils.currency import CURRENCY_CONFIG
        
        assert CURRENCY_CONFIG['USD']['symbol'] == '$'
        assert CURRENCY_CONFIG['EUR']['symbol'] == '€'
        assert CURRENCY_CONFIG['GBP']['symbol'] == '£'
        assert CURRENCY_CONFIG['INR']['symbol'] == '₹'
        assert CURRENCY_CONFIG['JPY']['symbol'] == '¥'


class TestCurrencyDetectionFromValue:
    """Test currency detection from value strings"""
    
    def test_detect_usd_from_dollar_sign(self):
        """Test USD detection from $ symbol"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('$100.50') == 'USD'
        assert detect_currency_from_value('$1,234.56') == 'USD'
    
    def test_detect_eur_from_euro_sign(self):
        """Test EUR detection from € symbol"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('€100.50') == 'EUR'
        assert detect_currency_from_value('100€') == 'EUR'
    
    def test_detect_gbp_from_pound_sign(self):
        """Test GBP detection from £ symbol"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('£100.50') == 'GBP'
    
    def test_detect_inr_from_rupee_sign(self):
        """Test INR detection from ₹ symbol"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('₹10,000') == 'INR'
        assert detect_currency_from_value('₹1,00,000') == 'INR'  # Indian format
    
    def test_detect_aud_from_a_dollar(self):
        """Test AUD detection from A$ symbol"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('A$100.50') == 'AUD'
    
    def test_detect_cad_from_c_dollar(self):
        """Test CAD detection from C$ symbol"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('C$100.50') == 'CAD'
    
    def test_detect_sgd_from_s_dollar(self):
        """Test SGD detection from S$ symbol"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('S$100.50') == 'SGD'
    
    def test_returns_none_for_no_currency(self):
        """Test that None is returned when no currency detected"""
        from utils.currency import detect_currency_from_value
        
        assert detect_currency_from_value('12345') is None
        assert detect_currency_from_value('hello') is None


class TestCurrencyDetectionFromColumnNames:
    """Test currency detection from column names"""
    
    def test_detect_usd_from_column_name(self):
        """Test USD detection from column names"""
        from utils.currency import detect_currency_from_column_names
        
        assert detect_currency_from_column_names(['price_usd', 'quantity']) == 'USD'
        assert detect_currency_from_column_names(['amount_dollar', 'date']) == 'USD'
    
    def test_detect_inr_from_column_name(self):
        """Test INR detection from column names"""
        from utils.currency import detect_currency_from_column_names
        
        assert detect_currency_from_column_names(['price_inr', 'quantity']) == 'INR'
        assert detect_currency_from_column_names(['amount_rupee', 'date']) == 'INR'
    
    def test_detect_eur_from_column_name(self):
        """Test EUR detection from column names"""
        from utils.currency import detect_currency_from_column_names
        
        assert detect_currency_from_column_names(['price_eur', 'quantity']) == 'EUR'
        assert detect_currency_from_column_names(['amount_euro', 'date']) == 'EUR'
    
    def test_returns_none_for_no_currency_column(self):
        """Test that None is returned when no currency in column names"""
        from utils.currency import detect_currency_from_column_names
        
        assert detect_currency_from_column_names(['price', 'quantity', 'date']) is None


class TestCurrencyDetectionFromFilename:
    """Test currency detection from filename"""
    
    def test_detect_inr_from_filename(self):
        """Test INR detection from filename"""
        from utils.currency import detect_currency_from_filename
        
        assert detect_currency_from_filename('sales_india_2025.csv') == 'INR'
        assert detect_currency_from_filename('revenue_inr.xlsx') == 'INR'
    
    def test_detect_usd_from_filename(self):
        """Test USD detection from filename"""
        from utils.currency import detect_currency_from_filename
        
        assert detect_currency_from_filename('sales_usd_report.csv') == 'USD'
    
    def test_returns_none_for_generic_filename(self):
        """Test that None is returned for generic filenames"""
        from utils.currency import detect_currency_from_filename
        
        assert detect_currency_from_filename('data.csv') is None
        assert detect_currency_from_filename('report.xlsx') is None


class TestFormatCurrency:
    """Test currency formatting"""
    
    def test_format_usd(self):
        """Test USD formatting"""
        from utils.currency import format_currency
        
        result = format_currency(1234.56, 'USD')
        assert '$' in result
        assert '1,234' in result or '1234' in result
    
    def test_format_inr(self):
        """Test INR formatting with Indian numbering"""
        from utils.currency import format_currency
        
        result = format_currency(100000, 'INR')
        assert '₹' in result
        # Indian format: 1,00,000
        assert '1,00,000' in result or '100,000' in result or '100000' in result
    
    def test_format_eur(self):
        """Test EUR formatting"""
        from utils.currency import format_currency
        
        result = format_currency(1234.56, 'EUR')
        assert '€' in result
    
    def test_format_large_number(self):
        """Test formatting large numbers"""
        from utils.currency import format_currency
        
        result = format_currency(1000000, 'USD')
        assert '$' in result
        assert '1' in result and '000' in result


class TestCurrencyConversion:
    """Test currency conversion functions"""
    
    def test_exchange_rates_exist(self):
        """Test that exchange rates are defined"""
        from utils.currency import EXCHANGE_RATES_TO_USD
        
        assert 'INR' in EXCHANGE_RATES_TO_USD
        assert 'EUR' in EXCHANGE_RATES_TO_USD
        assert 'GBP' in EXCHANGE_RATES_TO_USD
    
    def test_convert_to_usd(self):
        """Test conversion to USD"""
        from utils.currency import convert_to_usd, EXCHANGE_RATES_TO_USD
        
        # INR to USD - rate is how much 1 INR is worth in USD
        inr_rate = EXCHANGE_RATES_TO_USD.get('INR', 0.01136)
        result = convert_to_usd(10000, 'INR')
        expected = 10000 * inr_rate
        assert abs(result - expected) < 10  # Within $10 tolerance
    
    def test_convert_from_usd(self):
        """Test conversion from USD"""
        from utils.currency import convert_from_usd, EXCHANGE_RATES_TO_USD
        
        # USD to INR - rate is how much 1 INR is worth in USD
        # So 100 USD / 0.01136 = ~8803 INR
        inr_rate = EXCHANGE_RATES_TO_USD.get('INR', 0.01136)
        result = convert_from_usd(100, 'INR')
        expected = 100 / inr_rate
        assert abs(result - expected) < 100  # Within 100 INR tolerance
    
    def test_usd_to_usd_conversion(self):
        """Test USD to USD returns same value"""
        from utils.currency import convert_to_usd
        
        result = convert_to_usd(100, 'USD')
        assert result == 100


class TestDetectCurrency:
    """Test main detect_currency function"""
    
    def test_detect_from_dataframe_values(self, sample_inr_dataframe):
        """Test currency detection from DataFrame values"""
        from utils.currency import detect_currency
        
        result = detect_currency(df=sample_inr_dataframe)
        assert result == 'INR'
    
    def test_detect_from_column_names(self, sample_usd_dataframe):
        """Test currency detection from column names"""
        from utils.currency import detect_currency
        
        result = detect_currency(df=sample_usd_dataframe)
        assert result == 'USD'
    
    def test_default_to_usd(self):
        """Test default to USD when no currency detected"""
        from utils.currency import detect_currency
        import pandas as pd
        
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        result = detect_currency(df=df)
        assert result == 'USD'  # Default


class TestGetCurrencySymbol:
    """Test get_currency_symbol function"""
    
    def test_get_known_symbols(self):
        """Test getting symbols for known currencies"""
        from utils.currency import get_currency_symbol
        
        assert get_currency_symbol('USD') == '$'
        assert get_currency_symbol('EUR') == '€'
        assert get_currency_symbol('GBP') == '£'
        assert get_currency_symbol('INR') == '₹'
        assert get_currency_symbol('JPY') == '¥'
    
    def test_get_unknown_currency_returns_default(self):
        """Test unknown currency returns default"""
        from utils.currency import get_currency_symbol
        
        assert get_currency_symbol('XYZ') == '$'  # Default to USD
