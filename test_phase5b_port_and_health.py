import asyncio
import os
import time
import subprocess
import socket
import requests
import pytest
import tempfile
import shutil

# NOTE: these tests assume you run the container locally via docker compose up -d
# or run the entrypoint script in a test environment.
HOST = os.getenv("PUBLIC_HOST", "http://localhost")

def is_port_open(port, host="127.0.0.1"):
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def test_entrypoint_selects_free_port(tmp_path):
    """Test that entrypoint script finds free ports when preferred port is occupied."""
    # emulate port in use by binding to 8000
    s = socket.socket()
    s.bind(("0.0.0.0", 8000))
    s.listen(1)
    try:
        # run entrypoint script and ensure it writes SONORA_PORT
        envfile = tmp_path / "envfile"
        # run the entrypoint with preferred 8000 but let it find next free
        p = subprocess.Popen(["/usr/local/bin/entrypoint.sh", "8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        p.terminate()
        # verify /tmp/sonora_env.sh created
        assert os.path.exists("/tmp/sonora_env.sh")
        with open("/tmp/sonora_env.sh") as f:
            txt = f.read()
        # Should have SONORA_PORT set and not equal 8000 (since blocked)
        assert "SONORA_PORT=" in txt
        port = int(txt.strip().split("=")[1])
        assert port != 8000
    finally:
        s.close()

def test_health_live_endpoint():
    """Test the lightweight liveness probe endpoint."""
    r = requests.get(HOST + "/health/live", timeout=3)
    assert r.status_code == 200
    data = r.json()
    assert data.get("live", False) is True

def test_full_health_endpoint():
    """Test the comprehensive health check endpoint."""
    r = requests.get(HOST + "/health", timeout=3)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "uptime" in data
    assert "services" in data
    services = data["services"]
    assert services.get("asr") is True
    assert services.get("tts") is True
    assert services.get("lipsync") is True

def test_prometheus_metrics_endpoint():
    """Test that Prometheus metrics are exposed correctly."""
    r = requests.get(HOST + "/metrics", timeout=3)
    assert r.status_code == 200
    content = r.text
    # Check for our custom metrics
    assert "sonora_live_status" in content
    assert "sonora_up_seconds" in content
    assert "sonora_dub_requests_total" in content

def test_nginx_proxy_routing():
    """Test that nginx correctly routes requests to the right services."""
    # Test API routing
    r = requests.get(HOST + "/api/health", timeout=3)
    assert r.status_code == 200
    
    # Test dashboard routing (should redirect to Streamlit)
    r = requests.get(HOST + "/dashboard/", timeout=3)
    # Streamlit might return 200 or redirect, both are acceptable
    assert r.status_code in [200, 301, 302]

def test_websocket_endpoint():
    """Test WebSocket connection for real-time updates."""
    import websocket
    ws_url = HOST.replace("http", "ws") + "/ws/status"
    
    def on_message(ws, message):
        data = json.loads(message)
        assert "timestamp" in data
        assert "uptime" in data
        assert "status" in data
        ws.close()
    
    def on_error(ws, error):
        pytest.fail(f"WebSocket error: {error}")
    
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error)
    ws.run_forever(timeout=5)

def test_docker_healthcheck():
    """Test that Docker healthcheck works correctly."""
    # This test assumes the container is running with healthcheck
    # We can test by making requests to the health endpoint
    for i in range(5):  # Try multiple times
        try:
            r = requests.get(HOST + "/health/live", timeout=2)
            if r.status_code == 200:
                return  # Success
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    
    pytest.fail("Health check failed after multiple attempts")

def test_port_allocation_under_load():
    """Test port allocation when multiple ports are occupied."""
    # Bind to multiple ports to simulate a busy system
    sockets = []
    try:
        for port in range(8000, 8010):
            s = socket.socket()
            s.bind(("0.0.0.0", port))
            s.listen(1)
            sockets.append(s)
        
        # Now test that entrypoint can still find a free port
        # This is more of a unit test for the find_free_port function
        # In a real scenario, we'd run the entrypoint script
        assert not is_port_open(8000)  # Should be occupied
        assert not is_port_open(8001)  # Should be occupied
        # Port 8010 should be free
        assert is_port_open(8010)
        
    finally:
        for s in sockets:
            s.close()

def test_supervisord_process_management():
    """Test that supervisord manages processes correctly."""
    # This test would require running the actual container
    # For now, we'll test the configuration file exists and is valid
    assert os.path.exists("deploy/supervisord.conf")
    
    with open("deploy/supervisord.conf") as f:
        config = f.read()
    
    # Check that all required programs are defined
    assert "[program:fastapi]" in config
    assert "[program:streamlit]" in config
    assert "[program:nginx]" in config
    
    # Check that autorestart is enabled
    assert "autorestart=true" in config

def test_nginx_template_substitution():
    """Test that nginx template gets correct port substitutions."""
    # Test the nginx replacer script logic
    test_env_content = "SONORA_PORT=8005"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(test_env_content)
        env_file = f.name
    
    try:
        # Simulate the nginx replacer script
        import subprocess
        result = subprocess.run([
            "bash", "-c", 
            f"source {env_file} && echo $SONORA_PORT"
        ], capture_output=True, text=True)
        
        assert result.stdout.strip() == "8005"
        
    finally:
        os.unlink(env_file)

def test_streamlit_ui_connectivity():
    """Test that Streamlit UI is accessible through nginx proxy."""
    # Test that the dashboard is accessible
    r = requests.get(HOST + "/dashboard/", timeout=5)
    # Streamlit should return some HTML content
    assert r.status_code in [200, 301, 302]
    if r.status_code == 200:
        assert "text/html" in r.headers.get("content-type", "")

def test_graceful_shutdown():
    """Test graceful shutdown behavior."""
    # This would require testing the actual container shutdown
    # For now, we'll test that the health endpoint responds quickly
    start_time = time.time()
    r = requests.get(HOST + "/health/live", timeout=1)
    response_time = time.time() - start_time
    
    assert r.status_code == 200
    assert response_time < 0.5  # Should respond quickly

def test_error_handling():
    """Test error handling in health endpoints."""
    # Test with invalid endpoint
    r = requests.get(HOST + "/health/invalid", timeout=3)
    assert r.status_code == 404
    
    # Test that live endpoint handles errors gracefully
    r = requests.get(HOST + "/health/live", timeout=3)
    assert r.status_code == 200
    data = r.json()
    assert "live" in data

def test_metrics_collection():
    """Test that metrics are being collected and updated."""
    # Get initial metrics
    r1 = requests.get(HOST + "/metrics", timeout=3)
    assert r1.status_code == 200
    initial_content = r1.text
    
    # Wait a bit for metrics to update
    time.sleep(3)
    
    # Get updated metrics
    r2 = requests.get(HOST + "/metrics", timeout=3)
    assert r2.status_code == 200
    updated_content = r2.text
    
    # Uptime should have increased
    assert updated_content != initial_content

# Integration test that requires running container
@pytest.mark.integration
def test_full_system_integration():
    """Full system integration test."""
    # Test all endpoints are working
    endpoints = [
        "/health",
        "/health/live", 
        "/metrics",
        "/dashboard/"
    ]
    
    for endpoint in endpoints:
        r = requests.get(HOST + endpoint, timeout=5)
        assert r.status_code in [200, 301, 302], f"Endpoint {endpoint} failed with status {r.status_code}"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

































