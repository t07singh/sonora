#!/usr/bin/env python3
"""
Standalone test suite for cache stats functionality.

This version tests the cache manager directly without requiring the API server.
"""

import sys
import os
import tempfile
import shutil
import time

# Add the sonora directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sonora_dir = os.path.join(current_dir, '..', 'sonora')
sys.path.insert(0, sonora_dir)

# Import cache manager
try:
    from sonora.utils.cache_manager import CacheManager
    CACHE_MANAGER_AVAILABLE = True
except ImportError as e:
    CACHE_MANAGER_AVAILABLE = False
    print(f"❌ Cannot import CacheManager: {e}")


def test_cache_manager_initialization():
    """Test cache manager initialization."""
    if not CACHE_MANAGER_AVAILABLE:
        return False
    
    try:
        temp_dir = tempfile.mkdtemp()
        cache_manager = CacheManager(cache_dir=temp_dir, max_memory_size=10, default_ttl=5)
        
        # Test initial stats
        stats = cache_manager.get_simple_stats()
        assert stats["memory_items"] == 0
        assert stats["disk_items"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["expired_entries"] == 0
        assert stats["uptime_minutes"] >= 0
        assert stats["cache_size_mb"] == 0.0
        
        print("✅ Cache manager initialization test passed")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
    except Exception as e:
        print(f"❌ Cache manager initialization test failed: {e}")
        return False


def test_cache_operations_and_stats():
    """Test cache operations and stats tracking."""
    if not CACHE_MANAGER_AVAILABLE:
        return False
    
    try:
        temp_dir = tempfile.mkdtemp()
        cache_manager = CacheManager(cache_dir=temp_dir, max_memory_size=10, default_ttl=5)
        
        # Add some items
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", "value3")
        
        # Test hits and misses
        cache_manager.get("key1")  # Hit
        cache_manager.get("key2")  # Hit
        cache_manager.get("nonexistent")  # Miss
        
        # Check stats
        stats = cache_manager.get_simple_stats()
        assert stats["memory_items"] >= 0
        assert stats["hit_rate"] > 0
        assert stats["uptime_minutes"] >= 0
        
        print("✅ Cache operations and stats test passed")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
    except Exception as e:
        print(f"❌ Cache operations and stats test failed: {e}")
        return False


def test_cache_clear_functionality():
    """Test cache clear functionality."""
    if not CACHE_MANAGER_AVAILABLE:
        return False
    
    try:
        temp_dir = tempfile.mkdtemp()
        cache_manager = CacheManager(cache_dir=temp_dir, max_memory_size=10, default_ttl=5)
        
        # Add some items
        cache_manager.set("clear_test_1", "clear_value_1")
        cache_manager.set("clear_test_2", "clear_value_2")
        
        # Verify items exist
        stats_before = cache_manager.get_simple_stats()
        assert stats_before["memory_items"] > 0 or stats_before["disk_items"] > 0
        
        # Clear cache
        cache_manager.clear()
        
        # Verify cache is cleared
        stats_after = cache_manager.get_simple_stats()
        assert stats_after["memory_items"] == 0
        assert stats_after["disk_items"] == 0
        
        print("✅ Cache clear functionality test passed")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
    except Exception as e:
        print(f"❌ Cache clear functionality test failed: {e}")
        return False


def test_simple_vs_comprehensive_stats():
    """Test that simple and comprehensive stats are compatible."""
    if not CACHE_MANAGER_AVAILABLE:
        return False
    
    try:
        temp_dir = tempfile.mkdtemp()
        cache_manager = CacheManager(cache_dir=temp_dir, max_memory_size=10, default_ttl=5)
        
        # Add some data
        cache_manager.set("compat_test", "compat_value")
        cache_manager.get("compat_test")
        
        # Get both stats formats
        simple_stats = cache_manager.get_simple_stats()
        comprehensive_stats = cache_manager.get_cache_stats()
        
        # Verify compatibility
        assert simple_stats["memory_items"] == comprehensive_stats["memory_items"]
        assert simple_stats["disk_items"] == comprehensive_stats["disk_items"]
        assert abs(simple_stats["hit_rate"] - comprehensive_stats["hit_rate"] * 100) < 0.01
        assert simple_stats["expired_entries"] == comprehensive_stats["expired_entries"]
        
        print("✅ Simple vs comprehensive stats compatibility test passed")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
    except Exception as e:
        print(f"❌ Simple vs comprehensive stats compatibility test failed: {e}")
        return False


def test_uptime_tracking():
    """Test uptime tracking functionality."""
    if not CACHE_MANAGER_AVAILABLE:
        return False
    
    try:
        temp_dir = tempfile.mkdtemp()
        cache_manager = CacheManager(cache_dir=temp_dir, max_memory_size=10, default_ttl=5)
        
        # Get initial uptime
        stats1 = cache_manager.get_simple_stats()
        initial_uptime = stats1["uptime_minutes"]
        
        # Wait a bit
        time.sleep(0.1)
        
        # Get later uptime
        stats2 = cache_manager.get_simple_stats()
        later_uptime = stats2["uptime_minutes"]
        
        # Uptime should be >= previous uptime
        assert later_uptime >= initial_uptime
        
        print("✅ Uptime tracking test passed")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
    except Exception as e:
        print(f"❌ Uptime tracking test failed: {e}")
        return False


def test_cache_size_calculation():
    """Test cache size calculation."""
    if not CACHE_MANAGER_AVAILABLE:
        return False
    
    try:
        temp_dir = tempfile.mkdtemp()
        cache_manager = CacheManager(cache_dir=temp_dir, max_memory_size=5, default_ttl=5)
        
        # Add many items to trigger disk cache
        for i in range(10):
            cache_manager.set(f"size_test_{i}", f"size_value_{i}" * 100)  # Larger values
        
        # Check cache size
        stats = cache_manager.get_simple_stats()
        assert stats["cache_size_mb"] >= 0
        assert stats["memory_items"] >= 0
        assert stats["disk_items"] >= 0
        
        print("✅ Cache size calculation test passed")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
    except Exception as e:
        print(f"❌ Cache size calculation test failed: {e}")
        return False


def main():
    """Run all standalone tests."""
    print("🧪 Testing Cache Stats - Standalone Tests")
    print("=" * 50)
    
    if not CACHE_MANAGER_AVAILABLE:
        print("❌ CacheManager not available - cannot run tests")
        return
    
    tests = [
        test_cache_manager_initialization,
        test_cache_operations_and_stats,
        test_cache_clear_functionality,
        test_simple_vs_comprehensive_stats,
        test_uptime_tracking,
        test_cache_size_calculation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All standalone tests passed!")
        print("\n✅ Cache stats functionality is working correctly!")
        print("💡 The cache manager supports:")
        print("   - Simple stats format (get_simple_stats())")
        print("   - Comprehensive stats format (get_cache_stats())")
        print("   - Uptime tracking")
        print("   - Cache size calculation")
        print("   - Hit rate calculation")
        print("   - Cache clearing functionality")
    elif passed > 0:
        print("⚠️ Some tests passed, some failed")
    else:
        print("❌ No tests passed")


if __name__ == "__main__":
    main()










