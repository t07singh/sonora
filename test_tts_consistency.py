#!/usr/bin/env python3
"""
TTS Consistency Test Suite for Sonora/Auralis AI Dubbing System.

Tests TTS consistency across multiple clips, measuring:
- Response times per clip
- Audio duration vs segment timestamps
- Whisper output alignment with TTS synthesis
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from asr.transcriber import Transcriber
from translate.translator import Translator
from tts.tts_provider import TTSProvider
from utils.perf_timer import PerfTimer, PerfProfiler
from utils.cache_manager import clear_all_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TTSConsistencyTester:
    """Test suite for TTS consistency verification."""
    
    def __init__(self):
        """Initialize the TTS consistency tester."""
        self.transcriber = Transcriber()
        self.translator = Translator()
        self.tts_provider = TTSProvider()
        
        # Test data - different types of content
        self.test_clips = [
            {
                "name": "Short Greeting",
                "text": "Hello, how are you?",
                "expected_duration": 2.0,
                "description": "Simple greeting phrase"
            },
            {
                "name": "Medium Sentence",
                "text": "This is a longer sentence that should take more time to synthesize.",
                "expected_duration": 4.0,
                "description": "Medium length sentence"
            },
            {
                "name": "Long Paragraph",
                "text": "This is a much longer piece of text that contains multiple sentences and should demonstrate how the TTS system handles extended content with proper timing and duration calculations.",
                "expected_duration": 8.0,
                "description": "Long paragraph with multiple sentences"
            }
        ]
        
        self.results = []
    
    def test_individual_tts_clips(self):
        """Test individual TTS clips for response time and duration."""
        print("\n" + "="*70)
        print("TESTING INDIVIDUAL TTS CLIPS")
        print("="*70)
        
        for i, clip in enumerate(self.test_clips):
            print(f"\n--- Test Clip {i+1}: {clip['name']} ---")
            print(f"Description: {clip['description']}")
            print(f"Text: '{clip['text']}'")
            print(f"Expected Duration: {clip['expected_duration']}s")
            
            # Test TTS synthesis with timing
            with PerfTimer(f"TTS Clip {i+1}", logger):
                result = self.tts_provider.synthesize(
                    clip['text'], 
                    f"test_clip_{i+1}.wav"
                )
            
            # Analyze results
            actual_duration = result.get('duration', 0)
            success = result.get('success', False)
            
            print(f"Result:")
            print(f"  Success: {success}")
            print(f"  Actual Duration: {actual_duration:.2f}s")
            print(f"  Expected Duration: {clip['expected_duration']:.2f}s")
            print(f"  Duration Difference: {abs(actual_duration - clip['expected_duration']):.2f}s")
            print(f"  Duration Accuracy: {((1 - abs(actual_duration - clip['expected_duration']) / clip['expected_duration']) * 100):.1f}%")
            
            # Store results
            self.results.append({
                "clip_name": clip['name'],
                "text": clip['text'],
                "expected_duration": clip['expected_duration'],
                "actual_duration": actual_duration,
                "success": success,
                "duration_accuracy": ((1 - abs(actual_duration - clip['expected_duration']) / clip['expected_duration']) * 100)
            })
    
    def test_back_to_back_consistency(self):
        """Test TTS consistency by running the same clip multiple times."""
        print("\n" + "="*70)
        print("TESTING BACK-TO-BACK CONSISTENCY")
        print("="*70)
        
        test_text = "This is a consistency test to verify that TTS produces the same results."
        num_runs = 3
        
        print(f"Running '{test_text}' {num_runs} times back-to-back...")
        
        consistency_results = []
        
        for i in range(num_runs):
            print(f"\nRun {i+1}/{num_runs}:")
            
            with PerfTimer(f"Consistency Run {i+1}", logger):
                result = self.tts_provider.synthesize(
                    test_text,
                    f"consistency_test_{i+1}.wav"
                )
            
            duration = result.get('duration', 0)
            success = result.get('success', False)
            
            print(f"  Duration: {duration:.2f}s")
            print(f"  Success: {success}")
            
            consistency_results.append({
                "run": i+1,
                "duration": duration,
                "success": success
            })
        
        # Analyze consistency
        durations = [r['duration'] for r in consistency_results]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        duration_variance = max_duration - min_duration
        
        print(f"\nConsistency Analysis:")
        print(f"  Average Duration: {avg_duration:.2f}s")
        print(f"  Min Duration: {min_duration:.2f}s")
        print(f"  Max Duration: {max_duration:.2f}s")
        print(f"  Duration Variance: {duration_variance:.2f}s")
        print(f"  Consistency: {'High' if duration_variance < 0.1 else 'Medium' if duration_variance < 0.5 else 'Low'}")
    
    def test_whisper_tts_alignment(self):
        """Test alignment between Whisper output and TTS synthesis."""
        print("\n" + "="*70)
        print("TESTING WHISPER-TTS ALIGNMENT")
        print("="*70)
        
        # Create test audio file (dummy for mock mode)
        test_audio = "test_alignment.wav"
        
        print("Step 1: ASR Transcription")
        with PerfTimer("ASR Transcription", logger):
            transcription_result = self.transcriber.transcribe(test_audio)
            segments = self.transcriber.transcribe_segments(test_audio)
        
        print(f"Transcription Result: {transcription_result['text']}")
        print(f"Number of Segments: {len(segments)}")
        
        # Calculate total duration from segments
        total_segment_duration = 0
        for i, segment in enumerate(segments):
            segment_duration = segment['end'] - segment['start']
            total_segment_duration += segment_duration
            print(f"  Segment {i+1}: [{segment['start']:.2f}s-{segment['end']:.2f}s] "
                  f"Duration: {segment_duration:.2f}s - '{segment['text']}'")
        
        print(f"Total Segment Duration: {total_segment_duration:.2f}s")
        
        print("\nStep 2: Translation")
        translated_segments = []
        for segment in segments:
            if segment['lang'] == 'JP':
                translated_text = self.translator.translate(segment['text'], segment['lang'])
                translated_segment = segment.copy()
                translated_segment['text'] = translated_text
                translated_segment['lang'] = 'EN'
                translated_segments.append(translated_segment)
            else:
                translated_segments.append(segment)
        
        print("Translated Segments:")
        for i, segment in enumerate(translated_segments):
            print(f"  Segment {i+1}: '{segment['text']}'")
        
        print("\nStep 3: TTS Synthesis")
        # Combine all text for TTS
        text_to_synthesize = " ".join([seg['text'] for seg in translated_segments if seg['lang'] in ['EN', 'JP']])
        print(f"Text to Synthesize: '{text_to_synthesize}'")
        
        with PerfTimer("TTS Synthesis", logger):
            tts_result = self.tts_provider.synthesize(text_to_synthesize, "alignment_test.wav")
        
        tts_duration = tts_result.get('duration', 0)
        tts_success = tts_result.get('success', False)
        
        print(f"TTS Result:")
        print(f"  Success: {tts_success}")
        print(f"  TTS Duration: {tts_duration:.2f}s")
        print(f"  Segment Duration: {total_segment_duration:.2f}s")
        print(f"  Duration Difference: {abs(tts_duration - total_segment_duration):.2f}s")
        
        # Calculate alignment accuracy
        if total_segment_duration > 0:
            alignment_accuracy = (1 - abs(tts_duration - total_segment_duration) / total_segment_duration) * 100
            print(f"  Alignment Accuracy: {alignment_accuracy:.1f}%")
        else:
            print(f"  Alignment Accuracy: N/A (no segment duration)")
    
    def test_cache_impact_on_consistency(self):
        """Test how caching affects TTS consistency."""
        print("\n" + "="*70)
        print("TESTING CACHE IMPACT ON CONSISTENCY")
        print("="*70)
        
        test_text = "Cache consistency test for TTS operations."
        
        print("Step 1: First TTS call (should miss cache)")
        with PerfTimer("First TTS Call", logger):
            result1 = self.tts_provider.synthesize(test_text, "cache_test_1.wav")
        
        duration1 = result1.get('duration', 0)
        print(f"  Duration: {duration1:.2f}s")
        
        print("Step 2: Second TTS call (should hit cache)")
        with PerfTimer("Second TTS Call", logger):
            result2 = self.tts_provider.synthesize(test_text, "cache_test_2.wav")
        
        duration2 = result2.get('duration', 0)
        print(f"  Duration: {duration2:.2f}s")
        
        print("Step 3: Third TTS call (should hit cache)")
        with PerfTimer("Third TTS Call", logger):
            result3 = self.tts_provider.synthesize(test_text, "cache_test_3.wav")
        
        duration3 = result3.get('duration', 0)
        print(f"  Duration: {duration3:.2f}s")
        
        # Check consistency
        durations = [duration1, duration2, duration3]
        all_same = all(d == durations[0] for d in durations)
        
        print(f"\nCache Consistency Analysis:")
        print(f"  All durations identical: {all_same}")
        print(f"  Duration 1: {duration1:.2f}s")
        print(f"  Duration 2: {duration2:.2f}s")
        print(f"  Duration 3: {duration3:.2f}s")
        
        if all_same:
            print("  ✅ Cache maintains TTS consistency")
        else:
            print("  ⚠️  Cache may affect TTS consistency")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        print("\n" + "="*70)
        print("TTS CONSISTENCY TEST SUMMARY REPORT")
        print("="*70)
        
        if not self.results:
            print("No test results available.")
            return
        
        # Calculate overall statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        avg_accuracy = sum(r['duration_accuracy'] for r in self.results) / total_tests
        
        print(f"Overall Statistics:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Successful Tests: {successful_tests}")
        print(f"  Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"  Average Duration Accuracy: {avg_accuracy:.1f}%")
        
        print(f"\nIndividual Test Results:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['clip_name']}: {result['duration_accuracy']:.1f}% accuracy")
        
        # Performance assessment
        if avg_accuracy > 90:
            performance = "Excellent"
        elif avg_accuracy > 80:
            performance = "Good"
        elif avg_accuracy > 70:
            performance = "Fair"
        else:
            performance = "Poor"
        
        print(f"\nOverall Performance Assessment: {performance}")
        
        # Recommendations
        print(f"\nRecommendations:")
        if avg_accuracy < 80:
            print("  - Consider adjusting TTS duration calculation algorithms")
        if successful_tests < total_tests:
            print("  - Investigate TTS synthesis failures")
        if avg_accuracy > 90:
            print("  - TTS consistency is excellent, system ready for production")
    
    def run_all_tests(self):
        """Run all TTS consistency tests."""
        print("TTS CONSISTENCY TEST SUITE")
        print("="*70)
        print("Testing TTS consistency across multiple clips...")
        
        # Clear cache for clean testing
        clear_all_cache()
        
        # Run all tests
        self.test_individual_tts_clips()
        self.test_back_to_back_consistency()
        self.test_whisper_tts_alignment()
        self.test_cache_impact_on_consistency()
        
        # Generate summary
        self.generate_summary_report()


def main():
    """Run the TTS consistency test suite."""
    tester = TTSConsistencyTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()









