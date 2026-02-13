#!/usr/bin/env python3
"""
Simple TTS Consistency Test - Focus on key metrics without Unicode issues.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tts.tts_provider import TTSProvider
from utils.perf_timer import PerfTimer
from utils.cache_manager import clear_all_cache


def test_tts_consistency():
    """Test TTS consistency with simple English text."""
    print("TTS CONSISTENCY TEST")
    print("=" * 50)
    
    # Clear cache for clean testing
    clear_all_cache()
    
    tts_provider = TTSProvider()
    
    # Test clips with different lengths
    test_clips = [
        {
            "name": "Short",
            "text": "Hello world",
            "expected_duration": 2.0
        },
        {
            "name": "Medium", 
            "text": "This is a medium length sentence for testing.",
            "expected_duration": 4.0
        },
        {
            "name": "Long",
            "text": "This is a much longer sentence that should take more time to synthesize and demonstrate duration consistency.",
            "expected_duration": 6.0
        }
    ]
    
    print("Testing Individual Clips:")
    results = []
    
    for i, clip in enumerate(test_clips):
        print(f"\nClip {i+1}: {clip['name']}")
        print(f"Text: '{clip['text']}'")
        
        with PerfTimer(f"TTS {clip['name']}", None):
            result = tts_provider.synthesize(clip['text'], f"test_{i+1}.wav")
        
        actual_duration = result.get('duration', 0)
        success = result.get('success', False)
        
        print(f"Success: {success}")
        print(f"Expected: {clip['expected_duration']}s")
        print(f"Actual: {actual_duration}s")
        print(f"Difference: {abs(actual_duration - clip['expected_duration']):.2f}s")
        
        results.append({
            'name': clip['name'],
            'expected': clip['expected_duration'],
            'actual': actual_duration,
            'success': success
        })
    
    print("\n" + "="*50)
    print("BACK-TO-BACK CONSISTENCY TEST")
    print("="*50)
    
    # Test same text multiple times
    test_text = "Consistency test for TTS operations."
    print(f"Testing: '{test_text}'")
    
    durations = []
    for i in range(3):
        with PerfTimer(f"Consistency {i+1}", None):
            result = tts_provider.synthesize(test_text, f"consistency_{i+1}.wav")
        
        duration = result.get('duration', 0)
        durations.append(duration)
        print(f"Run {i+1}: {duration}s")
    
    # Analyze consistency
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    variance = max_duration - min_duration
    
    print(f"\nConsistency Analysis:")
    print(f"Average: {avg_duration:.2f}s")
    print(f"Min: {min_duration:.2f}s")
    print(f"Max: {max_duration:.2f}s")
    print(f"Variance: {variance:.2f}s")
    print(f"Consistency: {'High' if variance < 0.1 else 'Medium' if variance < 0.5 else 'Low'}")
    
    print("\n" + "="*50)
    print("CACHE IMPACT TEST")
    print("="*50)
    
    # Test cache impact
    cache_test_text = "Cache impact test for TTS."
    
    print("First call (cache miss):")
    with PerfTimer("Cache Miss", None):
        result1 = tts_provider.synthesize(cache_test_text, "cache_1.wav")
    duration1 = result1.get('duration', 0)
    print(f"Duration: {duration1}s")
    
    print("Second call (cache hit):")
    with PerfTimer("Cache Hit", None):
        result2 = tts_provider.synthesize(cache_test_text, "cache_2.wav")
    duration2 = result2.get('duration', 0)
    print(f"Duration: {duration2}s")
    
    print(f"Cache consistency: {'Maintained' if duration1 == duration2 else 'Affected'}")
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    successful_tests = sum(1 for r in results if r['success'])
    print(f"Successful tests: {successful_tests}/{len(results)}")
    print(f"Back-to-back consistency: {'High' if variance < 0.1 else 'Medium' if variance < 0.5 else 'Low'}")
    print(f"Cache consistency: {'Maintained' if duration1 == duration2 else 'Affected'}")
    
    # Overall assessment
    if successful_tests == len(results) and variance < 0.1 and duration1 == duration2:
        print("Overall: TTS consistency is excellent")
    elif successful_tests >= len(results) * 0.8 and variance < 0.5:
        print("Overall: TTS consistency is good with minor issues")
    else:
        print("Overall: TTS consistency needs improvement")


if __name__ == "__main__":
    test_tts_consistency()
