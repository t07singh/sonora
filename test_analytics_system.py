#!/usr/bin/env python3
"""
Test script for the Sonora Analytics System.

This script tests the complete analytics pipeline:
1. Metrics collection
2. API endpoints
3. Dashboard functionality
"""

import requests
import time
import json
import sys
from pathlib import Path

# Add sonora to path
sys.path.insert(0, str(Path(__file__).parent / "sonora"))

from sonora.utils.metrics_collector import MetricsCollector, get_metrics_collector


def test_metrics_collector():
    """Test the MetricsCollector class directly."""
    print("🧪 Testing MetricsCollector...")
    
    # Test basic functionality
    metrics = MetricsCollector()
    
    # Record some test data
    metrics.record_request("/api/dub", "POST")
    metrics.record_request("/api/metrics", "GET")
    metrics.record_latency(0.5)
    metrics.record_latency(0.3, "/api/dub")
    metrics.record_error("/api/dub", "test_error")
    metrics.record_audio_duration(10.5)
    metrics.record_cache_hit()
    metrics.record_cache_miss()
    
    # Get snapshot
    snap = metrics.snapshot()
    
    # Verify data
    assert snap["total_requests"] == 2, f"Expected 2 requests, got {snap['total_requests']}"
    assert snap["total_errors"] == 1, f"Expected 1 error, got {snap['total_errors']}"
    assert snap["audio"]["audio_files_processed"] == 1, f"Expected 1 audio file, got {snap['audio']['audio_files_processed']}"
    assert snap["cache"]["cache_hits"] == 1, f"Expected 1 cache hit, got {snap['cache']['cache_hits']}"
    
    print("✅ MetricsCollector tests passed!")
    return True


def test_api_endpoints():
    """Test the API endpoints."""
    print("🌐 Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False
    
    # Test metrics endpoint
    try:
        response = requests.get(f"{base_url}/api/metrics", timeout=5)
        if response.status_code == 200:
            metrics_data = response.json()
            print("✅ Metrics endpoint working")
            print(f"   - Uptime: {metrics_data.get('uptime_minutes', 0):.1f} minutes")
            print(f"   - Total requests: {metrics_data.get('total_requests', 0)}")
            print(f"   - CPU usage: {metrics_data.get('system', {}).get('cpu_percent', 0):.1f}%")
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Metrics endpoint error: {e}")
        return False
    
    # Test analytics endpoint
    try:
        response = requests.get(f"{base_url}/api/analytics", timeout=5)
        if response.status_code == 200:
            analytics_data = response.json()
            print("✅ Analytics endpoint working")
            print(f"   - Endpoints tracked: {len(analytics_data.get('endpoints', {}))}")
            print(f"   - Cache hit rate: {analytics_data.get('cache', {}).get('cache_hit_rate_percent', 0):.1f}%")
        else:
            print(f"❌ Analytics endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Analytics endpoint error: {e}")
        return False
    
    return True


def test_metrics_clear():
    """Test clearing metrics."""
    print("🧹 Testing metrics clear...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Get metrics before clearing
        response = requests.get(f"{base_url}/api/metrics", timeout=5)
        if response.status_code == 200:
            metrics_before = response.json()
            requests_before = metrics_before.get('total_requests', 0)
            print(f"   - Requests before clear: {requests_before}")
        
        # Clear metrics
        response = requests.delete(f"{base_url}/api/metrics/clear", timeout=5)
        if response.status_code == 200:
            print("✅ Metrics clear endpoint working")
            
            # Verify metrics are cleared
            response = requests.get(f"{base_url}/api/metrics", timeout=5)
            if response.status_code == 200:
                metrics_after = response.json()
                requests_after = metrics_after.get('total_requests', 0)
                print(f"   - Requests after clear: {requests_after}")
                
                if requests_after == 0:
                    print("✅ Metrics successfully cleared")
                else:
                    print(f"⚠️  Metrics not fully cleared: {requests_after} requests remaining")
        else:
            print(f"❌ Metrics clear endpoint failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Metrics clear error: {e}")
        return False
    
    return True


def generate_test_traffic():
    """Generate some test traffic to populate metrics."""
    print("🚀 Generating test traffic...")
    
    base_url = "http://localhost:8000"
    
    # Make some requests to generate metrics
    endpoints = [
        ("/health", "GET"),
        ("/api/metrics", "GET"),
        ("/api/analytics", "GET"),
        ("/api/cache/stats", "GET"),
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 404, 405]:  # Accept various response codes
                print(f"   ✅ {method} {endpoint}")
            else:
                print(f"   ⚠️  {method} {endpoint} - {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {method} {endpoint} - {e}")
    
    # Wait a moment for metrics to be recorded
    time.sleep(1)
    print("✅ Test traffic generated")


def main():
    """Run all analytics system tests."""
    print("🎬 Sonora Analytics System Test Suite")
    print("=" * 50)
    
    # Test 1: Metrics Collector
    if not test_metrics_collector():
        print("❌ MetricsCollector tests failed!")
        return False
    
    print()
    
    # Test 2: API Endpoints
    if not test_api_endpoints():
        print("❌ API endpoint tests failed!")
        print("💡 Make sure the Sonora server is running: python -m sonora.api.server")
        return False
    
    print()
    
    # Test 3: Generate test traffic
    generate_test_traffic()
    print()
    
    # Test 4: Metrics Clear
    if not test_metrics_clear():
        print("❌ Metrics clear tests failed!")
        return False
    
    print()
    print("🎉 All analytics system tests passed!")
    print()
    print("📊 Next steps:")
    print("   1. Start the Streamlit dashboard: streamlit run sonora/analytics_dashboard.py")
    print("   2. Or use the integrated dashboard: streamlit run sonora/ui/demo_app.py")
    print("   3. View metrics at: http://localhost:8000/api/metrics")
    print("   4. View analytics at: http://localhost:8000/api/analytics")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)









