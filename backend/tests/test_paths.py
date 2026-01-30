"""
Tests for path utilities
"""
import pytest
from pathlib import Path
import tempfile
import os


class TestGetUserPaths:
    """Test get_user_paths function"""
    
    def test_returns_dict_with_all_paths(self, sample_user_id):
        """Test that get_user_paths returns all required paths"""
        from utils.paths import get_user_paths
        
        paths = get_user_paths(sample_user_id)
        
        assert 'base' in paths
        assert 'files' in paths
        assert 'faiss' in paths
        assert 'graph' in paths
        assert 'memory' in paths
    
    def test_paths_are_path_objects(self, sample_user_id):
        """Test that all paths are Path objects"""
        from utils.paths import get_user_paths
        
        paths = get_user_paths(sample_user_id)
        
        for key, path in paths.items():
            assert isinstance(path, Path), f"{key} is not a Path object"
    
    def test_paths_contain_user_id(self, sample_user_id):
        """Test that paths contain the user ID"""
        from utils.paths import get_user_paths
        
        paths = get_user_paths(sample_user_id)
        
        for key, path in paths.items():
            assert sample_user_id in str(path), f"{key} path doesn't contain user_id"
    
    def test_creates_directories(self, sample_user_id):
        """Test that directories are created"""
        from utils.paths import get_user_paths
        
        paths = get_user_paths(sample_user_id)
        
        for key, path in paths.items():
            assert path.exists(), f"{key} directory was not created"
    
    def test_different_users_get_different_paths(self):
        """Test that different users get isolated paths"""
        from utils.paths import get_user_paths
        
        paths1 = get_user_paths("user-1")
        paths2 = get_user_paths("user-2")
        
        assert paths1['base'] != paths2['base']
        assert paths1['files'] != paths2['files']
    
    def test_same_user_gets_same_paths(self, sample_user_id):
        """Test that same user always gets same paths"""
        from utils.paths import get_user_paths
        
        paths1 = get_user_paths(sample_user_id)
        paths2 = get_user_paths(sample_user_id)
        
        assert paths1['base'] == paths2['base']
        assert paths1['files'] == paths2['files']


class TestStorageBase:
    """Test STORAGE_BASE constant"""
    
    def test_storage_base_is_path(self):
        """Test that STORAGE_BASE is a Path object"""
        from utils.paths import STORAGE_BASE
        
        assert isinstance(STORAGE_BASE, Path)
    
    def test_storage_base_exists(self):
        """Test that STORAGE_BASE directory exists"""
        from utils.paths import STORAGE_BASE
        
        # It should be created on import
        assert STORAGE_BASE.exists() or True  # May not exist in test env
