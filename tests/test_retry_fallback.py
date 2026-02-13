import unittest
from unittest.mock import MagicMock, patch
import os
import time
import json
import shutil

# Add src to path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock missing dependency before import
sys.modules['sonora.audio_editing.bus_system'] = MagicMock()
from sonora.core.orchestrator import SonoraOrchestrator

class TestRetryFallback(unittest.TestCase):
    
    @patch('sonora.core.orchestrator.OpenAI')
    @patch('sonora.core.orchestrator.VibeVoiceAgent')
    @patch('sonora.core.orchestrator.EmotionTokenizer')
    @patch('sonora.core.orchestrator.StepAudioRefiner')
    @patch('sonora.core.orchestrator.EmotionalSplicer')
    @patch('sonora.core.orchestrator.HardenedTranslator')
    def setUp(self, MockTranslator, MockSplicer, MockRefiner, MockTokenizer, MockVibe, MockOpenAI):
        self.mock_vibe = MockVibe.return_value
        self.mock_tokenizer = MockTokenizer.return_value
        self.mock_refiner = MockRefiner.return_value
        self.orchestrator = SonoraOrchestrator("dummy.mp4")
        
        # Setup directories
        self.task_dir = "/tmp/sonora/tasks"
        self.output_dir = "shared_data/outputs"
        os.makedirs(self.task_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
    def tearDown(self):
        # Cleanup
        if os.path.exists(self.task_dir):
            shutil.rmtree(self.task_dir)
        # Don't delete output_dir entirely as it might be used by others, but for test safely cleaner to mock paths
        # Actually orchestrator uses hardcoded paths, so I should be careful. 
        # But since I control the test execution, I can clean up created files.
        pass

    def test_dispatch_timeout_and_cleanup(self):
        """Test that dispatch_to_qwen times out, returns None, and deletes task file."""
        print("\nTesting Dispatch Timeout & Cleanup...")
        
        # Call dispatch with short timeout
        timeout = 2.0
        start = time.time()
        result = self.orchestrator.dispatch_to_qwen("test text", timeout=timeout)
        duration = time.time() - start
        
        # Assertions
        self.assertIsNone(result, "Dispatch should return None on timeout")
        self.assertGreaterEqual(duration, timeout, "Should wait at least for timeout duration")
        
        # proper timeout is loose, but should be close.
        
        # Verify task file is gone
        # The dispatch function generates a random UUID, so we can't know the filename easily unless we mock uuid or listdir
        # But we know the directory should be empty if we started clean and it cleaned up.
        # However, concurrent tests might be an issue.
        # Let's inspect the logic again.
        # It deletes the specific task file.
        
        # To verify deletion, we can check if any json files exist in task_dir.
        json_files = [f for f in os.listdir(self.task_dir) if f.endswith('.json')]
        self.assertEqual(len(json_files), 0, "Task file should be deleted after timeout")

    def test_fallback_flow(self):
        """Test that process_studio_pipeline falls back to VibeVoice on Qwen timeout."""
        print("\nTesting Fallback Flow...")
        
        # Setup Mocks
        segment_words = [{'start': 0, 'end': 3, 'word': 'test'}] # 3s duration -> routes to Qwen
        translation = "Translated text"
        
        self.mock_tokenizer.analyze_segment.return_value = {'token': 'happy', 'confidence': 0.9}
        self.mock_tokenizer.get_director_cues.return_value = "Keep it happy"
        
        self.mock_vibe.perform_transfer.return_value = "vibe_output.wav"
        self.mock_refiner.apply_refinement.return_value = "refined.wav"
        self.mock_refiner.spectral_match.return_value = "final.wav"
        
        # Mock dispatch_to_qwen to return None immediately (to skip waiting in this test)
        # OR specifically test the timeout logic integration.
        # Let's patch dispatch_to_qwen to return None to simulate timeout quickly.
        with patch.object(self.orchestrator, 'dispatch_to_qwen', return_value=None) as mock_dispatch:
            
            result_path, _ = self.orchestrator.process_studio_pipeline(segment_words, translation)
            
            # Verify Qwen was attempted
            mock_dispatch.assert_called_once()
            
            # Verify Vibe Fallback was called
            self.mock_vibe.perform_transfer.assert_called_once()
            print("VibeVoice fallback confirmed.")
            
            self.assertEqual(result_path, "final.wav")

if __name__ == '__main__':
    unittest.main()
