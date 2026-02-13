"""
Test VibeVoice Bridge Mock Implementation

Tests that the VibeVoice bridge mock returns valid audio bytes.
"""

import pytest
import asyncio
from sonora.vibevoice.bridge import VibeVoiceBridge


class TestVibeVoiceMock:
    """Test VibeVoice bridge mock functionality."""
    
    def test_bridge_initialization(self):
        """Test that VibeVoice bridge initializes correctly."""
        bridge = VibeVoiceBridge(api_key="test_key")
        
        assert bridge.api_key == "test_key"
        assert bridge.base_url == "https://api.vibevoice.ai"
    
    def test_bridge_initialization_custom_url(self):
        """Test VibeVoice bridge with custom base URL."""
        custom_url = "https://custom.vibevoice.com"
        bridge = VibeVoiceBridge(api_key="test_key", base_url=custom_url)
        
        assert bridge.api_key == "test_key"
        assert bridge.base_url == custom_url
    
    @pytest.mark.asyncio
    async def test_synthesize_returns_bytes(self):
        """Test that synthesize method returns bytes."""
        bridge = VibeVoiceBridge(api_key="test_key")
        
        # Test synthesis
        result = await bridge.synthesize("Hello world", "test_voice")
        
        # Should return bytes (even if empty for mock)
        assert isinstance(result, bytes)
    
    @pytest.mark.asyncio
    async def test_synthesize_with_different_inputs(self):
        """Test synthesize with various inputs."""
        bridge = VibeVoiceBridge(api_key="test_key")
        
        test_cases = [
            ("Hello world", "voice1"),
            ("", "voice2"),
            ("Long text with multiple words and punctuation!", "voice3"),
            ("Special chars: @#$%^&*()", "voice4"),
        ]
        
        for text, voice_id in test_cases:
            result = await bridge.synthesize(text, voice_id)
            assert isinstance(result, bytes)
    
    @pytest.mark.asyncio
    async def test_concurrent_synthesis(self):
        """Test concurrent synthesis calls."""
        bridge = VibeVoiceBridge(api_key="test_key")
        
        # Create multiple concurrent synthesis tasks
        tasks = [
            bridge.synthesize(f"Text {i}", f"voice_{i}")
            for i in range(5)
        ]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # All results should be bytes
        for result in results:
            assert isinstance(result, bytes)
    
    def test_bridge_attributes(self):
        """Test bridge attributes are accessible."""
        bridge = VibeVoiceBridge(api_key="secret_key")
        
        # Test attribute access
        assert hasattr(bridge, 'api_key')
        assert hasattr(bridge, 'base_url')
        assert hasattr(bridge, 'synthesize')
        
        # Test attribute values
        assert bridge.api_key == "secret_key"
        assert bridge.base_url == "https://api.vibevoice.ai"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])










