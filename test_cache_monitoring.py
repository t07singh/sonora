#!/usr/bin/env python3
"""
Quick test script for the Sonora Cache Monitoring System.

This script tests the cache endpoints and functionality.
"""

import requests
import time
import json
from sonora.utils.cache_manager import get_cache_manager

def test_cache_manager():
    """Test the cache manager directly."""
    print("🧪 Testing Cache Manager...")
    
    cache_manager = get_cache_manager()
    
    # Test basic operations
    cache_manager.set("test_key", "test_value")
    result = cache_manager.get("test_key")
    assert result == "test_value", f"Expected 'test_value', got {result}"
    
    # Test stats
    stats = cache_manager.get_stats()
    assert stats['memory_items'] > 0, "Should have memory items"
    assert stats['total_requests'] > 0, "Should have requests"
    
    print("✅ Cache Manager tests passed")

def test_api_endpoints():
    """Test the API endpoints."""
    print("🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data['status']}")
            assert health_data['components']['cache_manager'], "Cache manager should be healthy"
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure to start the server with: python -m sonora.api.server")
        return False
    
    # Test cache stats endpoint
    try:
        response = requests.get(f"{base_url}/api/cache/stats", timeout=5)
        if response.status_code == 200:
            stats_data = response.json()
            print("✅ Cache stats endpoint working")
            print(f"   Memory items: {stats_data['memory_items']}")
            print(f"   Disk items: {stats_data['disk_items']}")
            print(f"   Hit rate: {stats_data['hit_rate']:.2%}")
            print(f"   Uptime: {stats_data['uptime_minutes']:.1f} minutes")
        else:
            print(f"❌ Cache stats failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cache stats request failed: {e}")
        return False
    
    # Test cache clear endpoint
    try:
        response = requests.delete(f"{base_url}/api/cache/clear", timeout=10)
        if response.status_code == 200:
            clear_data = response.json()
            print("✅ Cache clear endpoint working")
            print(f"   Status: {clear_data['status']}")
        else:
            print(f"❌ Cache clear failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cache clear request failed: {e}")
        return False
    
    return True

def test_cache_performance():
    """Test cache performance with multiple operations."""
    print("⚡ Testing Cache Performance...")
    
    cache_manager = get_cache_manager()
    
    # Add many items
    start_time = time.time()
    for i in range(100):
        cache_manager.set(f"perf_key_{i}", f"perf_value_{i}")
    add_time = time.time() - start_time
    
    # Retrieve items
    start_time = time.time()
    for i in range(100):
        result = cache_manager.get(f"perf_key_{i}")
        assert result == f"perf_value_{i}", f"Value mismatch for key {i}"
    get_time = time.time() - start_time
    
    # Get stats
    stats = cache_manager.get_stats()
    
    print(f"✅ Performance test completed:")
    print(f"   Added 100 items in {add_time:.3f}s")
    print(f"   Retrieved 100 items in {get_time:.3f}s")
    print(f"   Hit rate: {stats['hit_rate']:.2%}")
    print(f"   Total requests: {stats['total_requests']}")

def main():
    """Run all tests."""
    print("🧠 Sonora Cache Monitoring System Test")
    print("=" * 50)
    
    # Test cache manager
    test_cache_manager()
    print()
    
    # Test API endpoints
    api_success = test_api_endpoints()
    print()
    
    if api_success:
        # Test performance
        test_cache_performance()
        print()
    
    print("🎉 All tests completed!")
    
    if api_success:
        print("\n📊 To view the dashboard, run:")
        print("   python -m sonora.run_cache_dashboard")
        print("\n🌐 Dashboard will be available at: http://localhost:8501")
    else:
        print("\n💡 To start the API server, run:")
        print("   python -m sonora.api.server")
        print("   or")
        print("   uvicorn sonora.api.server:app --reload")

if __name__ == "__main__":
    main()










