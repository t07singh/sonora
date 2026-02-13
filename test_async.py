#!/usr/bin/env python3
"""
Test script to demonstrate async processing functionality.

This script shows how the async dubbing pipeline works with concurrent processing.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.async_pipeline import AsyncDubbingPipeline
from utils.perf_timer import PerfTimer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_async_processing():
    """Test single file async processing."""
    print("\n" + "="*60)
    print("Testing Single File Async Processing")
    print("="*60)
    
    pipeline = AsyncDubbingPipeline(max_workers=2)
    
    # Create dummy audio content
    dummy_content = b"dummy audio content for testing"
    
    with PerfTimer("Single Async Processing", logger):
        result = await pipeline.process_audio_file(dummy_content, "test_audio.wav")
    
    print(f"Processing result: {result}")
    
    pipeline.shutdown()


async def test_concurrent_processing():
    """Test concurrent processing of multiple files."""
    print("\n" + "="*60)
    print("Testing Concurrent Batch Processing")
    print("="*60)
    
    pipeline = AsyncDubbingPipeline(max_workers=4)
    
    # Create multiple dummy files
    files = []
    for i in range(5):
        files.append({
            "content": f"dummy audio content {i}".encode(),
            "filename": f"test_audio_{i}.wav"
        })
    
    with PerfTimer("Concurrent Batch Processing", logger):
        results = await pipeline.process_batch(files)
    
    print(f"Batch processing results:")
    for i, result in enumerate(results):
        print(f"  File {i}: {result['success']} - {result.get('filename', 'unknown')}")
    
    pipeline.shutdown()


async def test_async_vs_sync_comparison():
    """Compare async vs sync processing times."""
    print("\n" + "="*60)
    print("Testing Async vs Sync Performance Comparison")
    print("="*60)
    
    # Test async processing
    pipeline = AsyncDubbingPipeline(max_workers=3)
    
    files = []
    for i in range(3):
        files.append({
            "content": f"dummy content {i}".encode(),
            "filename": f"async_test_{i}.wav"
        })
    
    # Async processing
    with PerfTimer("Async Processing (3 files)", logger):
        async_results = await pipeline.process_batch(files)
    
    # Simulate sync processing (sequential)
    with PerfTimer("Sync Processing (3 files)", logger):
        sync_results = []
        for file_data in files:
            result = await pipeline.process_audio_file(file_data["content"], file_data["filename"])
            sync_results.append(result)
    
    print(f"Async results: {len(async_results)} files processed")
    print(f"Sync results: {len(sync_results)} files processed")
    
    pipeline.shutdown()


async def test_pipeline_scalability():
    """Test pipeline scalability with different worker counts."""
    print("\n" + "="*60)
    print("Testing Pipeline Scalability")
    print("="*60)
    
    worker_counts = [1, 2, 4]
    file_count = 6
    
    for workers in worker_counts:
        print(f"\nTesting with {workers} workers:")
        
        pipeline = AsyncDubbingPipeline(max_workers=workers)
        
        files = []
        for i in range(file_count):
            files.append({
                "content": f"scalability test content {i}".encode(),
                "filename": f"scale_test_{i}.wav"
            })
        
        with PerfTimer(f"Scalability Test ({workers} workers)", logger):
            results = await pipeline.process_batch(files)
        
        successful = sum(1 for r in results if r["success"])
        print(f"  Workers: {workers}, Files: {file_count}, Successful: {successful}")
        
        pipeline.shutdown()


async def main():
    """Run all async tests."""
    print("Sonora Async Processing Test Suite")
    print("=" * 60)
    
    # Test single async processing
    await test_single_async_processing()
    
    # Test concurrent processing
    await test_concurrent_processing()
    
    # Test async vs sync comparison
    await test_async_vs_sync_comparison()
    
    # Test scalability
    await test_pipeline_scalability()
    
    print("\n" + "="*60)
    print("Async processing tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())









