"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mock environment variables before importing app modules
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-key")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture
def mock_settings():
    """Mock settings for tests"""
    from config.settings import Settings
    return Settings


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    storage = tmp_path / "storage" / "users"
    storage.mkdir(parents=True)
    return storage


@pytest.fixture
def sample_user_id():
    """Sample user ID for tests"""
    return "test-user-123"


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing"""
    import pandas as pd
    return pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'product': ['Widget A', 'Widget B', 'Widget C'],
        'revenue': [1000.50, 2500.75, 1750.25],
        'quantity': [10, 25, 15],
        'customer': ['Customer 1', 'Customer 2', 'Customer 1']
    })


@pytest.fixture
def sample_inr_dataframe():
    """Sample DataFrame with INR currency"""
    import pandas as pd
    return pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'product': ['Widget A', 'Widget B', 'Widget C'],
        'amount': ['₹10,000', '₹25,000', '₹17,500'],
        'quantity': [10, 25, 15]
    })


@pytest.fixture
def sample_usd_dataframe():
    """Sample DataFrame with USD currency"""
    import pandas as pd
    return pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'product': ['Widget A', 'Widget B', 'Widget C'],
        'price_usd': [100.50, 250.75, 175.25],
        'quantity': [10, 25, 15]
    })


@pytest.fixture
def mock_llm_response():
    """Mock LLM response"""
    return {
        "content": "Based on the data analysis, total revenue is $5,251.50 with Widget B being the top performer.",
        "model": "test-model",
        "tokens": 150
    }
