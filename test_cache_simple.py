#!/usr/bin/env python3
"""
Simple cache test to demonstrate cache functionality without Unicode issues.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.cache_manager import get_cache_manager, get_cache_stats, log_cache_stats, clear_all_cache
from translate.translator import Translator
from tts.tts_provider import TTSProvider


def test_simple_cache():
    """Test cache with simple English text."""
    print("Testing Cache System")
    print("=" * 40)
    
    # Clear cache
    clear_all_cache()
    
    # Test translation cache
    translator = Translator()
    
    print("Testing Translation Cache:")
    print("1. First translation of 'Hello'")
    result1 = translator.translate("Hello", "JP")
    print(f"   Result: {result1}")
    
    print("2. Second translation of 'Hello' (should hit cache)")
    result2 = translator.translate("Hello", "JP")
    print(f"   Result: {result2}")
    
    print("3. Translation of 'Goodbye'")
    result3 = translator.translate("Goodbye", "JP")
    print(f"   Result: {result3}")
    
    print("4. Third translation of 'Hello' (should hit cache)")
    result4 = translator.translate("Hello", "JP")
    print(f"   Result: {result4}")
    
    # Test TTS cache
    print("\nTesting TTS Cache:")
    tts_provider = TTSProvider()
    
    print("1. First TTS synthesis of 'Hello world'")
    result1 = tts_provider.synthesize("Hello world", "test1.wav")
    print(f"   Success: {result1['success']}")
    
    print("2. Second TTS synthesis of 'Hello world' (should hit cache)")
    result2 = tts_provider.synthesize("Hello world", "test2.wav")
    print(f"   Success: {result2['success']}")
    
    # Show cache statistics
    print("\nCache Statistics:")
    stats = get_cache_stats()
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Memory Hits: {stats['hits']}")
    print(f"Disk Hits: {stats['disk_hits']}")
    print(f"Total Misses: {stats['misses'] + stats['disk_misses']}")
    print(f"Hit Rate: {stats['hit_rate']:.2%}")
    print(f"Cache Files: {stats['cache_files']}")
    
    # Verify results are consistent
    print(f"\nTranslation Results Match: {result1 == result2 == result4}")
    print(f"TTS Results Match: {result1['success'] == result2['success']}")


if __name__ == "__main__":
    test_simple_cache()









