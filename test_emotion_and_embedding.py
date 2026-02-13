import pytest
import tempfile
import os
from pathlib import Path
import numpy as np
import soundfile as sf

@pytest.fixture
def sample_audio_path():
    """Create a sample audio file for testing."""
    tmp_path = tempfile.mktemp(suffix=".wav")
    
    # Create 5 seconds of mock audio data
    sample_rate = 16000
    duration = 5.0
    samples = np.random.randn(int(sample_rate * duration)).astype(np.float32)
    
    sf.write(tmp_path, samples, sample_rate)
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

@pytest.fixture
def tmp_path():
    """Temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_embedding_and_profile(tmp_path, sample_audio_path):
    """Test embedding computation and profile management."""
    from sonora.multichar.embed_manager import compute_embedding, match_or_create_profile
    
    # Test embedding computation
    emb = compute_embedding(sample_audio_path)
    assert isinstance(emb, np.ndarray)
    assert len(emb) > 0  # Should have some dimensions
    
    # Test profile matching/creation
    sid = match_or_create_profile(emb, threshold=0.5)
    assert sid.startswith("spk_")
    assert len(sid) > 4  # Should have some ID number

def test_emotion_inference(sample_audio_path):
    """Test emotion inference from audio."""
    from sonora.multichar.emotion import infer_emotion
    
    emo = infer_emotion(sample_audio_path)
    assert "emotion" in emo
    assert "score" in emo
    assert isinstance(emo["emotion"], str)
    assert isinstance(emo["score"], (int, float))
    assert 0 <= emo["score"] <= 1

def test_emotion_statistics():
    """Test emotion statistics calculation."""
    from sonora.multichar.emotion import get_emotion_statistics
    
    # Test with empty emotions
    empty_stats = get_emotion_statistics([])
    assert empty_stats["total_segments"] == 0
    assert empty_stats["emotion_distribution"] == {}
    assert empty_stats["average_confidence"] == 0.0
    
    # Test with mock emotions
    mock_emotions = [
        {"emotion": "happy", "score": 0.8},
        {"emotion": "sad", "score": 0.7},
        {"emotion": "happy", "score": 0.9},
        {"emotion": "neutral", "score": 0.6}
    ]
    
    stats = get_emotion_statistics(mock_emotions)
    assert stats["total_segments"] == 4
    assert stats["average_confidence"] > 0.0
    assert "happy" in stats["emotion_distribution"]
    assert "sad" in stats["emotion_distribution"]
    assert "neutral" in stats["emotion_distribution"]
    
    # Check happy emotion stats
    happy_stats = stats["emotion_distribution"]["happy"]
    assert happy_stats["count"] == 2
    assert happy_stats["average_confidence"] > 0.0

def test_voice_settings_mapping():
    """Test emotion to voice settings mapping."""
    from sonora.multichar.emotion import map_emotion_to_voice_settings
    
    # Test known emotions
    happy_settings = map_emotion_to_voice_settings("happy")
    assert "pitch" in happy_settings
    assert "speed" in happy_settings
    assert "energy" in happy_settings
    assert happy_settings["pitch"] > 1.0  # Should be higher pitch
    
    sad_settings = map_emotion_to_voice_settings("sad")
    assert sad_settings["pitch"] < 1.0  # Should be lower pitch
    
    # Test unknown emotion
    unknown_settings = map_emotion_to_voice_settings("unknown_emotion")
    assert unknown_settings["pitch"] == 1.0  # Should default to neutral

def test_emotion_prompt_creation():
    """Test emotion-aware prompt creation."""
    from sonora.multichar.emotion import create_emotion_prompt
    
    text = "Hello world"
    
    happy_prompt = create_emotion_prompt("happy", text)
    assert "cheerful" in happy_prompt.lower()
    assert text in happy_prompt
    
    sad_prompt = create_emotion_prompt("sad", text)
    assert "melancholic" in sad_prompt.lower()
    assert text in sad_prompt

def test_profile_management(tmp_path, sample_audio_path):
    """Test speaker profile management."""
    from sonora.multichar.embed_manager import (
        compute_embedding, save_profile, load_profiles, 
        match_or_create_profile, get_speaker_statistics
    )
    
    # Create test embedding
    emb = compute_embedding(sample_audio_path)
    
    # Test profile creation
    speaker_id = "test_speaker_01"
    voice_profile = {"pitch": 1.1, "speed": 1.0}
    metadata = {"gender": "female", "age": "young"}
    
    save_profile(speaker_id, emb, voice_profile, metadata)
    
    # Test profile loading
    profiles = load_profiles()
    assert speaker_id in profiles
    assert profiles[speaker_id]["voice_profile"] == voice_profile
    assert profiles[speaker_id]["metadata"] == metadata
    
    # Test profile matching
    matched_id = match_or_create_profile(emb, threshold=0.9)
    assert matched_id == speaker_id  # Should match existing profile
    
    # Test statistics
    stats = get_speaker_statistics()
    assert stats["total_speakers"] >= 1
    assert any(p["speaker_id"] == speaker_id for p in stats["profiles"])

def test_embedding_similarity():
    """Test embedding similarity calculation."""
    from sonora.multichar.embed_manager import match_or_create_profile
    import numpy as np
    
    # Create two similar embeddings
    emb1 = np.random.randn(256).astype(np.float32)
    emb2 = emb1 + np.random.randn(256).astype(np.float32) * 0.1  # Small noise
    
    # Create two different embeddings
    emb3 = np.random.randn(256).astype(np.float32)
    
    # Test similarity matching
    id1 = match_or_create_profile(emb1, threshold=0.5)
    id2 = match_or_create_profile(emb2, threshold=0.5)
    id3 = match_or_create_profile(emb3, threshold=0.5)
    
    # Similar embeddings should match
    assert id1 == id2
    
    # Different embeddings should create new profiles
    assert id3 != id1

def test_voice_profile_updates():
    """Test voice profile updates."""
    from sonora.multichar.embed_manager import (
        compute_embedding, save_profile, update_voice_profile, load_profiles
    )
    import numpy as np
    
    # Create initial profile
    emb = np.random.randn(256).astype(np.float32)
    speaker_id = "test_speaker_update"
    initial_profile = {"pitch": 1.0, "speed": 1.0}
    
    save_profile(speaker_id, emb, initial_profile)
    
    # Update voice profile
    new_profile = {"pitch": 1.2, "speed": 0.9, "energy": 1.1}
    success = update_voice_profile(speaker_id, new_profile)
    assert success
    
    # Verify update
    profiles = load_profiles()
    assert profiles[speaker_id]["voice_profile"] == new_profile

def test_profile_deletion():
    """Test profile deletion."""
    from sonora.multichar.embed_manager import (
        compute_embedding, save_profile, delete_profile, load_profiles
    )
    import numpy as np
    
    # Create profile
    emb = np.random.randn(256).astype(np.float32)
    speaker_id = "test_speaker_delete"
    
    save_profile(speaker_id, emb)
    assert speaker_id in load_profiles()
    
    # Delete profile
    success = delete_profile(speaker_id)
    assert success
    
    # Verify deletion
    profiles = load_profiles()
    assert speaker_id not in profiles

@pytest.mark.slow
def test_large_embedding_dataset():
    """Test embedding computation with larger dataset."""
    from sonora.multichar.embed_manager import compute_embedding, match_or_create_profile
    import numpy as np
    
    # Create multiple embeddings
    embeddings = []
    for i in range(10):
        emb = np.random.randn(256).astype(np.float32)
        embeddings.append(emb)
    
    # Test profile creation and matching
    profile_ids = []
    for emb in embeddings:
        profile_id = match_or_create_profile(emb, threshold=0.5)
        profile_ids.append(profile_id)
    
    # Should have created multiple profiles
    unique_profiles = set(profile_ids)
    assert len(unique_profiles) > 1

def test_emotion_classifier_initialization():
    """Test emotion classifier initialization."""
    from sonora.multichar.emotion import get_emotion_classifier
    
    classifier = get_emotion_classifier()
    assert classifier is not None

def test_voice_encoder_initialization():
    """Test voice encoder initialization."""
    from sonora.multichar.embed_manager import get_voice_encoder
    
    encoder = get_voice_encoder()
    assert encoder is not None
































