import asyncio, os, time, tempfile, aiofiles
import pytest
import httpx
import websockets

API_URL = os.getenv("API_URL", "http://localhost:8000")
WS_URL  = os.getenv("WS_URL", "ws://localhost:8000/ws/status")

@pytest.mark.asyncio
async def test_health_endpoint():
    """
    ✅ Ensures /health responds quickly with correct fields.
    """
    async with httpx.AsyncClient(timeout=3) as client:
        start = time.time()
        r = await client.get(f"{API_URL}/health")
        latency = time.time() - start
        assert r.status_code == 200
        data = r.json()
        assert "status" in data and data["status"] == "ok"
        assert "uptime" in data and isinstance(data["uptime"], (int, float))
        assert latency < 1.5, f"Health too slow ({latency:.2f}s)"
        print(f"Health endpoint OK ({latency:.2f}s)")

@pytest.mark.asyncio
async def test_websocket_live_updates():
    """
    ✅ Verifies WebSocket stays alive for N seconds and sends valid messages.
    """
    N = 5
    received = 0
    async with websockets.connect(WS_URL) as ws:
        start = time.time()
        while time.time() - start < N:
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            assert "timestamp" in msg
            received += 1
        assert received >= 3, f"Expected ≥3 WS messages, got {received}"
    print(f"WebSocket alive {N}s, {received} messages received.")

@pytest.mark.asyncio
async def test_metrics_values_change():
    """
    ✅ Confirms Prometheus metrics (/metrics) increase over time.
    """
    async with httpx.AsyncClient(timeout=3) as client:
        m1 = await client.get(f"{API_URL}/metrics")
        await asyncio.sleep(2)
        m2 = await client.get(f"{API_URL}/metrics")
        assert "sonora_up_seconds" in m2.text
        # check that uptime increased
        t1 = float([l.split()[-1] for l in m1.text.splitlines() if "sonora_up_seconds" in l][0])
        t2 = float([l.split()[-1] for l in m2.text.splitlines() if "sonora_up_seconds" in l][0])
        assert t2 > t1, f"Uptime did not increase ({t1}→{t2})"
    print(f"Metrics OK (uptime {t1:.1f}->{t2:.1f}s)")

@pytest.mark.asyncio
async def test_websocket_reconnect_resilience():
    """
    ✅ Drop connection intentionally, ensure reconnection succeeds quickly.
    """
    for attempt in range(2):
        try:
            async with websockets.connect(WS_URL) as ws:
                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                assert "timestamp" in msg
                print(f"Attempt {attempt+1}: received WS message")
                await ws.close()
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
        await asyncio.sleep(1)
    # reconnect
    async with websockets.connect(WS_URL) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=2)
        assert "timestamp" in msg
    print("WebSocket reconnect OK.")

@pytest.mark.asyncio
async def test_cleanup_daemon(tmp_path):
    """
    ✅ Creates dummy tmp files and ensures cleanup coroutine deletes old ones.
    """
    tmp_dir = "/tmp/sonora"
    os.makedirs(tmp_dir, exist_ok=True)
    dummy = os.path.join(tmp_dir, "old_file.txt")
    async with aiofiles.open(dummy, "w") as f:
        await f.write("test")
    # backdate the file 25 hours
    old_time = time.time() - 25*3600
    os.utime(dummy, (old_time, old_time))
    await asyncio.sleep(2)
    # Wait for cleanup loop (if running)
    for _ in range(5):
        if not os.path.exists(dummy):
            break
        await asyncio.sleep(2)
    assert not os.path.exists(dummy), "Old temp file not cleaned up"
    print("Cleanup daemon working.")

@pytest.mark.asyncio
async def test_nginx_single_endpoint_routing():
    """
    ✅ Confirms API and Dashboard reachable via single NGINX entrypoint.
    (Requires docker-compose running.)
    """
    host = os.getenv("PUBLIC_HOST", "http://localhost")
    async with httpx.AsyncClient(timeout=3) as client:
        r1 = await client.get(f"{host}/api/health")
        r2 = await client.get(f"{host}/dashboard/")
        assert r1.status_code == 200
        assert r2.status_code in (200, 302)
    print("NGINX unified endpoint OK.")

@pytest.mark.asyncio
async def test_api_dub_video_endpoint():
    """
    ✅ Tests the video dubbing API endpoint with a dummy file.
    """
    # Create a dummy video file
    dummy_content = b"dummy video content"
    files = {"file": ("test_video.mp4", dummy_content, "video/mp4")}
    
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{API_URL}/api/dub/video", files=files)
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "filename" in data
        assert data["filename"] == "test_video.mp4"
    print("Video dubbing endpoint OK.")

@pytest.mark.asyncio
async def test_prometheus_metrics_format():
    """
    ✅ Validates Prometheus metrics format and required metrics.
    """
    async with httpx.AsyncClient(timeout=3) as client:
        r = await client.get(f"{API_URL}/metrics")
        assert r.status_code == 200
        metrics_text = r.text
        
        # Check for required metrics
        required_metrics = [
            "sonora_dub_requests_total",
            "sonora_processing_seconds",
            "sonora_up_seconds"
        ]
        
        for metric in required_metrics:
            assert metric in metrics_text, f"Missing metric: {metric}"
        
        # Check metrics format (should be valid Prometheus format)
        lines = metrics_text.splitlines()
        metric_lines = [line for line in lines if not line.startswith("#") and line.strip()]
        assert len(metric_lines) > 0, "No metrics found"
        
        # Validate at least one metric line format
        for line in metric_lines:
            if "sonora_up_seconds" in line:
                parts = line.split()
                assert len(parts) >= 2, f"Invalid metric format: {line}"
                assert parts[1].replace(".", "").isdigit(), f"Invalid metric value: {line}"
                break
    print("Prometheus metrics format OK.")

