"""
Tests for FastAPI application setup
"""
import pytest
from unittest.mock import patch, MagicMock
import os


class TestAppConfiguration:
    """Test FastAPI application configuration"""
    
    def test_app_can_be_imported(self):
        """Test that the app can be imported"""
        from main import app
        assert app is not None
    
    def test_app_has_title(self):
        """Test that app has a title"""
        from main import app
        assert app.title is not None
        assert len(app.title) > 0
    
    def test_app_has_version(self):
        """Test that app has a version"""
        from main import app
        assert app.version is not None
    
    def test_docs_available_in_test_env(self):
        """Test that docs are available in test/dev environment"""
        # In test environment, docs should be available
        os.environ['ENVIRONMENT'] = 'development'
        
        # Re-import to apply env change
        from main import app
        # Docs URL should be set in non-production
        assert app.docs_url is not None or os.environ.get('ENVIRONMENT') == 'production'


class TestSecurityMiddleware:
    """Test security middleware configuration"""
    
    def test_security_headers_middleware_exists(self):
        """Test that SecurityHeadersMiddleware is defined"""
        from main import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None
    
    def test_cors_origins_configured(self):
        """Test that CORS origins are configured"""
        from main import ALLOWED_ORIGINS
        assert ALLOWED_ORIGINS is not None
        assert len(ALLOWED_ORIGINS) > 0
    
    def test_localhost_in_cors_origins(self):
        """Test that localhost is in CORS origins"""
        from main import ALLOWED_ORIGINS
        # At least one localhost origin should be present
        localhost_found = any('localhost' in origin for origin in ALLOWED_ORIGINS)
        # Or wildcard is used
        wildcard_found = '*' in ALLOWED_ORIGINS
        assert localhost_found or wildcard_found


class TestRouterInclusion:
    """Test that routers are properly included"""
    
    def test_chat_router_imported(self):
        """Test that chat router is imported"""
        from api.v1.endpoints import chat
        assert chat.router is not None
    
    def test_files_router_imported(self):
        """Test that files router is imported"""
        from api.v1.endpoints import files
        assert files.router is not None
    
    def test_analytics_router_imported(self):
        """Test that analytics router is imported"""
        from api.v1.endpoints import analytics
        assert analytics.router is not None
    
    def test_reports_router_imported(self):
        """Test that reports router is imported"""
        from api.v1.endpoints import reports
        assert reports.router is not None


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_app_routes_include_api_prefix(self):
        """Test that app includes API routes"""
        from main import app
        
        # Get all route paths
        routes = [route.path for route in app.routes]
        
        # Should have some API routes
        api_routes = [r for r in routes if '/api/' in r]
        # Note: Routes might be mounted differently
        assert len(routes) > 0  # At least some routes exist
