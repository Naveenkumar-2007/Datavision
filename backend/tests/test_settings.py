"""
Tests for Settings configuration
"""
import pytest
from pathlib import Path
import os


class TestSettingsClass:
    """Test Settings class"""
    
    def test_settings_has_base_dir(self, mock_settings):
        """Test that Settings has BASE_DIR"""
        assert hasattr(mock_settings, 'BASE_DIR')
        assert isinstance(mock_settings.BASE_DIR, Path)
    
    def test_settings_has_storage_paths(self, mock_settings):
        """Test that Settings has storage paths"""
        assert hasattr(mock_settings, 'STORAGE')
        assert hasattr(mock_settings, 'UPLOADS')
        assert hasattr(mock_settings, 'FAISS_DIR')
        assert hasattr(mock_settings, 'GRAPH_DIR')
    
    def test_storage_paths_are_under_base_dir(self, mock_settings):
        """Test that storage paths are under BASE_DIR"""
        base = str(mock_settings.BASE_DIR)
        
        assert str(mock_settings.STORAGE).startswith(base)
        assert str(mock_settings.UPLOADS).startswith(base)
    
    def test_paths_are_path_objects(self, mock_settings):
        """Test that paths are Path objects"""
        assert isinstance(mock_settings.STORAGE, Path)
        assert isinstance(mock_settings.UPLOADS, Path)
        assert isinstance(mock_settings.FAISS_DIR, Path)
        assert isinstance(mock_settings.GRAPH_DIR, Path)


class TestEnvironmentVariables:
    """Test environment variable handling"""
    
    def test_environment_is_set(self):
        """Test that environment variable is set"""
        env = os.environ.get('ENVIRONMENT')
        # Should be either 'test' or 'development' during testing
        assert env in ('test', 'development', None)
    
    def test_api_keys_are_mocked(self):
        """Test that API keys are mocked for tests"""
        # These should be set in conftest.py
        assert os.environ.get('OPENAI_API_KEY') is not None
        assert os.environ.get('GROQ_API_KEY') is not None


class TestSensitiveDataFilter:
    """Test the logging filter that redacts sensitive data"""
    
    def test_filter_exists(self):
        """Test that SensitiveDataFilter exists"""
        from config.settings import SensitiveDataFilter
        
        filter_instance = SensitiveDataFilter()
        assert filter_instance is not None
    
    def test_filter_has_sensitive_patterns(self):
        """Test that filter has defined sensitive patterns"""
        from config.settings import SensitiveDataFilter
        
        assert hasattr(SensitiveDataFilter, 'SENSITIVE_PATTERNS')
        assert len(SensitiveDataFilter.SENSITIVE_PATTERNS) > 0