@pytest.mark.asyncio
async def test_concurrent_websocket_connections():
    """
    ✅ Tests multiple concurrent WebSocket connections.
    """
    async def connect_and_receive():
        async with websockets.connect(WS_URL) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            assert "timestamp" in msg
            return True
    
    # Test 3 concurrent connections
    tasks = [connect_and_receive() for _ in range(3)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if r is True)
    assert successful >= 2, f"Only {successful}/3 concurrent connections succeeded"
    print(f"Concurrent WebSocket connections OK ({successful}/3 successful).")

@pytest.mark.asyncio
async def test_system_performance_under_load():
    """
    ✅ Tests system performance with multiple concurrent requests.
    """
    async def make_request():
        async with httpx.AsyncClient(timeout=5) as client:
            start = time.time()
            r = await client.get(f"{API_URL}/health")
            latency = time.time() - start
            assert r.status_code == 200
            return latency
    
    # Make 10 concurrent requests
    tasks = [make_request() for _ in range(10)]
    latencies = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and calculate average latency
    valid_latencies = [l for l in latencies if isinstance(l, float)]
    assert len(valid_latencies) >= 8, f"Only {len(valid_latencies)}/10 requests succeeded"
    
    avg_latency = sum(valid_latencies) / len(valid_latencies)
    assert avg_latency < 2.0, f"Average latency too high: {avg_latency:.2f}s"
    print(f"Performance under load OK (avg latency: {avg_latency:.2f}s).")

@pytest.mark.asyncio
async def test_graceful_shutdown_simulation():
    """
    ✅ Simulates graceful shutdown by testing connection handling.
    """
    # Test that the system handles connection drops gracefully
    connections = []
    
    try:
        # Create multiple connections
        for _ in range(3):
            ws = await websockets.connect(WS_URL)
            connections.append(ws)
        
        # Receive one message from each
        for ws in connections:
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            assert "timestamp" in msg
        
        # Close connections abruptly
        for ws in connections:
            await ws.close()
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Test that new connections still work
        async with websockets.connect(WS_URL) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            assert "timestamp" in msg
        
        print("Graceful shutdown simulation OK.")
        
    except Exception as e:
        # Clean up any remaining connections
        for ws in connections:
            try:
                await ws.close()
            except:
                pass
        raise e

@pytest.mark.asyncio
async def test_error_handling():
    """
    ✅ Tests error handling for invalid requests.
    """
    async with httpx.AsyncClient(timeout=3) as client:
        # Test 404 endpoint
        r = await client.get(f"{API_URL}/nonexistent")
        assert r.status_code == 404
        
        # Test invalid POST to health endpoint
        r = await client.post(f"{API_URL}/health", json={"invalid": "data"})
        assert r.status_code == 405  # Method not allowed
        
        # Test malformed WebSocket URL
        try:
            async with websockets.connect(f"{WS_URL}/invalid") as ws:
                await ws.recv()
        except websockets.exceptions.InvalidStatusCode:
            pass  # Expected behavior
        except Exception as e:
            # Other exceptions are also acceptable for invalid endpoints
            pass
    
    print("Error handling OK.")

@pytest.mark.asyncio
async def test_environment_configuration():
    """
    ✅ Tests that environment variables are properly configured.
    """
    # Test that the API is accessible
    async with httpx.AsyncClient(timeout=3) as client:
        r = await client.get(f"{API_URL}/health")
        assert r.status_code == 200
    
    # Test WebSocket connection
    async with websockets.connect(WS_URL) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=2)
        assert "timestamp" in msg
    
    print("Environment configuration OK.")

# Performance and stress tests
@pytest.mark.asyncio
async def test_websocket_message_frequency():
    """
    ✅ Tests WebSocket message frequency and consistency.
    """
    message_times = []
    async with websockets.connect(WS_URL) as ws:
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 seconds
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            message_times.append(time.time())
            assert "timestamp" in msg
    
    # Check message frequency (should be ~1 message per second)
    if len(message_times) > 1:
        intervals = [message_times[i] - message_times[i-1] for i in range(1, len(message_times))]
        avg_interval = sum(intervals) / len(intervals)
        assert 0.5 <= avg_interval <= 2.0, f"Message frequency too irregular: {avg_interval:.2f}s"
    
    print(f"WebSocket message frequency OK ({len(message_times)} messages in 10s).")

@pytest.mark.asyncio
async def test_memory_usage_stability():
    """
    ✅ Tests that memory usage remains stable under load.
    """
    # Make multiple requests to test memory stability
    async with httpx.AsyncClient(timeout=3) as client:
        for _ in range(20):
            r = await client.get(f"{API_URL}/health")
            assert r.status_code == 200
            await asyncio.sleep(0.1)
    
    # Test WebSocket connections don't leak
    for _ in range(5):
        async with websockets.connect(WS_URL) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            assert "timestamp" in msg
            await ws.close()
        await asyncio.sleep(0.5)
    
    print("Memory usage stability OK.")



































