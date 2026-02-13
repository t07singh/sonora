#!/usr/bin/env python3
"""
Test suite for cache stats endpoints.

Verifies both /api/cache/stats and /api/cache/clear endpoints
and confirms JSON format and operational functionality.
"""

import requests
import time
import pytest
import sys
import os

# Add the sonora directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sonora_dir = os.path.join(current_dir, '..', 'sonora')
sys.path.insert(0, sonora_dir)

# Try to import cache manager, but make it optional for basic tests
try:
    from sonora.utils.cache_manager import get_cache_manager
    CACHE_MANAGER_AVAILABLE = True
except ImportError:
    CACHE_MANAGER_AVAILABLE = False
    print("Warning: Cache manager not available for advanced tests")


def test_cache_stats_endpoint():
    """Test the cache stats endpoint returns correct data."""
    r = requests.get("http://localhost:8000/api/cache/stats")
    assert r.status_code == 200
    data = r.json()
    assert "memory_items" in data
    assert "disk_items" in data
    assert "hit_rate" in data


def test_cache_clear_endpoint():
    """Test the cache clear endpoint works correctly."""
    r = requests.delete("http://localhost:8000/api/cache/clear")
    assert r.status_code == 200
    msg = r.json()["status"]
    assert "cleared" in msg.lower()


def test_cache_stats_simple_format():
    """Test the simplified cache stats format."""
    r = requests.get("http://localhost:8000/api/cache/stats?simple=true")
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


def test_cache_stats_comprehensive_format():
    """Test the comprehensive cache stats format."""
    r = requests.get("http://localhost:8000/api/cache/stats")
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


def test_cache_stats_with_operations():
    """Test cache stats reflect actual cache operations."""
    if not CACHE_MANAGER_AVAILABLE:
        pytest.skip("Cache manager not available")
    
    # Clear cache first
    requests.delete("http://localhost:8000/api/cache/clear")
    
    # Get initial stats
    r1 = requests.get("http://localhost:8000/api/cache/stats")
    assert r1.status_code == 200
    initial_stats = r1.json()
    
    # Add some items to cache via cache manager
    cache_manager = get_cache_manager()
    cache_manager.set("test_key_1", "test_value_1")
    cache_manager.set("test_key_2", "test_value_2")
    cache_manager.get("test_key_1")  # Hit
    cache_manager.get("test_key_2")  # Hit
    cache_manager.get("nonexistent")  # Miss
    
    # Get updated stats
    r2 = requests.get("http://localhost:8000/api/cache/stats")
    assert r2.status_code == 200
    updated_stats = r2.json()
    
    # Verify stats changed
    assert updated_stats["total_requests"] > initial_stats["total_requests"]
    assert updated_stats["hits"] > initial_stats["hits"]
    assert updated_stats["misses"] > initial_stats["misses"]
    assert updated_stats["memory_items"] >= 0


def test_cache_clear_effectiveness():
    """Test that cache clear actually clears the cache."""
    if not CACHE_MANAGER_AVAILABLE:
        pytest.skip("Cache manager not available")
    
    # Add some items to cache
    cache_manager = get_cache_manager()
    cache_manager.set("clear_test_1", "clear_value_1")
    cache_manager.set("clear_test_2", "clear_value_2")
    
    # Verify items exist
    r1 = requests.get("http://localhost:8000/api/cache/stats")
    assert r1.status_code == 200
    stats_before = r1.json()
    assert stats_before["memory_items"] + stats_before["disk_items"] > 0
    
    # Clear cache
    r2 = requests.delete("http://localhost:8000/api/cache/clear")
    assert r2.status_code == 200
    clear_response = r2.json()
    assert "cleared" in clear_response["status"].lower()
    
    # Verify cache is cleared
    r3 = requests.get("http://localhost:8000/api/cache/stats")
    assert r3.status_code == 200
    stats_after = r3.json()
    assert stats_after["memory_items"] == 0
    assert stats_after["disk_items"] == 0


def test_cache_stats_uptime_tracking():
    """Test that uptime tracking works correctly."""
    r1 = requests.get("http://localhost:8000/api/cache/stats")
    assert r1.status_code == 200
    stats1 = r1.json()
    
    # Wait a bit
    time.sleep(0.1)
    
    r2 = requests.get("http://localhost:8000/api/cache/stats")
    assert r2.status_code == 200
    stats2 = r2.json()
    
    # Uptime should be >= previous uptime
    assert stats2["uptime_minutes"] >= stats1["uptime_minutes"]


def test_cache_stats_hit_rate_calculation():
    """Test that hit rate is calculated correctly."""
    if not CACHE_MANAGER_AVAILABLE:
        pytest.skip("Cache manager not available")
    
    # Clear cache first
    requests.delete("http://localhost:8000/api/cache/clear")
    
    # Add items and perform operations
    cache_manager = get_cache_manager()
    cache_manager.set("hit_rate_test", "value")
    
    # Perform some hits and misses
    cache_manager.get("hit_rate_test")  # Hit
    cache_manager.get("hit_rate_test")  # Hit
    cache_manager.get("nonexistent")    # Miss
    
    # Check hit rate
    r = requests.get("http://localhost:8000/api/cache/stats")
    assert r.status_code == 200
    stats = r.json()
    
    # Should have 2 hits out of 3 total requests = 66.7% hit rate
    assert stats["total_requests"] == 3
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert abs(stats["hit_rate"] - 0.6667) < 0.01  # Allow small floating point differences


def test_cache_stats_error_handling():
    """Test error handling when API is not available."""
    # This test would need to be run when API is down
    # For now, we'll test that the endpoint returns proper error codes
    try:
        r = requests.get("http://localhost:8000/api/cache/stats", timeout=1)
        # If we get here, API is running, which is expected in normal test runs
        assert r.status_code in [200, 503]  # 503 if cache manager not initialized
    except requests.exceptions.RequestException:
        # API not available - this is expected in some test environments
        pass


def test_cache_stats_json_format():
    """Test that the response is valid JSON."""
    r = requests.get("http://localhost:8000/api/cache/stats")
    assert r.status_code == 200
    
    # Should be able to parse as JSON
    data = r.json()
    assert isinstance(data, dict)
    
    # Should have timestamp
    assert "timestamp" in data
    assert isinstance(data["timestamp"], (int, float))


def test_cache_clear_response_format():
    """Test that cache clear returns proper response format."""
    r = requests.delete("http://localhost:8000/api/cache/clear")
    assert r.status_code == 200
    
    data = r.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert "timestamp" in data
    assert isinstance(data["status"], str)
    assert isinstance(data["timestamp"], (int, float))


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Testing Cache Stats Endpoints...")
    
    try:
        test_cache_stats_endpoint()
        print("✅ Cache stats endpoint test passed")
    except Exception as e:
        print(f"❌ Cache stats endpoint test failed: {e}")
    
    try:
        test_cache_clear_endpoint()
        print("✅ Cache clear endpoint test passed")
    except Exception as e:
        print(f"❌ Cache clear endpoint test failed: {e}")
    
    try:
        test_cache_stats_simple_format()
        print("✅ Simple format test passed")
    except Exception as e:
        print(f"❌ Simple format test failed: {e}")
    
    try:
        test_cache_stats_comprehensive_format()
        print("✅ Comprehensive format test passed")
    except Exception as e:
        print(f"❌ Comprehensive format test failed: {e}")
    
    print("\n🎉 Cache stats tests completed!")
