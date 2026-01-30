"""
Tests for Files API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import tempfile


class TestFileValidation:
    """Test file validation functions"""
    
    def test_sanitize_filename_removes_path_traversal(self):
        """Test that path traversal attempts are sanitized"""
        from api.v1.endpoints.files import sanitize_filename
        
        # Test path traversal attempts
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result
    
    def test_sanitize_filename_removes_null_bytes(self):
        """Test that null bytes are removed"""
        from api.v1.endpoints.files import sanitize_filename
        
        result = sanitize_filename("file\x00name.csv")
        assert "\x00" not in result
    
    def test_sanitize_filename_limits_length(self):
        """Test that long filenames are truncated"""
        from api.v1.endpoints.files import sanitize_filename
        
        long_name = "a" * 300 + ".csv"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".csv")
    
    def test_sanitize_filename_rejects_empty(self):
        """Test that empty filenames are rejected"""
        from api.v1.endpoints.files import sanitize_filename
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            sanitize_filename("")
        assert exc_info.value.status_code == 400
    
    def test_sanitize_filename_normal_file(self):
        """Test that normal filenames pass through"""
        from api.v1.endpoints.files import sanitize_filename
        
        result = sanitize_filename("my_data_file.csv")
        assert result == "my_data_file.csv"
    
    def test_validate_user_id_rejects_path_traversal(self):
        """Test that user ID validation rejects path traversal"""
        from api.v1.endpoints.files import validate_user_id
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_user_id("../admin")
        assert exc_info.value.status_code == 400
    
    def test_validate_user_id_accepts_valid_id(self):
        """Test that valid user IDs are accepted"""
        from api.v1.endpoints.files import validate_user_id
        
        result = validate_user_id("user-123-abc")
        assert result == "user-123-abc"
    
    def test_validate_user_id_accepts_uuid(self):
        """Test that UUID-style user IDs are accepted"""
        from api.v1.endpoints.files import validate_user_id
        
        result = validate_user_id("550e8400-e29b-41d4-a716-446655440000")
        # Should not raise - UUIDs contain hyphens which are allowed
        assert result is not None


class TestAllowedExtensions:
    """Test file extension validation"""
    
    def test_allowed_extensions_include_csv(self):
        """Test that CSV files are allowed"""
        from api.v1.endpoints.files import ALLOWED_EXTENSIONS
        
        assert '.csv' in ALLOWED_EXTENSIONS
    
    def test_allowed_extensions_include_excel(self):
        """Test that Excel files are allowed"""
        from api.v1.endpoints.files import ALLOWED_EXTENSIONS
        
        assert '.xlsx' in ALLOWED_EXTENSIONS
        assert '.xls' in ALLOWED_EXTENSIONS
    
    def test_allowed_extensions_include_json(self):
        """Test that JSON files are allowed"""
        from api.v1.endpoints.files import ALLOWED_EXTENSIONS
        
        assert '.json' in ALLOWED_EXTENSIONS
    
    def test_allowed_extensions_include_pdf(self):
        """Test that PDF files are allowed"""
        from api.v1.endpoints.files import ALLOWED_EXTENSIONS
        
        assert '.pdf' in ALLOWED_EXTENSIONS
    
    def test_allowed_extensions_include_images(self):
        """Test that image files are allowed"""
        from api.v1.endpoints.files import ALLOWED_EXTENSIONS
        
        assert '.png' in ALLOWED_EXTENSIONS
        assert '.jpg' in ALLOWED_EXTENSIONS
        assert '.jpeg' in ALLOWED_EXTENSIONS
    
    def test_dangerous_extensions_not_allowed(self):
        """Test that dangerous extensions are not allowed"""
        from api.v1.endpoints.files import ALLOWED_EXTENSIONS
        
        assert '.exe' not in ALLOWED_EXTENSIONS
        assert '.sh' not in ALLOWED_EXTENSIONS
        assert '.bat' not in ALLOWED_EXTENSIONS
        assert '.py' not in ALLOWED_EXTENSIONS
        assert '.js' not in ALLOWED_EXTENSIONS


class TestMaxFileSize:
    """Test file size limits"""
    
    def test_max_file_size_is_reasonable(self):
        """Test that max file size is set reasonably"""
        from api.v1.endpoints.files import MAX_FILE_SIZE
        
        # Should be at least 10MB
        assert MAX_FILE_SIZE >= 10 * 1024 * 1024
        # But not more than 500MB
        assert MAX_FILE_SIZE <= 500 * 1024 * 1024
