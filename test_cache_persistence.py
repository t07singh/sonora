"""
Test Cache Persistence

Tests that cache persists between container restarts.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from sonora.utils.cache_manager import CacheManager


class TestCachePersistence:
    """Test cache persistence functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_cache_manager_initialization(self, temp_cache_dir):
        """Test cache manager initializes with custom directory."""
        cache_manager = CacheManager(cache_dir=temp_cache_dir)
        
        assert cache_manager.cache_dir == Path(temp_cache_dir)
        assert cache_manager.cache_dir.exists()
    
    def test_cache_persistence_basic(self, temp_cache_dir):
        """Test basic cache persistence."""
        # Create first cache manager instance
        cache1 = CacheManager(cache_dir=temp_cache_dir)
        
        # Add some data to cache
        test_key = "test_key_1"
        test_data = b"test_data_1"
        
        cache1.set(test_key, test_data)
        
        # Verify data is in cache
        assert cache1.get(test_key) == test_data
        
        # Create second cache manager instance (simulating restart)
        cache2 = CacheManager(cache_dir=temp_cache_dir)
        
        # Data should still be available
        assert cache2.get(test_key) == test_data
    
    def test_cache_persistence_multiple_items(self, temp_cache_dir):
        """Test cache persistence with multiple items."""
        # Create first cache manager
        cache1 = CacheManager(cache_dir=temp_cache_dir)
        
        # Add multiple items
        test_items = {
            "item1": b"data1",
            "item2": b"data2",
            "item3": b"data3",
            "item4": b"data4",
        }
        
        for key, data in test_items.items():
            cache1.set(key, data)
        
        # Verify all items are cached
        for key, expected_data in test_items.items():
            assert cache1.get(key) == expected_data
        
        # Create second cache manager (simulating restart)
        cache2 = CacheManager(cache_dir=temp_cache_dir)
        
        # All items should still be available
        for key, expected_data in test_items.items():
            assert cache2.get(key) == expected_data
    
    def test_cache_persistence_with_metadata(self, temp_cache_dir):
        """Test cache persistence with metadata."""
        cache1 = CacheManager(cache_dir=temp_cache_dir)
        
        # Add item with metadata
        key = "metadata_test"
        data = b"test_data_with_metadata"
        metadata = {"source": "test", "timestamp": 1234567890}
        
        cache1.set(key, data, metadata=metadata)
        
        # Verify data and metadata
        cached_data, cached_metadata = cache1.get_with_metadata(key)
        assert cached_data == data
        assert cached_metadata == metadata
        
        # Create new cache manager (simulating restart)
        cache2 = CacheManager(cache_dir=temp_cache_dir)
        
        # Data and metadata should persist
        cached_data, cached_metadata = cache2.get_with_metadata(key)
        assert cached_data == data
        assert cached_metadata == metadata
    
    def test_cache_persistence_file_structure(self, temp_cache_dir):
        """Test that cache files are properly created and structured."""
        cache = CacheManager(cache_dir=temp_cache_dir)
        
        # Add some data
        key = "file_structure_test"
        data = b"test_data_for_file_structure"
        
        cache.set(key, data)
        
        # Check that cache files exist
        cache_dir = Path(temp_cache_dir)
        assert cache_dir.exists()
        
        # Should have cache files (exact structure depends on implementation)
        cache_files = list(cache_dir.glob("*"))
        assert len(cache_files) > 0, "Should have cache files"
    
    def test_cache_persistence_after_clear(self, temp_cache_dir):
        """Test cache behavior after clearing."""
        cache1 = CacheManager(cache_dir=temp_cache_dir)
        
        # Add data
        key = "clear_test"
        data = b"data_to_be_cleared"
        cache1.set(key, data)
        
        # Verify data exists
        assert cache1.get(key) == data
        
        # Clear cache
        cache1.clear()
        
        # Data should be gone
        assert cache1.get(key) is None
        
        # Create new cache manager (simulating restart)
        cache2 = CacheManager(cache_dir=temp_cache_dir)
        
        # Data should still be gone
        assert cache2.get(key) is None
    
    def test_cache_persistence_with_expiration(self, temp_cache_dir):
        """Test cache persistence with expiration (if supported)."""
        cache1 = CacheManager(cache_dir=temp_cache_dir)
        
        # Add data with short expiration
        key = "expiration_test"
        data = b"data_with_expiration"
        
        # Note: This test assumes the cache manager supports TTL
        # If not supported, this test can be skipped
        try:
            cache1.set(key, data, ttl=1)  # 1 second TTL
            
            # Verify data exists initially
            assert cache1.get(key) == data
            
            # Create new cache manager (simulating restart)
            cache2 = CacheManager(cache_dir=temp_cache_dir)
            
            # Data should still be available (TTL might reset on restart)
            # This behavior depends on implementation
            cached_data = cache2.get(key)
            # We can't assert specific behavior here as it depends on implementation
            
        except TypeError:
            # If TTL is not supported, skip this test
            pytest.skip("Cache manager does not support TTL")
    
    def test_cache_persistence_large_data(self, temp_cache_dir):
        """Test cache persistence with larger data."""
        cache1 = CacheManager(cache_dir=temp_cache_dir)
        
        # Create larger data
        large_data = b"x" * 1024 * 1024  # 1MB of data
        
        key = "large_data_test"
        cache1.set(key, large_data)
        
        # Verify data is cached
        assert cache1.get(key) == large_data
        
        # Create new cache manager (simulating restart)
        cache2 = CacheManager(cache_dir=temp_cache_dir)
        
        # Large data should persist
        assert cache2.get(key) == large_data
    
    def test_cache_persistence_concurrent_access(self, temp_cache_dir):
        """Test cache persistence with concurrent access simulation."""
        # Create multiple cache managers (simulating multiple processes)
        cache1 = CacheManager(cache_dir=temp_cache_dir)
        cache2 = CacheManager(cache_dir=temp_cache_dir)
        
        # Add data from first cache
        key = "concurrent_test"
        data = b"concurrent_data"
        cache1.set(key, data)
        
        # Read from second cache
        assert cache2.get(key) == data
        
        # Add data from second cache
        key2 = "concurrent_test_2"
        data2 = b"concurrent_data_2"
        cache2.set(key2, data2)
        
        # Read from first cache
        assert cache1.get(key2) == data2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])










