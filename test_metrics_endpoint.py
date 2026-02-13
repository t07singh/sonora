"""
Test Metrics Endpoint

Tests that the /metrics endpoint returns proper status JSON.
"""

import pytest
import time
from fastapi.testclient import TestClient
from sonora.api.server import app


class TestMetricsEndpoint:
    """Test metrics endpoint functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_metrics_endpoint_exists(self, client):
        """Test that /metrics endpoint exists and returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_metrics_returns_json(self, client):
        """Test that /metrics returns valid JSON."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_metrics_has_required_fields(self, client):
        """Test that /metrics returns required fields."""
        response = client.get("/metrics")
        data = response.json()
        
        # Check required fields
        assert "status" in data, "Should have 'status' field"
        assert "uptime" in data, "Should have 'uptime' field"
        assert "requests" in data, "Should have 'requests' field"
    
    def test_metrics_status_is_ok(self, client):
        """Test that status field is 'ok'."""
        response = client.get("/metrics")
        data = response.json()
        
        assert data["status"] == "ok", "Status should be 'ok'"
    
    def test_metrics_uptime_is_number(self, client):
        """Test that uptime is a number."""
        response = client.get("/metrics")
        data = response.json()
        
        assert isinstance(data["uptime"], (int, float)), "Uptime should be a number"
        assert data["uptime"] >= 0, "Uptime should be non-negative"
    
    def test_metrics_requests_is_number(self, client):
        """Test that requests is a number."""
        response = client.get("/metrics")
        data = response.json()
        
        assert isinstance(data["requests"], int), "Requests should be an integer"
        assert data["requests"] >= 0, "Requests should be non-negative"
    
    def test_metrics_requests_increment(self, client):
        """Test that request count increments on each call."""
        # Get initial request count
        response1 = client.get("/metrics")
        data1 = response1.json()
        initial_requests = data1["requests"]
        
        # Make another request
        response2 = client.get("/metrics")
        data2 = response2.json()
        new_requests = data2["requests"]
        
        # Request count should have increased
        assert new_requests > initial_requests, "Request count should increment"
    
    def test_metrics_uptime_increases(self, client):
        """Test that uptime increases over time."""
        # Get initial uptime
        response1 = client.get("/metrics")
        data1 = response1.json()
        initial_uptime = data1["uptime"]
        
        # Wait a small amount of time
        time.sleep(0.1)
        
        # Get new uptime
        response2 = client.get("/metrics")
        data2 = response2.json()
        new_uptime = data2["uptime"]
        
        # Uptime should have increased
        assert new_uptime > initial_uptime, "Uptime should increase over time"
    
    def test_metrics_response_structure(self, client):
        """Test complete response structure."""
        response = client.get("/metrics")
        data = response.json()
        
        # Verify complete structure
        expected_keys = {"status", "uptime", "requests"}
        actual_keys = set(data.keys())
        
        assert actual_keys == expected_keys, f"Expected keys {expected_keys}, got {actual_keys}"
        
        # Verify types
        assert isinstance(data["status"], str)
        assert isinstance(data["uptime"], (int, float))
        assert isinstance(data["requests"], int)
    
    def test_multiple_metrics_calls(self, client):
        """Test multiple consecutive calls to metrics endpoint."""
        responses = []
        
        # Make 5 consecutive calls
        for i in range(5):
            response = client.get("/metrics")
            assert response.status_code == 200
            data = response.json()
            responses.append(data)
        
        # All responses should have the same structure
        for i, data in enumerate(responses):
            assert "status" in data, f"Response {i} missing status"
            assert "uptime" in data, f"Response {i} missing uptime"
            assert "requests" in data, f"Response {i} missing requests"
            assert data["status"] == "ok", f"Response {i} status not ok"
        
        # Request counts should be increasing
        for i in range(1, len(responses)):
            assert responses[i]["requests"] > responses[i-1]["requests"], \
                f"Request count should increase: {responses[i-1]['requests']} -> {responses[i]['requests']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])










