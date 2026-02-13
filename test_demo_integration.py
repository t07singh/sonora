#!/usr/bin/env python3
"""
Test script to verify the demo app cache integration.

This script tests the cache monitoring integration in the demo app.
"""

import requests
import time
from sonora.utils.cache_manager import get_cache_manager

def test_demo_app_cache_integration():
    """Test the cache integration in the demo app."""
    print("🧪 Testing Demo App Cache Integration...")
    
    base_url = "http://localhost:8000"
    cache_stats_url = f"{base_url}/api/cache/stats"
    cache_clear_url = f"{base_url}/api/cache/clear"
    
    # Test 1: Check if cache stats endpoint is accessible
    print("1. Testing cache stats endpoint...")
    try:
        response = requests.get(cache_stats_url, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Cache stats accessible")
            print(f"   Memory items: {stats['memory_items']}")
            print(f"   Hit rate: {stats['hit_rate']:.2%}")
        else:
            print(f"   ❌ Cache stats failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot connect to cache API: {e}")
        return False
    
    # Test 2: Add some cache data
    print("2. Adding test cache data...")
    cache_manager = get_cache_manager()
    for i in range(5):
        cache_manager.set(f"demo_test_{i}", f"demo_value_{i}")
    
    # Test 3: Verify cache stats reflect the changes
    print("3. Verifying cache stats reflect changes...")
    try:
        response = requests.get(cache_stats_url, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            total_items = stats['memory_items'] + stats['disk_items']
            if total_items >= 5:
                print(f"   ✅ Cache stats updated correctly ({total_items} items)")
            else:
                print(f"   ⚠️ Cache stats may not reflect all changes ({total_items} items)")
        else:
            print(f"   ❌ Failed to get updated stats: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting updated stats: {e}")
    
    # Test 4: Test cache clear functionality
    print("4. Testing cache clear functionality...")
    try:
        response = requests.delete(cache_clear_url, timeout=10)
        if response.status_code == 200:
            clear_data = response.json()
            print(f"   ✅ Cache clear successful: {clear_data['status']}")
            
            # Verify cache is actually cleared
            time.sleep(1)  # Give it a moment
            response = requests.get(cache_stats_url, timeout=5)
            if response.status_code == 200:
                stats = response.json()
                total_items = stats['memory_items'] + stats['disk_items']
                if total_items == 0:
                    print(f"   ✅ Cache successfully cleared ({total_items} items)")
                else:
                    print(f"   ⚠️ Cache may not be fully cleared ({total_items} items)")
        else:
            print(f"   ❌ Cache clear failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error clearing cache: {e}")
    
    return True

def test_cache_performance_visibility():
    """Test that cache performance is visible in the demo app context."""
    print("5. Testing cache performance visibility...")
    
    cache_manager = get_cache_manager()
    
    # Simulate some cache operations
    for i in range(10):
        cache_manager.set(f"perf_test_{i}", f"perf_value_{i}")
    
    # Generate some hits and misses
    for i in range(15):
        cache_manager.get(f"perf_test_{i % 10}")  # Some hits
        cache_manager.get(f"nonexistent_{i}")     # Some misses
    
    # Check final stats
    stats = cache_manager.get_stats()
    hit_rate = stats['hit_rate']
    total_requests = stats['total_requests']
    
    print(f"   Cache performance:")
    print(f"   - Total requests: {total_requests}")
    print(f"   - Hit rate: {hit_rate:.2%}")
    print(f"   - Memory items: {stats['memory_items']}")
    print(f"   - Disk items: {stats['disk_items']}")
    
    if hit_rate > 0:
        print("   ✅ Cache performance metrics are working")
    else:
        print("   ⚠️ No cache hits detected")
    
    return True

def main():
    """Run all integration tests."""
    print("🎬 Sonora Demo App Cache Integration Test")
    print("=" * 50)
    
    # Test basic integration
    success = test_demo_app_cache_integration()
    print()
    
    if success:
        # Test performance visibility
        test_cache_performance_visibility()
        print()
    
    print("🎉 Integration tests completed!")
    
    if success:
        print("\n📊 To test the demo app with cache monitoring:")
        print("   1. Start the API server: python -m sonora.api.server")
        print("   2. Start the demo app: streamlit run sonora/ui/demo_app.py")
        print("   3. Check the sidebar for cache status")
        print("   4. Upload an audio file and watch cache metrics")
    else:
        print("\n💡 Make sure the API server is running first:")
        print("   python -m sonora.api.server")

if __name__ == "__main__":
    main()










