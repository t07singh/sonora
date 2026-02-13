#!/usr/bin/env python3
"""
Unit tests for the MetricsCollector class.

Tests all functionality including:
- Request tracking
- Latency measurement
- Error recording
- System metrics
- Audio processing metrics
- Cache metrics
- Thread safety
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from sonora.utils.metrics_collector import MetricsCollector, get_metrics_collector


class TestMetricsCollector:
    """Test suite for MetricsCollector class."""
    
    def setup_method(self):
        """Set up a fresh MetricsCollector for each test."""
        self.metrics = MetricsCollector()
    
    def test_metrics_basic(self):
        """Test basic metrics collection functionality."""
        # Record some basic metrics
        self.metrics.record_request("/api/dub")
        self.metrics.record_latency(0.5)
        self.metrics.record_error()
        
        # Wait a bit to ensure uptime is recorded
        time.sleep(0.1)
        
        # Get snapshot
        snap = self.metrics.snapshot()
        
        # Verify basic metrics
        assert snap["total_requests"] == 1
        assert snap["total_errors"] == 1
        assert snap["uptime_seconds"] > 0
        assert "cpu_percent" in snap["system"]
        assert "memory_mb" in snap["system"]
    
    def test_request_tracking(self):
        """Test request tracking by endpoint and method."""
        # Record requests to different endpoints
        self.metrics.record_request("/api/dub", "POST")
        self.metrics.record_request("/api/dub", "POST")
        self.metrics.record_request("/api/metrics", "GET")
        self.metrics.record_request("/health", "GET")
        
        # Check endpoint-specific counts
        endpoint_stats = self.metrics.get_endpoint_stats()
        
        assert endpoint_stats["/api/dub"]["requests"] == 2
        assert endpoint_stats["/api/metrics"]["requests"] == 1
        assert endpoint_stats["/health"]["requests"] == 1
        
        # Check total requests
        snap = self.metrics.snapshot()
        assert snap["total_requests"] == 4
    
    def test_latency_tracking(self):
        """Test latency measurement and statistics."""
        # Record various latencies
        latencies = [0.1, 0.2, 0.3, 0.4, 0.5, 1.0, 2.0]
        for latency in latencies:
            self.metrics.record_latency(latency)
        
        # Get latency stats
        latency_stats = self.metrics.get_latency_stats()
        
        assert latency_stats["avg_latency_sec"] == pytest.approx(0.5, rel=1e-2)
        assert latency_stats["min_latency_sec"] == 0.1
        assert latency_stats["max_latency_sec"] == 2.0
        assert latency_stats["samples"] == 7
        
        # Test endpoint-specific latency
        self.metrics.record_latency(0.8, "/api/dub")
        self.metrics.record_latency(0.2, "/api/dub")
        
        endpoint_stats = self.metrics.get_endpoint_stats()
        assert endpoint_stats["/api/dub"]["avg_latency"] == pytest.approx(0.5, rel=1e-2)
    
    def test_error_tracking(self):
        """Test error recording and categorization."""
        # Record different types of errors
        self.metrics.record_error("/api/dub", "validation_error")
        self.metrics.record_error("/api/dub", "processing_error")
        self.metrics.record_error("/api/metrics", "timeout_error")
        self.metrics.record_error()  # General error
        
        snap = self.metrics.snapshot()
        
        # Check total errors
        assert snap["total_errors"] == 4
        
        # Check error breakdown
        error_breakdown = snap["error_breakdown"]
        assert error_breakdown["validation_error"] == 1
        assert error_breakdown["processing_error"] == 1
        assert error_breakdown["timeout_error"] == 1
        assert error_breakdown["general"] == 1
    
    def test_audio_metrics(self):
        """Test audio processing metrics."""
        # Record audio durations
        durations = [10.5, 25.3, 45.7, 12.1, 8.9]
        for duration in durations:
            self.metrics.record_audio_duration(duration)
        
        audio_stats = self.metrics.get_audio_stats()
        
        assert audio_stats["audio_files_processed"] == 5
        assert audio_stats["avg_audio_duration_sec"] == pytest.approx(20.5, rel=1e-2)
        assert audio_stats["total_audio_processed_sec"] == pytest.approx(102.5, rel=1e-2)
    
    def test_cache_metrics(self):
        """Test cache performance metrics."""
        # Record cache hits and misses
        for _ in range(7):
            self.metrics.record_cache_hit()
        
        for _ in range(3):
            self.metrics.record_cache_miss()
        
        cache_stats = self.metrics.get_cache_stats()
        
        assert cache_stats["cache_hits"] == 7
        assert cache_stats["cache_misses"] == 3
        assert cache_stats["total_cache_requests"] == 10
        assert cache_stats["cache_hit_rate_percent"] == 70.0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection with mocked psutil."""
        # Mock system metrics
        mock_cpu.return_value = 45.2
        mock_memory.return_value = MagicMock(
            used=1024*1024*1024,  # 1GB
            percent=65.5
        )
        mock_disk.return_value = MagicMock(
            free=50*1024*1024*1024,  # 50GB
            percent=25.0
        )
        
        system_metrics = self.metrics.get_system_metrics()
        
        assert system_metrics["cpu_percent"] == 45.2
        assert system_metrics["memory_mb"] == 1024.0
        assert system_metrics["memory_percent"] == 65.5
        assert system_metrics["disk_free_gb"] == 50.0
        assert system_metrics["disk_percent"] == 25.0
    
    def test_latency_rolling_window(self):
        """Test that latency samples are limited to max_latency_samples."""
        # Create collector with small sample limit
        small_metrics = MetricsCollector(max_latency_samples=5)
        
        # Add more samples than the limit
        for i in range(10):
            small_metrics.record_latency(float(i))
        
        latency_stats = small_metrics.get_latency_stats()
        
        # Should only keep the last 5 samples (5, 6, 7, 8, 9)
        assert latency_stats["samples"] == 5
        assert latency_stats["min_latency_sec"] == 5.0
        assert latency_stats["max_latency_sec"] == 9.0
    
    def test_clear_metrics(self):
        """Test clearing all metrics."""
        # Add some data
        self.metrics.record_request("/api/dub")
        self.metrics.record_latency(0.5)
        self.metrics.record_error()
        self.metrics.record_audio_duration(10.0)
        self.metrics.record_cache_hit()
        
        # Verify data exists
        snap_before = self.metrics.snapshot()
        assert snap_before["total_requests"] == 1
        assert snap_before["total_errors"] == 1
        
        # Clear metrics
        self.metrics.clear()
        
        # Verify data is cleared
        snap_after = self.metrics.snapshot()
        assert snap_after["total_requests"] == 0
        assert snap_after["total_errors"] == 0
        assert snap_after["uptime_seconds"] < 1.0  # Should be reset
    
    def test_thread_safety(self):
        """Test that metrics collection is thread-safe."""
        def record_metrics(metrics_obj, count):
            for i in range(count):
                metrics_obj.record_request(f"/api/test{i}")
                metrics_obj.record_latency(0.1 + i * 0.01)
                if i % 10 == 0:
                    metrics_obj.record_error()
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_metrics, args=(self.metrics, 20))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all metrics were recorded correctly
        snap = self.metrics.snapshot()
        assert snap["total_requests"] == 100  # 5 threads * 20 requests each
        assert snap["total_errors"] == 10  # 5 threads * 2 errors each (every 10th request)
        
        latency_stats = self.metrics.get_latency_stats()
        assert latency_stats["samples"] == 100
    
    def test_snapshot_completeness(self):
        """Test that snapshot contains all expected fields."""
        # Add some data to ensure all sections are populated
        self.metrics.record_request("/api/dub")
        self.metrics.record_latency(0.5)
        self.metrics.record_error()
        self.metrics.record_audio_duration(10.0)
        self.metrics.record_cache_hit()
        
        snap = self.metrics.snapshot()
        
        # Check top-level fields
        required_fields = [
            "timestamp", "uptime_seconds", "uptime_minutes", "uptime_hours",
            "total_requests", "total_errors", "system", "latency", 
            "audio", "cache", "endpoints", "error_breakdown"
        ]
        
        for field in required_fields:
            assert field in snap, f"Missing field: {field}"
        
        # Check system metrics
        system_fields = ["cpu_percent", "memory_mb", "memory_percent", "disk_free_gb", "disk_percent"]
        for field in system_fields:
            assert field in snap["system"], f"Missing system field: {field}"
        
        # Check latency metrics
        latency_fields = ["avg_latency_sec", "min_latency_sec", "max_latency_sec", "p95_latency_sec", "p99_latency_sec", "samples"]
        for field in latency_fields:
            assert field in snap["latency"], f"Missing latency field: {field}"
        
        # Check audio metrics
        audio_fields = ["avg_audio_duration_sec", "total_audio_processed_sec", "audio_files_processed"]
        for field in audio_fields:
            assert field in snap["audio"], f"Missing audio field: {field}"
        
        # Check cache metrics
        cache_fields = ["cache_hits", "cache_misses", "cache_hit_rate_percent", "total_cache_requests"]
        for field in cache_fields:
            assert field in snap["cache"], f"Missing cache field: {field}"


