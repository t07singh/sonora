
import asyncio
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from sonora.core.orchestrator import SonoraOrchestrator
from sonora.core.emotion_tokenizer import EmotionTokenizer
from sonora.core.emotional_splicer import EmotionalSplicer
from api.server import ConnectionManager

class TestPhase2(unittest.TestCase):
    
    async def test_websocket_manager_async(self):
        """Async test for WebSocket Connection Manager logic."""
        manager = ConnectionManager()
        # Create an awaitable mock
        mock_ws = MagicMock()
        f = asyncio.Future()
        f.set_result(None)
        mock_ws.accept.return_value = f
        mock_ws.send_json.return_value = f
        
        await manager.connect(mock_ws)
        self.assertIn(mock_ws, manager.active_connections)
        manager.disconnect(mock_ws)
        self.assertNotIn(mock_ws, manager.active_connections)

    def test_websocket_manager(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.test_websocket_manager_async())
        loop.close()

    @patch('sonora.core.orchestrator.get_secure_path', return_value="dummy.wav")
    @patch('sonora.core.orchestrator.VibeVoiceAgent')
    @patch('sonora.core.orchestrator.StepAudioRefiner')
    @patch('sonora.core.emotion_tokenizer.EmotionTokenizer.analyze_segment')
    @patch('sonora.core.emotion_tokenizer.EmotionTokenizer.get_director_cues')
    @patch('sonora.core.emotional_splicer.EmotionalSplicer.auto_detect_artifacts')
    @patch('sonora.core.emotional_splicer.EmotionalSplicer.extract_artifact')
    @patch('sonora.core.emotional_splicer.EmotionalSplicer.inject_to_dub')
    def test_orchestrator_enhancements(self, mock_inject, mock_extract, mock_detect, mock_cues, mock_analyze, mock_refiner, mock_vibe, mock_secure):
        """Verify Orchestrator calls the new components."""
        print("\n--- Verifying Orchestrator Phase 2 Enhancements ---")
        
        # Setup Mocks
        mock_analyze.return_value = {'token': 'excited', 'confidence': 0.95, 'intensity': 0.8}
        mock_cues.return_value = "Emotion: EXCITED. Acoustics: High-pitched tone."
        mock_detect.return_value = [(100, 300)] # One artifact found
        mock_extract.return_value = "artifact_audio_data"
        mock_inject.return_value = "matched.wav_synced.wav"
        
        # Mock Refiner instance
        refiner_instance = mock_refiner.return_value
        refiner_instance.apply_refinement.return_value = "refined.wav"
        refiner_instance.spectral_match.return_value = "matched.wav"
        
        # Mock VibeVoice
        vibe_instance = mock_vibe.return_value
        vibe_instance.perform_transfer.return_value = "dubbed.wav"
        
        # Init Orchestrator
        orch = SonoraOrchestrator("dummy_video.mp4")
        
        # Run Pipeline
        result_path, stats = orch.process_studio_pipeline(
            segment_words=[{"word": "Test", "start": 0, "end": 1}],
            translation="Test Translation"
        )
        
        # Assertions
        self.assertEqual(result_path, "matched.wav_synced.wav") # Synced injected
        
        # 1. Check Director Cues called
        mock_cues.assert_called_once()
        print("[OK] Director Cues extraction: VERIFIED")
        
        # 2. Check Spectral Matching called
        refiner_instance.spectral_match.assert_called_once()
        print("[OK] Spectral Matching: VERIFIED")
        
        # 3. Check Auto Artifact Detection called
        mock_detect.assert_called_once()
        print("[OK] Auto Artifact Detection: VERIFIED")
        
        # 4. Check Injection called
        mock_inject.assert_called_once()
        print("[OK] Emotional Injection: VERIFIED")
        
if __name__ == "__main__":
    unittest.main()
