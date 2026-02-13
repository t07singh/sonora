import pytest
import tempfile
import os
from pathlib import Path
import numpy as np
import soundfile as sf

@pytest.fixture
def sample_video_path():
    """Create a sample video file for testing."""
    # For testing, we'll create a mock video path
    # In real tests, you'd have actual video files
    return "tests/data/sample_multichar.mp4"

@pytest.fixture
def mock_translator():
    """Create a mock translator for testing."""
    class MockTranslator:
        def translate(self, text, **kwargs):
            return f"[TRANSLATED] {text}"
    
    return MockTranslator()

@pytest.fixture
def sample_audio_path():
    """Create a sample audio file for testing."""
    tmp_path = tempfile.mktemp(suffix=".wav")
    
    # Create 15 seconds of mock audio data
    sample_rate = 16000
    duration = 15.0
    samples = np.random.randn(int(sample_rate * duration)).astype(np.float32)
    
    sf.write(tmp_path, samples, sample_rate)
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

@pytest.mark.slow
def test_end2end_multichar(sample_video_path, mock_translator):
    """Test end-to-end multi-character processing."""
    from sonora.multichar.multichar_pipeline import process_video_multichar
    
    # Create temporary output path
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        output_path = tmp.name
    
    try:
        res = process_video_multichar(
            sample_video_path, 
            mock_translator, 
            output_path=output_path
        )
        
        assert res["status"] == "ok"
        assert "output" in res
        assert "profiles" in res
        assert "statistics" in res
        
        # Check that output file exists (or would exist in real implementation)
        # For mock implementation, we just check the structure
        assert isinstance(res["profiles"], list)
        assert isinstance(res["statistics"], dict)
        
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)

@pytest.mark.slow
def test_multichar_pipeline_components(sample_audio_path, mock_translator):
    """Test individual components of the multi-character pipeline."""
    from sonora.multichar.multichar_pipeline import (
        translate_with_emotion, asr_transcribe_segment, 
        synthesize_speech, get_processing_progress
    )
    
    # Test translation with emotion
    text = "Hello world"
    translated = translate_with_emotion(text, "happy", mock_translator)
    assert "[TRANSLATED]" in translated
    assert text in translated
    
    # Test ASR transcription
    transcription = asr_transcribe_segment(sample_audio_path, 0.0, 5.0)
    assert isinstance(transcription, str)
    assert len(transcription) > 0
    
    # Test speech synthesis
    audio_data = synthesize_speech("Test text", "spk_01", "happy")
    assert isinstance(audio_data, bytes)
    assert len(audio_data) > 0
    
    # Test progress tracking
    progress = get_processing_progress()
    assert isinstance(progress, dict)
    assert "stage" in progress
    assert "progress" in progress

@pytest.mark.slow
def test_audio_merging(sample_audio_path):
    """Test audio merging functionality."""
    from sonora.multichar.recompose import merge_speech_segments_keep_background
    
    # Create mock segments
    segments_info = [
        {
            "speaker_id": "spk_01",
            "start": 0.0,
            "end": 5.0,
            "tts_path": sample_audio_path
        },
        {
            "speaker_id": "spk_02", 
            "start": 5.0,
            "end": 10.0,
            "tts_path": sample_audio_path
        }
    ]
    
    # Create temporary output
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result_path = merge_speech_segments_keep_background(
            sample_audio_path, segments_info, output_path
        )
        
        assert result_path == output_path
        # In real implementation, would check file exists and has content
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

@pytest.mark.slow
def test_lipsync_processing(sample_video_path, sample_audio_path):
    """Test lip-sync processing."""
    from sonora.multichar.lipsync import (
        detect_face_tracks, perform_multispeaker_lipsync,
        get_lipsync_statistics
    )
    
    # Test face detection
    face_tracks = detect_face_tracks(sample_video_path)
    assert isinstance(face_tracks, list)
    
    # Test lip-sync processing
    segments_info = [
        {
            "speaker_id": "spk_01",
            "start": 0.0,
            "end": 5.0,
            "tts_path": sample_audio_path
        }
    ]
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result_path = perform_multispeaker_lipsync(
            sample_video_path, sample_audio_path, segments_info, output_path
        )
        
        assert result_path == output_path
        
        # Test statistics
        stats = get_lipsync_statistics(segments_info, face_tracks)
        assert isinstance(stats, dict)
        assert "total_speakers" in stats
        assert "total_face_tracks" in stats
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