class TestMetricsCollectorSingleton:
    """Test the global metrics collector singleton."""
    
    def test_get_metrics_collector_singleton(self):
        """Test that get_metrics_collector returns the same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        assert collector1 is collector2
    
    def test_singleton_persistence(self):
        """Test that the singleton persists data across calls."""
        collector1 = get_metrics_collector()
        collector1.record_request("/api/test")
        
        collector2 = get_metrics_collector()
        snap = collector2.snapshot()
        
        assert snap["total_requests"] == 1


class TestMetricsCollectorEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up a fresh MetricsCollector for each test."""
        self.metrics = MetricsCollector()
    
    def test_empty_latency_stats(self):
        """Test latency stats when no latencies have been recorded."""
        latency_stats = self.metrics.get_latency_stats()
        
        assert latency_stats["avg_latency_sec"] == 0.0
        assert latency_stats["min_latency_sec"] == 0.0
        assert latency_stats["max_latency_sec"] == 0.0
        assert latency_stats["samples"] == 0
    
    def test_empty_audio_stats(self):
        """Test audio stats when no audio has been processed."""
        audio_stats = self.metrics.get_audio_stats()
        
        assert audio_stats["avg_audio_duration_sec"] == 0.0
        assert audio_stats["total_audio_processed_sec"] == 0.0
        assert audio_stats["audio_files_processed"] == 0
    
    def test_empty_cache_stats(self):
        """Test cache stats when no cache operations have occurred."""
        cache_stats = self.metrics.get_cache_stats()
        
        assert cache_stats["cache_hits"] == 0
        assert cache_stats["cache_misses"] == 0
        assert cache_stats["cache_hit_rate_percent"] == 0.0
        assert cache_stats["total_cache_requests"] == 0
    
    def test_negative_latency(self):
        """Test handling of negative latency values."""
        self.metrics.record_latency(-0.1)
        self.metrics.record_latency(0.5)
        
        latency_stats = self.metrics.get_latency_stats()
        
        # Should handle negative values gracefully
        assert latency_stats["samples"] == 2
        assert latency_stats["min_latency_sec"] == -0.1
        assert latency_stats["max_latency_sec"] == 0.5
    
    def test_very_large_latency(self):
        """Test handling of very large latency values."""
        self.metrics.record_latency(1000.0)  # 1000 seconds
        
        latency_stats = self.metrics.get_latency_stats()
        
        assert latency_stats["avg_latency_sec"] == 1000.0
        assert latency_stats["max_latency_sec"] == 1000.0
    
    @patch('psutil.cpu_percent', side_effect=Exception("CPU error"))
    def test_system_metrics_error_handling(self, mock_cpu):
        """Test that system metrics handle errors gracefully."""
        system_metrics = self.metrics.get_system_metrics()
        
        # Should return default values when psutil fails
        assert system_metrics["cpu_percent"] == 0.0
        assert system_metrics["memory_mb"] == 0.0
        assert system_metrics["memory_percent"] == 0.0
        assert system_metrics["disk_free_gb"] == 0.0
        assert system_metrics["disk_percent"] == 0.0
    
    def test_cleanup_thread_functionality(self):
        """Test that the cleanup thread properly manages memory usage."""
        # Create a collector with small limits for testing
        small_metrics = MetricsCollector(max_latency_samples=10)
        
        # Add more samples than the limit
        for i in range(15):
            small_metrics.record_latency(float(i))
        
        # Verify we have more than the limit
        assert len(small_metrics.latencies) == 10  # Should be limited by maxlen
        
        # Add endpoint latencies
        for i in range(60):
            small_metrics.record_latency(float(i), "/api/test")
        
        # Verify endpoint latencies are limited
        assert len(small_metrics.endpoint_latencies["/api/test"]) == 60  # Should be limited by maxlen
        
        # Add audio durations
        for i in range(150):
            small_metrics.record_audio_duration(float(i))
        
        # Verify audio durations are limited
        assert len(small_metrics.audio_durations) == 100  # Should be limited by maxlen
        
        # The cleanup thread should be running in the background
        # We can't easily test the timing without mocking time.sleep,
        # but we can verify the structure is correct
        assert hasattr(small_metrics, '_cleanup_thread')
    
    @patch('time.sleep')  # Mock sleep to avoid waiting
    def test_cleanup_thread_execution(self, mock_sleep):
        """Test that the cleanup thread executes properly."""
        # Create a collector with small limits
        small_metrics = MetricsCollector(max_latency_samples=10)
        
        # Add samples that exceed limits
        for i in range(15):
            small_metrics.record_latency(float(i))
        
        for i in range(60):
            small_metrics.record_latency(float(i), "/api/test")
        
        for i in range(150):
            small_metrics.record_audio_duration(float(i))
        
        # Manually call the cleanup method to test it
        small_metrics.cleanup_thread()
        
        # Verify cleanup worked (though the deques should already be limited by maxlen)
        assert len(small_metrics.latencies) <= 10
        assert len(small_metrics.endpoint_latencies["/api/test"]) <= 100
        assert len(small_metrics.audio_durations) <= 100


if __name__ == "__main__":
    pytest.main([__file__])
