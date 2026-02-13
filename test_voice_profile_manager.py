"""
Test Voice Profile Manager

Tests that Voice Profile Manager registers and retrieves voices correctly.
"""

import pytest
from sonora.voice.profile_manager import VoiceProfileManager


class TestVoiceProfileManager:
    """Test Voice Profile Manager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh Voice Profile Manager instance."""
        return VoiceProfileManager()
    
    def test_manager_initialization(self, manager):
        """Test that manager initializes correctly."""
        assert manager.profiles == {}
        assert isinstance(manager.profiles, dict)
    
    def test_register_voice_basic(self, manager):
        """Test basic voice registration."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        
        # Check that voice was registered
        assert name in manager.profiles
        assert manager.profiles[name]["model_id"] == model_id
        assert manager.profiles[name]["params"] == params
    
    def test_register_voice_multiple(self, manager):
        """Test registering multiple voices."""
        voices = [
            ("narrator", "elevenlabs_voice_123", {"speed": 1.0, "pitch": 0.8}),
            ("hero", "vibevoice_model_456", {"emotion": "confident", "age": "young"}),
            ("villain", "openai_voice_789", {"emotion": "menacing", "age": "old"}),
        ]
        
        for name, model_id, params in voices:
            manager.register_voice(name, model_id, params)
        
        # Check all voices were registered
        assert len(manager.profiles) == 3
        
        for name, model_id, params in voices:
            assert name in manager.profiles
            assert manager.profiles[name]["model_id"] == model_id
            assert manager.profiles[name]["params"] == params
    
    def test_get_profile_existing(self, manager):
        """Test getting an existing profile."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        
        profile = manager.get_profile(name)
        
        assert profile is not None
        assert profile["model_id"] == model_id
        assert profile["params"] == params
    
    def test_get_profile_nonexistent(self, manager):
        """Test getting a non-existent profile."""
        profile = manager.get_profile("nonexistent_voice")
        assert profile is None
    
    def test_list_profiles_empty(self, manager):
        """Test listing profiles when none exist."""
        profiles = manager.list_profiles()
        assert profiles == []
    
    def test_list_profiles_with_voices(self, manager):
        """Test listing profiles with registered voices."""
        voices = ["narrator", "hero", "villain"]
        
        for voice in voices:
            manager.register_voice(voice, f"model_{voice}", {"param": "value"})
        
        profiles = manager.list_profiles()
        
        assert len(profiles) == 3
        assert set(profiles) == set(voices)
    
    def test_remove_profile_existing(self, manager):
        """Test removing an existing profile."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        assert name in manager.profiles
        
        result = manager.remove_profile(name)
        
        assert result is True
        assert name not in manager.profiles
    
    def test_remove_profile_nonexistent(self, manager):
        """Test removing a non-existent profile."""
        result = manager.remove_profile("nonexistent_voice")
        assert result is False
    
    def test_update_profile_existing(self, manager):
        """Test updating an existing profile."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        
        # Update model_id
        new_model_id = "vibevoice_model_456"
        result = manager.update_profile(name, model_id=new_model_id)
        
        assert result is True
        assert manager.profiles[name]["model_id"] == new_model_id
        assert manager.profiles[name]["params"] == params  # Should remain unchanged
    
    def test_update_profile_params(self, manager):
        """Test updating profile parameters."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        
        # Update parameters
        new_params = {"speed": 1.2, "volume": 0.9}
        result = manager.update_profile(name, params=new_params)
        
        assert result is True
        assert manager.profiles[name]["model_id"] == model_id  # Should remain unchanged
        assert manager.profiles[name]["params"] == new_params
    
    def test_update_profile_both(self, manager):
        """Test updating both model_id and parameters."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        
        # Update both
        new_model_id = "vibevoice_model_456"
        new_params = {"speed": 1.2, "volume": 0.9}
        result = manager.update_profile(name, model_id=new_model_id, params=new_params)
        
        assert result is True
        assert manager.profiles[name]["model_id"] == new_model_id
        assert manager.profiles[name]["params"] == new_params
    
    def test_update_profile_nonexistent(self, manager):
        """Test updating a non-existent profile."""
        result = manager.update_profile("nonexistent_voice", model_id="new_model")
        assert result is False
    
    def test_get_model_id_existing(self, manager):
        """Test getting model ID for existing voice."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        
        retrieved_model_id = manager.get_model_id(name)
        assert retrieved_model_id == model_id
    
    def test_get_model_id_nonexistent(self, manager):
        """Test getting model ID for non-existent voice."""
        model_id = manager.get_model_id("nonexistent_voice")
        assert model_id is None
    
    def test_get_params_existing(self, manager):
        """Test getting parameters for existing voice."""
        name = "narrator"
        model_id = "elevenlabs_voice_123"
        params = {"speed": 1.0, "pitch": 0.8}
        
        manager.register_voice(name, model_id, params)
        
        retrieved_params = manager.get_params(name)
        assert retrieved_params == params
    
    def test_get_params_nonexistent(self, manager):
        """Test getting parameters for non-existent voice."""
        params = manager.get_params("nonexistent_voice")
        assert params is None
    
    def test_voice_profile_complex_params(self, manager):
        """Test voice profiles with complex parameters."""
        name = "complex_voice"
        model_id = "advanced_model_123"
        complex_params = {
            "speed": 1.0,
            "pitch": 0.8,
            "emotion": "confident",
            "age": "young",
            "accent": "american",
            "style": "conversational",
            "nested": {
                "sub_param": "value",
                "number": 42
            }
        }
        
        manager.register_voice(name, model_id, complex_params)
        
        profile = manager.get_profile(name)
        assert profile["model_id"] == model_id
        assert profile["params"] == complex_params
    
    def test_voice_profile_empty_params(self, manager):
        """Test voice profiles with empty parameters."""
        name = "empty_params_voice"
        model_id = "model_123"
        empty_params = {}
        
        manager.register_voice(name, model_id, empty_params)
        
        profile = manager.get_profile(name)
        assert profile["model_id"] == model_id
        assert profile["params"] == empty_params
    
    def test_voice_profile_special_characters(self, manager):
        """Test voice profiles with special characters in names."""
        special_names = [
            "voice-with-dashes",
            "voice_with_underscores",
            "voice.with.dots",
            "voice with spaces",
            "voice123",
            "VoiceWithCaps",
        ]
        
        for name in special_names:
            model_id = f"model_{name}"
            params = {"param": "value"}
            
            manager.register_voice(name, model_id, params)
            
            # Verify registration
            profile = manager.get_profile(name)
            assert profile is not None
            assert profile["model_id"] == model_id
            assert profile["params"] == params
        
        # Verify all are in the list
        all_profiles = manager.list_profiles()
        assert len(all_profiles) == len(special_names)
        assert set(all_profiles) == set(special_names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])










