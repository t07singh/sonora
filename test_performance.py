#!/usr/bin/env python3
"""
Test script to demonstrate performance profiling functionality.

This script shows how the performance profiling works across different
components of the dubbing pipeline.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.perf_timer import PerfTimer, PerfProfiler, time_function
from asr.transcriber import Transcriber
from translate.translator import Translator
from tts.tts_provider import TTSProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_timer():
    """Test basic PerfTimer functionality."""
    print("\n" + "="*50)
    print("Testing Basic PerfTimer")
    print("="*50)
    
    with PerfTimer("Test Operation", logger):
        import time
        time.sleep(0.1)  # Simulate some work


def test_profiler():
    """Test PerfProfiler functionality."""
    print("\n" + "="*50)
    print("Testing PerfProfiler")
    print("="*50)
    
    profiler = PerfProfiler("Test Pipeline", logger)
    
    with profiler.stage("Stage 1"):
        import time
        time.sleep(0.05)
    
    with profiler.stage("Stage 2"):
        time.sleep(0.1)
    
    with profiler.stage("Stage 3"):
        time.sleep(0.03)
    
    profiler.report()


@time_function("Test Function")
def test_decorator():
    """Test function timing decorator."""
    import time
    time.sleep(0.08)


def test_component_profiling():
    """Test profiling with actual dubbing components."""
    print("\n" + "="*50)
    print("Testing Component Profiling")
    print("="*50)
    
    # Initialize components (will use mock mode if no API keys)
    transcriber = Transcriber()
    translator = Translator()
    tts_provider = TTSProvider()
    
    # Test with a dummy audio file path
    test_audio = "test_audio.wav"
    
    # Test ASR profiling
    print("\nTesting ASR Profiling:")
    try:
        result = transcriber.transcribe(test_audio)
        segments = transcriber.transcribe_segments(test_audio)
        print(f"   Transcription result: {result}")
        print(f"   Segments: {len(segments)}")
    except Exception as e:
        print(f"   ASR test failed: {e}")
    
    # Test Translation profiling
    print("\nTesting Translation Profiling:")
    try:
        translated = translator.translate("こんにちは", "JP")
        print(f"   Translation result: {translated}")
    except Exception as e:
        print(f"   Translation test failed: {e}")
    
    # Test TTS profiling
    print("\nTesting TTS Profiling:")
    try:
        tts_result = tts_provider.synthesize("Hello world", "test_output.wav")
        print(f"   TTS result: {tts_result}")
    except Exception as e:
        print(f"   TTS test failed: {e}")


def main():
    """Run all performance tests."""
    print("Sonora Performance Profiling Test Suite")
    print("=" * 60)
    
    # Test basic timer
    test_basic_timer()
    
    # Test profiler
    test_profiler()
    
    # Test decorator
    print("\n" + "="*50)
    print("Testing Function Decorator")
    print("="*50)
    test_decorator()
    
    # Test component profiling
    test_component_profiling()
    
    print("\n" + "="*60)
    print("Performance profiling tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
