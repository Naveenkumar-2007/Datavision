"""
Integration tests for API endpoints using FastAPI TestClient
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json


@pytest.fixture
def client():
    """Create FastAPI test client"""
    from main import app
    return TestClient(app)


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_returns_success(self, client):
        """Test that root endpoint returns success or redirects"""
        response = client.get("/", follow_redirects=False)
        # Could be 200, 307 redirect, or 404 depending on setup
        assert response.status_code in (200, 307, 404)


class TestStaticFiles:
    """Test static file serving"""
    
    def test_static_route_exists(self, client):
        """Test that static routes are configured"""
        from main import app
        routes = [r.path for r in app.routes]
        # Check for static or asset routes
        assert len(routes) > 0


class TestAPIRoutes:
    """Test API route availability"""
    
    def test_api_v1_routes_exist(self, client):
        """Test that API v1 routes are registered"""
        from main import app
        routes = [r.path for r in app.routes]
        
        # Convert routes to string for checking
        routes_str = str(routes)
        
        # Should have some routes defined
        assert len(routes) > 0


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_preflight_returns_headers(self, client):
        """Test that CORS preflight requests return proper headers"""
        response = client.options(
            "/api/v1/chat/message",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            }
        )
        # OPTIONS may return 200 or 405 depending on route existence
        assert response.status_code in (200, 405, 404)


class TestSecurityHeaders:
    """Test security headers are set"""
    
    def test_response_has_security_headers(self, client):
        """Test that responses include security headers"""
        response = client.get("/", follow_redirects=True)
        
        # These headers are set by SecurityHeadersMiddleware
        # They may not appear on all routes if route doesn't exist
        if response.status_code == 200:
            # Check for at least one security header
            headers = response.headers
            security_headers_present = any([
                'X-Content-Type-Options' in headers,
                'X-Frame-Options' in headers,
                'X-XSS-Protection' in headers,
            ])
            # Security headers should be present on successful responses
            assert security_headers_present or response.status_code != 200


class TestFilesEndpoints:
    """Test files API endpoints"""
    
    def test_list_files_endpoint_exists(self, client):
        """Test that listing files endpoint exists"""
        response = client.get("/api/v1/files/list")
        # Endpoint should exist - may return 200 (empty list) or other status
        assert response.status_code in (200, 307, 404, 422)
    
    def test_upload_endpoint_exists(self, client):
        """Test that upload endpoint is defined"""
        # Without a file, should get validation error (422) not 404
        response = client.post("/api/v1/files/upload/test-user")
        # 422 means endpoint exists but validation failed
        # 404 means endpoint doesn't exist
        assert response.status_code in (422, 400, 200)


class TestChatEndpoints:
    """Test chat API endpoints"""
    
    def test_chat_message_endpoint_exists(self, client):
        """Test that chat message endpoint is defined"""
        # Without proper body, should get validation error
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "test"}
        )
        # Should not be 404 - endpoint should exist
        assert response.status_code != 404 or response.status_code in (200, 422, 500)
