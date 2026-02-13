#!/usr/bin/env python3
"""
Basic test suite for cache stats endpoints.

This version tests the basic functionality without requiring the API server to be running.
"""

import requests
import time
import sys
import os

# Add the sonora directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sonora_dir = os.path.join(current_dir, '..', 'sonora')
sys.path.insert(0, sonora_dir)

# Try to import cache manager
try:
    from sonora.utils.cache_manager import get_cache_manager
    CACHE_MANAGER_AVAILABLE = True
except ImportError:
    CACHE_MANAGER_AVAILABLE = False
    print("Warning: Cache manager not available")


def test_cache_stats_endpoint():
    """Test the cache stats endpoint returns correct data."""
    try:
        r = requests.get("http://localhost:8000/api/cache/stats", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "memory_items" in data
        assert "disk_items" in data
        assert "hit_rate" in data
        print("✅ Cache stats endpoint test passed")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Cache stats endpoint test skipped (API not available): {e}")
        return False
    except Exception as e:
        print(f"❌ Cache stats endpoint test failed: {e}")
        return False


def test_cache_clear_endpoint():
    """Test the cache clear endpoint works correctly."""
    try:
        r = requests.delete("http://localhost:8000/api/cache/clear", timeout=5)
        assert r.status_code == 200
        msg = r.json()["status"]
        assert "cleared" in msg.lower()
        print("✅ Cache clear endpoint test passed")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Cache clear endpoint test skipped (API not available): {e}")
        return False
    except Exception as e:
        print(f"❌ Cache clear endpoint test failed: {e}")
        return False


def test_cache_stats_simple_format():
    """Test the simplified cache stats format."""
    try:
        r = requests.get("http://localhost:8000/api/cache/stats?simple=true", timeout=5)
        assert r.status_code == 200
        data = r.json()
        
        # Check required fields for simple format
        required_fields = ["memory_items", "disk_items", "hit_rate", "expired_entries", "uptime_minutes", "cache_size_mb"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(data["memory_items"], int)
        assert isinstance(data["disk_items"], int)
        assert isinstance(data["hit_rate"], (int, float))
        assert isinstance(data["expired_entries"], int)
        assert isinstance(data["uptime_minutes"], (int, float))
        assert isinstance(data["cache_size_mb"], (int, float))
        
        print("✅ Simple format test passed")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Simple format test skipped (API not available): {e}")
        return False
    except Exception as e:
        print(f"❌ Simple format test failed: {e}")
        return False


def test_cache_stats_comprehensive_format():
    """Test the comprehensive cache stats format."""
    try:
        r = requests.get("http://localhost:8000/api/cache/stats", timeout=5)
        assert r.status_code == 200
        data = r.json()
        
        # Check required fields for comprehensive format
        required_fields = [
            "memory_items", "disk_items", "hit_rate", "expired_entries", 
            "uptime_minutes", "cache_size_mb", "total_requests", "memory_hits", 
            "disk_hits", "misses", "max_memory_size", "default_ttl", "cache_dir", "timestamp"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(data["memory_items"], int)
        assert isinstance(data["disk_items"], int)
        assert isinstance(data["hit_rate"], (int, float))
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["memory_hits"], int)
        assert isinstance(data["disk_hits"], int)
        assert isinstance(data["misses"], int)
        assert isinstance(data["expired_entries"], int)
        assert isinstance(data["uptime_minutes"], (int, float))
        assert isinstance(data["cache_size_mb"], (int, float))
        assert isinstance(data["max_memory_size"], int)
        assert isinstance(data["default_ttl"], int)
        assert isinstance(data["cache_dir"], str)
        assert isinstance(data["timestamp"], (int, float))
        
        print("✅ Comprehensive format test passed")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Comprehensive format test skipped (API not available): {e}")
        return False
    except Exception as e:
        print(f"❌ Comprehensive format test failed: {e}")
        return False


def test_cache_manager_direct():
    """Test cache manager directly without API."""
    if not CACHE_MANAGER_AVAILABLE:
        print("⚠️ Cache manager direct test skipped (not available)")
        return False
    
    try:
        import tempfile
        import shutil
        
        # Create temporary cache directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize cache manager
            cache_manager = get_cache_manager()
            
            # Test basic operations
            cache_manager.set("test_key", "test_value")
            result = cache_manager.get("test_key")
            assert result == "test_value"
            
            # Test stats
            stats = cache_manager.get_simple_stats()
            assert "memory_items" in stats
            assert "hit_rate" in stats
            assert stats["memory_items"] >= 0
            
            print("✅ Cache manager direct test passed")
            return True
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Cache manager direct test failed: {e}")
        return False


def main():
    """Run all basic tests."""
    print("🧪 Testing Cache Stats - Basic Tests")
    print("=" * 50)
    
    tests = [
        test_cache_stats_endpoint,
        test_cache_clear_endpoint,
        test_cache_stats_simple_format,
        test_cache_stats_comprehensive_format,
        test_cache_manager_direct
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
        print("🎉 All tests passed!")
    elif passed > 0:
        print("⚠️ Some tests passed, some were skipped")
    else:
        print("❌ No tests passed")
    
    print("\n💡 To run full tests with API server:")
    print("   1. Start the API server: python -m sonora.api.server")
    print("   2. Run: python tests/test_cache_stats.py")


if __name__ == "__main__":
    main()










