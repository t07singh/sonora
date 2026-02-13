"""
Base TTS classes and interfaces for Sonora/Auralis.

This module provides the abstract base classes and data structures
for text-to-speech implementations, ensuring consistent interfaces
across different TTS providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TTSResult:
    """Container for TTS generation results with metadata."""
    
    def __init__(
        self,
        audio_path: str | Path,
        duration: float,
        sample_rate: int,
        provider: str,
        voice_id: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.audio_path = Path(audio_path)
        self.duration = duration
        self.sample_rate = sample_rate
        self.provider = provider
        self.voice_id = voice_id
        self.model = model
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        return (
            f"TTSResult(audio_path={self.audio_path}, "
            f"duration={self.duration:.2f}s, "
            f"provider={self.provider}, "
            f"voice_id={self.voice_id})"
        )


class BaseTTS(ABC):
    """Abstract base class for TTS providers."""
    
    def __init__(self, voice_id: str, model: str):
        """
        Initialize TTS provider.
        
        Args:
            voice_id: Voice identifier for the TTS provider
            model: Model name to use for synthesis
        """
        self.voice_id = voice_id
        self.model = model
        self.provider_name = self.__class__.__name__.replace("TTS", "").lower()
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        output_path: Optional[str | Path] = None,
        **kwargs
    ) -> TTSResult:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file (optional)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            TTSResult with audio file path and metadata
        """
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices.
        
        Returns:
            Dictionary mapping voice IDs to voice information
        """
        pass
    
    @abstractmethod
    def validate_voice_id(self, voice_id: str) -> bool:
        """
        Validate if a voice ID is available.
        
        Args:
            voice_id: Voice ID to validate
            
        Returns:
            True if voice ID is valid, False otherwise
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(voice_id={self.voice_id}, model={self.model})"

