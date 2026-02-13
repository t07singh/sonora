"""
Test suite for Phase 6: Advanced AI Features

Tests the enhanced AI capabilities including VibeVoice TTS,
advanced lip-sync, real-time processing, and quality assessment.
"""

import pytest
import asyncio
import tempfile
import os
import time
from pathlib import Path
import json

# Test imports
from sonora.tts.vibevoice_tts import VibeVoiceTTS
from sonora.video_sync.advanced_lipsync import AdvancedLipSyncEngine, LipSyncQuality
from sonora.processing.realtime_engine import RealTimeProcessingEngine, ProcessingStage


class TestVibeVoiceTTS:
    """Test VibeVoice TTS functionality."""
    
    @pytest.fixture
    def vibevoice_tts(self):
        """Create VibeVoice TTS instance for testing."""
        return VibeVoiceTTS(
            voice_id="anime_female_01",
            model="vibe-voice-v2",
            api_key=None  # Mock mode
        )
    
    @pytest.mark.asyncio
    async def test_vibevoice_synthesis(self, vibevoice_tts):
        """Test basic voice synthesis."""
        text = "Hello, this is a test of VibeVoice TTS."
        
        result = await vibevoice_tts.synthesize(text)
        
        assert result.provider == "vibevoice"
        assert result.voice_id == "anime_female_01"
        assert result.audio_path.exists()
        assert result.duration > 0
        assert result.sample_rate == 44100
        assert "anime_optimized" in result.metadata
    
    @pytest.mark.asyncio
    async def test_emotion_control(self, vibevoice_tts):
        """Test emotion control in voice synthesis."""
        text = "I am very excited about this!"
        
        # Test different emotions
        emotions = ["neutral", "happy", "excited", "sad"]
        results = []
        
        for emotion in emotions:
            result = await vibevoice_tts.synthesize(text, emotion=emotion)
            results.append(result)
            assert result.metadata["emotion"] == emotion
        
        # All results should be different (in real implementation)
        assert len(results) == len(emotions)
    
    @pytest.mark.asyncio
    async def test_voice_settings(self, vibevoice_tts):
        """Test voice settings configuration."""
        # Test setting voice parameters
        vibevoice_tts.set_voice_settings(
            emotion="excited",
            tone="high",
            speed=1.2,
            pitch=1.1,
            anime_style=True
        )
        
        assert vibevoice_tts.voice_settings["emotion"] == "excited"
        assert vibevoice_tts.voice_settings["tone"] == "high"
        assert vibevoice_tts.voice_settings["speed"] == 1.2
        assert vibevoice_tts.voice_settings["pitch"] == 1.1
        assert vibevoice_tts.voice_settings["anime_style"] is True
    
    @pytest.mark.asyncio
    async def test_batch_synthesis(self, vibevoice_tts):
        """Test batch voice synthesis."""
        texts = [
            "First sentence for testing.",
            "Second sentence with different content.",
            "Third sentence to complete the batch."
        ]
        
        results = await vibevoice_tts.synthesize_batch(texts)
        
        assert len(results) == len(texts)
        for i, result in enumerate(results):
            assert result.provider == "vibevoice"
            assert result.audio_path.exists()
            # Should have different emotions
            assert result.metadata["emotion"] in ["neutral", "happy", "sad", "excited", "calm"]
    
    @pytest.mark.asyncio
    async def test_available_voices(self, vibevoice_tts):
        """Test getting available voices."""
        voices = await vibevoice_tts.get_available_voices()
        
        assert isinstance(voices, dict)
        assert len(voices) > 0
        
        # Check voice structure
        for voice_id, voice_info in voices.items():
            assert "name" in voice_info
            assert "category" in voice_info
            assert "anime_optimized" in voice_info
            assert "emotions" in voice_info


