#!/usr/bin/env python3
"""
Test script to demonstrate cache functionality.

This script shows how the caching system works across different
components and measures cache hit/miss rates.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.cache_manager import get_cache_manager, get_cache_stats, log_cache_stats, clear_all_cache
from asr.transcriber import Transcriber
from translate.translator import Translator
from tts.tts_provider import TTSProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_translation_cache():
    """Test translation caching with repeated phrases."""
    print("\n" + "="*60)
    print("Testing Translation Cache")
    print("="*60)
    
    translator = Translator()
    
    # Common phrases that should be cached
    test_phrases = [
        "Hello",      # English
        "Thank you",  # English
        "Good morning", # English
        "Hello",      # Repeat - should hit cache
        "Thank you",  # Repeat - should hit cache
        "Goodbye",    # New phrase
        "Hello",      # Repeat again - should hit cache
    ]
    
    print("Translating phrases (some repeated):")
    for i, phrase in enumerate(test_phrases):
        print(f"  {i+1}. {phrase}")
        result = translator.translate(phrase, "JP")
        print(f"     -> {result}")
    
    # Show cache stats
    stats = get_cache_stats()
    print(f"\nTranslation Cache Stats:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Hit Rate: {stats['hit_rate']:.2%}")
    print(f"  Memory Hits: {stats['hits']}")
    print(f"  Disk Hits: {stats['disk_hits']}")


def test_asr_cache():
    """Test ASR caching with repeated audio files."""
    print("\n" + "="*60)
    print("Testing ASR Cache")
    print("="*60)
    
    transcriber = Transcriber()
    
    # Test with same audio file multiple times
    test_audio = "test_audio.wav"
    
    print("Transcribing same audio file multiple times:")
    for i in range(3):
        print(f"  Transcription {i+1}:")
        result = transcriber.transcribe(test_audio)
        print(f"    Text: {result['text']}")
        
        segments = transcriber.transcribe_segments(test_audio)
        print(f"    Segments: {len(segments)}")
    
    # Show cache stats
    stats = get_cache_stats()
    print(f"\nASR Cache Stats:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Hit Rate: {stats['hit_rate']:.2%}")


def test_tts_cache():
    """Test TTS caching with repeated text."""
    print("\n" + "="*60)
    print("Testing TTS Cache")
    print("="*60)
    
    tts_provider = TTSProvider()
    
    # Test with same text multiple times
    test_texts = [
        "Hello world",
        "Good morning",
        "Hello world",  # Repeat - should hit cache
        "Thank you",
        "Hello world",  # Repeat again - should hit cache
    ]
    
    print("Synthesizing text (some repeated):")
    for i, text in enumerate(test_texts):
        print(f"  {i+1}. '{text}'")
        result = tts_provider.synthesize(text, f"test_output_{i}.wav")
        print(f"     Success: {result['success']}")
    
    # Show cache stats
    stats = get_cache_stats()
    print(f"\nTTS Cache Stats:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Hit Rate: {stats['hit_rate']:.2%}")


def test_cache_persistence():
    """Test cache persistence across different instances."""
    print("\n" + "="*60)
    print("Testing Cache Persistence")
    print("="*60)
    
    # First instance
    translator1 = Translator()
    result1 = translator1.translate("Hello", "JP")
    print(f"First instance result: {result1}")
    
    # Show stats after first use
    stats1 = get_cache_stats()
    print(f"Stats after first use: {stats1['total_requests']} requests, {stats1['hit_rate']:.2%} hit rate")
    
    # Second instance (should use cache)
    translator2 = Translator()
    result2 = translator2.translate("Hello", "JP")
    print(f"Second instance result: {result2}")
    
    # Show stats after second use
    stats2 = get_cache_stats()
    print(f"Stats after second use: {stats2['total_requests']} requests, {stats2['hit_rate']:.2%} hit rate")
    
    # Verify results are the same
    print(f"Results match: {result1 == result2}")


def test_cache_clear():
    """Test cache clearing functionality."""
    print("\n" + "="*60)
    print("Testing Cache Clear")
    print("="*60)
    
    translator = Translator()
    
    # Use cache
    result1 = translator.translate("Test", "JP")
    print(f"First translation: {result1}")
    
    stats_before = get_cache_stats()
    print(f"Cache stats before clear: {stats_before['total_requests']} requests")
    
    # Clear cache
    clear_all_cache()
    print("Cache cleared!")
    
    # Use again (should miss cache)
    result2 = translator.translate("Test", "JP")
    print(f"Second translation: {result2}")
    
    stats_after = get_cache_stats()
    print(f"Cache stats after clear: {stats_after['total_requests']} requests")


def test_mixed_operations():
    """Test cache with mixed operations."""
    print("\n" + "="*60)
    print("Testing Mixed Operations Cache")
    print("="*60)
    
    transcriber = Transcriber()
    translator = Translator()
    tts_provider = TTSProvider()
    
    # Mix of operations
    operations = [
        ("ASR", lambda: transcriber.transcribe("test.wav")),
        ("Translation", lambda: translator.translate("Hello", "JP")),
        ("TTS", lambda: tts_provider.synthesize("Hello", "test.wav")),
        ("ASR", lambda: transcriber.transcribe("test.wav")),  # Repeat
        ("Translation", lambda: translator.translate("Thank you", "JP")),
        ("TTS", lambda: tts_provider.synthesize("Hello", "test.wav")),  # Repeat
    ]
    
    print("Running mixed operations:")
    for i, (op_name, operation) in enumerate(operations):
        print(f"  {i+1}. {op_name}")
        try:
            result = operation()
            print(f"     Success: {type(result).__name__}")
        except Exception as e:
            print(f"     Error: {e}")
    
    # Show final cache stats
    stats = get_cache_stats()
    print(f"\nFinal Cache Stats:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Hit Rate: {stats['hit_rate']:.2%}")
    print(f"  Memory Hits: {stats['hits']}")
    print(f"  Disk Hits: {stats['disk_hits']}")
    print(f"  Cache Files: {stats['cache_files']}")


def main():
    """Run all cache tests."""
    print("Sonora Cache System Test Suite")
    print("=" * 60)
    
    # Clear any existing cache
    clear_all_cache()
    
    # Test individual components
    test_translation_cache()
    test_asr_cache()
    test_tts_cache()
    
    # Test advanced features
    test_cache_persistence()
    test_cache_clear()
    test_mixed_operations()
    
    # Show final comprehensive stats
    print("\n" + "="*60)
    print("FINAL CACHE STATISTICS")
    print("="*60)
    log_cache_stats()
    
    print("\n" + "="*60)
    print("Cache system tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