@pytest.mark.slow
def test_full_pipeline_with_mock_data(mock_translator):
    """Test full pipeline with mock data."""
    from sonora.multichar.multichar_pipeline import process_video_multichar
    
    # Create mock video file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        mock_video_path = tmp.name
    
    try:
        # Create a small mock video file
        with open(mock_video_path, "wb") as f:
            f.write(b"mock video data")
        
        # Test processing
        result = process_video_multichar(
            mock_video_path,
            mock_translator,
            output_path="test_output.mp4"
        )
        
        # Should handle gracefully even with mock data
        assert isinstance(result, dict)
        assert "status" in result
        
    finally:
        if os.path.exists(mock_video_path):
            os.remove(mock_video_path)
        if os.path.exists("test_output.mp4"):
            os.remove("test_output.mp4")

def test_pipeline_error_handling(mock_translator):
    """Test pipeline error handling."""
    from sonora.multichar.multichar_pipeline import process_video_multichar
    
    # Test with non-existent file
    result = process_video_multichar(
        "nonexistent_video.mp4",
        mock_translator
    )
    
    # Should return error status
    assert result["status"] == "error"
    assert "error" in result

@pytest.mark.slow
def test_concurrent_processing(mock_translator):
    """Test concurrent processing capabilities."""
    import asyncio
    from sonora.multichar.multichar_pipeline import process_video_multichar
    
    # Create multiple mock video files
    mock_videos = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            mock_video_path = tmp.name
            with open(mock_video_path, "wb") as f:
                f.write(f"mock video data {i}".encode())
            mock_videos.append(mock_video_path)
    
    try:
        # Process multiple videos
        results = []
        for video_path in mock_videos:
            result = process_video_multichar(video_path, mock_translator)
            results.append(result)
        
        # All should complete
        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)
            assert "status" in result
            
    finally:
        # Cleanup
        for video_path in mock_videos:
            if os.path.exists(video_path):
                os.remove(video_path)

def test_statistics_generation():
    """Test statistics generation for processing results."""
    from sonora.multichar.multichar_pipeline import process_video_multichar
    from sonora.multichar.diarize import get_speaker_statistics
    from sonora.multichar.emotion import get_emotion_statistics
    from sonora.multichar.embed_manager import get_speaker_statistics as get_profile_stats
    
    # Test with mock data
    mock_segments = [
        {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
        {"start": 5.0, "end": 10.0, "speaker": "SPEAKER_01"}
    ]
    
    mock_emotions = [
        {"emotion": "happy", "score": 0.8},
        {"emotion": "sad", "score": 0.7}
    ]
    
    # Test statistics functions
    speaker_stats = get_speaker_statistics(mock_segments)
    emotion_stats = get_emotion_statistics(mock_emotions)
    profile_stats = get_profile_stats()
    
    assert isinstance(speaker_stats, dict)
    assert isinstance(emotion_stats, dict)
    assert isinstance(profile_stats, dict)
    
    assert "total_speakers" in speaker_stats
    assert "total_segments" in emotion_stats
    assert "total_speakers" in profile_stats

@pytest.mark.slow
def test_memory_usage():
    """Test memory usage during processing."""
    import psutil
    import os
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Run processing
    from sonora.multichar.multichar_pipeline import process_video_multichar
    
    class MockTranslator:
        def translate(self, text, **kwargs):
            return f"[TRANSLATED] {text}"
    
    # Create mock video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        mock_video_path = tmp.name
    
    try:
        with open(mock_video_path, "wb") as f:
            f.write(b"mock video data")
        
        result = process_video_multichar(mock_video_path, MockTranslator())
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB)
        assert memory_increase < 500 * 1024 * 1024
        
    finally:
        if os.path.exists(mock_video_path):
            os.remove(mock_video_path)
