class TestAdvancedLipSync:
    """Test advanced lip-sync functionality."""
    
    @pytest.fixture
    def lip_sync_engine(self):
        """Create advanced lip-sync engine for testing."""
        return AdvancedLipSyncEngine(
            model_type="mock",  # Use mock for testing
            quality_mode="balanced",
            enable_gpu=False
        )
    
    @pytest.fixture
    def test_video_audio(self):
        """Create test video and audio files."""
        # Create temporary test files
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "test_video.mp4")
        audio_path = os.path.join(temp_dir, "test_audio.wav")
        
        # Create mock files (in real tests, these would be actual media files)
        with open(video_path, 'wb') as f:
            f.write(b"mock video data")
        with open(audio_path, 'wb') as f:
            f.write(b"mock audio data")
        
        yield video_path, audio_path
        
        # Cleanup
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
        except Exception as e:
            # Ignore cleanup errors
            pass
    
    @pytest.mark.asyncio
    async def test_lip_sync_processing(self, lip_sync_engine, test_video_audio):
        """Test lip-sync processing."""
        video_path, audio_path = test_video_audio
        output_path = video_path.replace(".mp4", "_lipsync.mp4")
        
        result = await lip_sync_engine.sync_lips_advanced(video_path, audio_path, output_path)
        
        # Check that we got a LipSyncResult
        from sonora.video_sync.advanced_lipsync import LipSyncResult
        assert isinstance(result, LipSyncResult)
        assert result.output_path == output_path
        assert 0.0 <= result.quality_score <= 1.0
        assert result.quality_level in LipSyncQuality
        assert result.processing_time > 0
        assert result.model_used == "mock"
        assert isinstance(result.metrics, dict)
        assert isinstance(result.warnings, list)
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, lip_sync_engine, test_video_audio):
        """Test quality assessment functionality."""
        video_path, audio_path = test_video_audio
        output_path = video_path.replace(".mp4", "_lipsync.mp4")
        
        result = await lip_sync_engine.sync_lips_advanced(video_path, audio_path, output_path)
        
        # Check quality metrics
        metrics = result.metrics
        assert "overall_score" in metrics
        assert "visual_quality" in metrics
        assert "sync_quality" in metrics
        assert "face_consistency" in metrics
        assert "processing_efficiency" in metrics
        assert "anime_compatibility" in metrics
        
        # All metrics should be between 0 and 1
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                assert 0.0 <= metric_value <= 1.0
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, lip_sync_engine):
        """Test batch lip-sync processing."""
        # Create multiple test pairs
        temp_dir = tempfile.mkdtemp()
        video_audio_pairs = []
        
        for i in range(3):
            video_path = os.path.join(temp_dir, f"test_video_{i}.mp4")
            audio_path = os.path.join(temp_dir, f"test_audio_{i}.wav")
            
            with open(video_path, 'wb') as f:
                f.write(f"mock video data {i}".encode())
            with open(audio_path, 'wb') as f:
                f.write(f"mock audio data {i}".encode())
            
            video_audio_pairs.append((video_path, audio_path))
        
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process batch
        results = await lip_sync_engine.batch_sync_lips(video_audio_pairs, output_dir)
        
        assert len(results) == len(video_audio_pairs)
        for result in results:
            assert result.model_used == "mock"
            assert result.quality_score >= 0.0
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_model_selection(self):
        """Test automatic model selection."""
        # Test different quality modes
        for quality_mode in ["fast", "balanced", "high_quality"]:
            engine = AdvancedLipSyncEngine(
                model_type="auto",
                quality_mode=quality_mode,
                enable_gpu=False
            )
            
            assert engine.selected_model in engine.available_models
            assert engine.quality_mode == quality_mode
    
    def test_model_info(self, lip_sync_engine):
        """Test getting model information."""
        info = lip_sync_engine.get_model_info()
        
        assert "available_models" in info
        assert "selected_model" in info
        assert "quality_mode" in info
        assert "gpu_enabled" in info
        assert "model_configs" in info
        assert "quality_thresholds" in info


