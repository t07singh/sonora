#!/usr/bin/env python3
"""
Quick test script for Phase 5-B implementation.
Run this to verify the system is working correctly.
"""

import requests
import time
import sys
import os

def test_health_endpoints():
    """Test health endpoints are working."""
    base_url = "http://localhost"
    
    print("🔍 Testing health endpoints...")
    
    # Test full health endpoint
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ /health endpoint working - Status: {data.get('status')}")
            print(f"   Uptime: {data.get('uptime', 0):.1f}s")
            print(f"   Services: {data.get('services', {})}")
        else:
            print(f"❌ /health endpoint failed with status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ /health endpoint error: {e}")
        return False
    
    # Test live health endpoint
    try:
        r = requests.get(f"{base_url}/health/live", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ /health/live endpoint working - Live: {data.get('live')}")
        else:
            print(f"❌ /health/live endpoint failed with status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ /health/live endpoint error: {e}")
        return False
    
    return True

def test_prometheus_metrics():
    """Test Prometheus metrics endpoint."""
    base_url = "http://localhost"
    
    print("\n📊 Testing Prometheus metrics...")
    
    try:
        r = requests.get(f"{base_url}/metrics", timeout=5)
        if r.status_code == 200:
            content = r.text
            metrics_to_check = [
                "sonora_live_status",
                "sonora_up_seconds", 
                "sonora_dub_requests_total"
            ]
            
            found_metrics = []
            for metric in metrics_to_check:
                if metric in content:
                    found_metrics.append(metric)
            
            print(f"✅ /metrics endpoint working - Found {len(found_metrics)}/{len(metrics_to_check)} metrics")
            for metric in found_metrics:
                print(f"   ✓ {metric}")
            
            return len(found_metrics) > 0
        else:
            print(f"❌ /metrics endpoint failed with status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ /metrics endpoint error: {e}")
        return False

def test_dashboard_access():
    """Test dashboard accessibility."""
    base_url = "http://localhost"
    
    print("\n🎛️ Testing dashboard access...")
    
    try:
        r = requests.get(f"{base_url}/dashboard/", timeout=10)
        if r.status_code in [200, 301, 302]:
            print(f"✅ Dashboard accessible - Status: {r.status_code}")
            if r.status_code == 200:
                print(f"   Content-Type: {r.headers.get('content-type', 'unknown')}")
            return True
        else:
            print(f"❌ Dashboard failed with status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return False

def test_api_routing():
    """Test API routing through nginx."""
    base_url = "http://localhost"
    
    print("\n🔌 Testing API routing...")
    
    try:
        r = requests.get(f"{base_url}/api/health", timeout=5)
        if r.status_code == 200:
            print("✅ API routing working - /api/health accessible")
            return True
        else:
            print(f"❌ API routing failed with status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ API routing error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Phase 5-B Quick Test Suite")
    print("=" * 50)
    
    # Check if container is running
    try:
        r = requests.get("http://localhost/health", timeout=2)
        if r.status_code != 200:
            print("❌ Container not responding. Make sure to run:")
            print("   docker compose up -d")
            sys.exit(1)
    except Exception:
        print("❌ Cannot connect to localhost. Make sure to run:")
        print("   docker compose up -d")
        sys.exit(1)
    
    tests = [
        test_health_endpoints,
        test_prometheus_metrics,
        test_dashboard_access,
        test_api_routing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📋 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 5-B implementation is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

