class TestRealTimeProcessing:
    """Test real-time processing functionality."""
    
    @pytest.fixture
    def realtime_engine(self):
        """Create real-time processing engine for testing."""
        return RealTimeProcessingEngine(
            chunk_size=1024,
            update_interval=0.1,
            max_concurrent_tasks=2,
            enable_preview=True
        )
    
    @pytest.fixture
    def test_video(self):
        """Create test video file."""
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "test_video.mp4")
        
        with open(video_path, 'wb') as f:
            f.write(b"mock video data for real-time processing")
        
        yield video_path
        
        os.remove(video_path)
        os.rmdir(temp_dir)
    
    @pytest.mark.asyncio
    async def test_realtime_processing_flow(self, realtime_engine, test_video):
        """Test complete real-time processing flow."""
        session_id = "test_session_001"
        target_language = "en"
        voice_settings = {"emotion": "happy", "tone": "normal"}
        
        updates = []
        
        async for update in realtime_engine.process_video_realtime(
            session_id, test_video, target_language, voice_settings
        ):
            updates.append(update)
            
            # Check update structure
            assert update.stage in ProcessingStage
            assert 0.0 <= update.progress <= 1.0
            assert isinstance(update.message, str)
            assert update.timestamp > 0
        
        # Should have multiple updates
        assert len(updates) > 5
        
        # Check processing stages
        stages = [update.stage for update in updates]
        assert ProcessingStage.INITIALIZING in stages
        assert ProcessingStage.COMPLETED in stages or ProcessingStage.ERROR in stages
        
        # Progress should generally increase
        progress_values = [update.progress for update in updates]
        assert max(progress_values) >= 0.9  # Should reach near completion
    
    @pytest.mark.asyncio
    async def test_audio_streaming(self, realtime_engine):
        """Test audio streaming functionality."""
        # Create test audio file
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "test_audio.wav")
        
        # Create a simple WAV file
        import wave
        import numpy as np
        
        sample_rate = 44100
        duration = 2.0
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        with wave.open(audio_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        # Test streaming
        chunks = []
        async for chunk in realtime_engine.stream_audio_chunks(audio_path, chunk_duration=0.5):
            chunks.append(chunk)
            
            assert chunk.chunk_id >= 0
            assert isinstance(chunk.data, bytes)
            assert chunk.timestamp > 0
            assert isinstance(chunk.metadata, dict)
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Last chunk should be final
        assert chunks[-1].is_final is True
        
        # Cleanup
        os.remove(audio_path)
        os.rmdir(temp_dir)
    
    @pytest.mark.asyncio
    async def test_preview_generation(self, realtime_engine, test_video):
        """Test preview generation functionality."""
        session_id = "test_preview_session"
        
        # Initialize session
        realtime_engine.active_sessions[session_id] = {
            "video_path": test_video,
            "start_time": time.time(),
            "temp_dir": tempfile.mkdtemp(),
            "chunks": [],
            "preview_chunks": []
        }
        
        try:
            chunks = []
            async for chunk in realtime_engine.generate_preview_chunks(test_video, session_id):
                chunks.append(chunk)
                
                assert chunk.chunk_id >= 0
                assert isinstance(chunk.data, bytes)
                assert chunk.timestamp > 0
                assert chunk.metadata["type"] in ["preview_frame", "preview_complete"]
            
            # Should have preview chunks
            assert len(chunks) > 0
            
            # Last chunk should be final
            assert chunks[-1].is_final is True
            assert chunks[-1].metadata["type"] == "preview_complete"
            
        finally:
            # Cleanup
            if session_id in realtime_engine.active_sessions:
                import shutil
                temp_dir = realtime_engine.active_sessions[session_id]["temp_dir"]
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                del realtime_engine.active_sessions[session_id]
    
    def test_engine_stats(self, realtime_engine):
        """Test engine statistics."""
        stats = realtime_engine.get_engine_stats()
        
        assert "active_sessions" in stats
        assert "websocket_connections" in stats
        assert "max_concurrent_tasks" in stats
        assert "chunk_size" in stats
        assert "update_interval" in stats
        assert "enable_preview" in stats
        
        assert stats["active_sessions"] == 0
        assert stats["websocket_connections"] == 0
        assert stats["max_concurrent_tasks"] == 2
        assert stats["chunk_size"] == 1024
        assert stats["enable_preview"] is True


class TestAIIntegration:
    """Test integration between AI components."""
    
    @pytest.mark.asyncio
    async def test_tts_lipsync_integration(self):
        """Test integration between TTS and lip-sync."""
        # Create TTS instance
        tts = VibeVoiceTTS(voice_id="anime_female_01", api_key=None)
        
        # Create lip-sync engine
        lip_sync_engine = AdvancedLipSyncEngine(model_type="mock")
        
        # Create test files
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "test_video.mp4")
        
        with open(video_path, 'wb') as f:
            f.write(b"mock video data")
        
        try:
            # Synthesize voice
            tts_result = await tts.synthesize("Test integration between TTS and lip-sync.")
            
            # Perform lip-sync
            output_path = os.path.join(temp_dir, "integrated_output.mp4")
            lip_sync_result = await lip_sync_engine.sync_lips_advanced(
                video_path, tts_result.audio_path, output_path
            )
            
            # Verify integration
            assert lip_sync_result.output_path == output_path
            assert lip_sync_result.quality_score > 0
            assert tts_result.provider == "vibevoice"
            assert lip_sync_result.model_used == "mock"
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_realtime_tts_integration(self):
        """Test real-time processing with TTS integration."""
        realtime_engine = RealTimeProcessingEngine()
        tts = VibeVoiceTTS(api_key=None)
        
        # Create test video
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "test_video.mp4")
        
        with open(video_path, 'wb') as f:
            f.write(b"mock video data")
        
        try:
            session_id = "integration_test"
            updates = []
            
            async for update in realtime_engine.process_video_realtime(
                session_id, video_path, "en", {"emotion": "excited"}
            ):
                updates.append(update)
                
                # Check that TTS stage is included
                if update.stage == ProcessingStage.SYNTHESIZING:
                    assert "synthesizing" in update.message.lower()
            
            # Should have gone through synthesis stage
            synthesis_stages = [u for u in updates if u.stage == ProcessingStage.SYNTHESIZING]
            assert len(synthesis_stages) > 0
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)


# Performance and stress tests
class TestAIPerformance:
    """Test AI features performance and stress testing."""
    
    @pytest.mark.asyncio
    async def test_concurrent_tts_requests(self):
        """Test concurrent TTS requests."""
        tts = VibeVoiceTTS(api_key=None)
        
        # Create multiple concurrent requests
        texts = [f"Concurrent test text {i}" for i in range(5)]
        
        start_time = time.time()
        results = await asyncio.gather(*[
            tts.synthesize(text) for text in texts
        ])
        end_time = time.time()
        
        # All requests should complete
        assert len(results) == len(texts)
        for result in results:
            assert result.provider == "vibevoice"
            assert result.audio_path.exists()
        
        # Should complete in reasonable time
        processing_time = end_time - start_time
        assert processing_time < 10.0  # Should complete within 10 seconds
    
    @pytest.mark.asyncio
    async def test_large_batch_processing(self):
        """Test processing large batches."""
        lip_sync_engine = AdvancedLipSyncEngine(model_type="mock")
        
        # Create many test pairs
        temp_dir = tempfile.mkdtemp()
        video_audio_pairs = []
        
        for i in range(10):  # Large batch
            video_path = os.path.join(temp_dir, f"test_video_{i}.mp4")
            audio_path = os.path.join(temp_dir, f"test_audio_{i}.wav")
            
            with open(video_path, 'wb') as f:
                f.write(f"mock video data {i}".encode())
            with open(audio_path, 'wb') as f:
                f.write(f"mock audio data {i}".encode())
            
            video_audio_pairs.append((video_path, audio_path))
        
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            start_time = time.time()
            results = await lip_sync_engine.batch_sync_lips(video_audio_pairs, output_dir)
            end_time = time.time()
            
            # All should complete
            assert len(results) == len(video_audio_pairs)
            
            # Should complete in reasonable time
            processing_time = end_time - start_time
            assert processing_time < 30.0  # Should complete within 30 seconds
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

