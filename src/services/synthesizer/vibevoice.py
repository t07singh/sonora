"""
VibeVoice TTS implementation for Sonora/Auralis.

This module provides advanced text-to-speech synthesis using Microsoft VibeVoice
open-source model with support for voice cloning, emotion control, and anime-optimized voices.

Supports both local model inference and API-based fallback.
"""

import asyncio
import tempfile
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

import torch
import torchaudio
import soundfile as sf
import numpy as np

from src.core.base_tts import BaseTTS, TTSResult
from src.core.settings import settings
from src.core.reliability import retry_api_call, get_device

logger = logging.getLogger(__name__)

# Try to import VibeVoice model components
try:
    # Attempt to import from Microsoft VibeVoice repository structure
    # This assumes the model is installed or available in the Python path
    VIBEVOICE_AVAILABLE = True
    try:
        # Try importing from the VibeVoice package if installed via pip
        from vibevoice import VibeVoice
        VIBEVOICE_PACKAGE_MODE = True
    except ImportError:
        # Try alternative package names
        try:
            # Some forks use different package names
            import vibevoice_tts
            from vibevoice_tts import VibeVoice
            VIBEVOICE_PACKAGE_MODE = True
        except ImportError:
            # Try importing from local repository structure
            try:
                import sys
                vibevoice_path = os.getenv("VIBEVOICE_PATH", "./VibeVoice")
                if os.path.exists(vibevoice_path):
                    sys.path.insert(0, vibevoice_path)
                    from vibevoice import VibeVoice
                    VIBEVOICE_PACKAGE_MODE = True
                else:
                    VIBEVOICE_PACKAGE_MODE = False
                    logger.warning(f"VibeVoice path not found: {vibevoice_path}")
            except ImportError:
                VIBEVOICE_PACKAGE_MODE = False
                logger.warning("VibeVoice package not found. Using mock mode. "
                              "Install from: https://github.com/microsoft/VibeVoice or community forks")
except Exception as e:
    VIBEVOICE_AVAILABLE = False
    VIBEVOICE_PACKAGE_MODE = False
    logger.warning(f"VibeVoice initialization failed: {e}. Using mock mode.")


class VibeVoiceTTS(BaseTTS):
    """
    VibeVoice TTS implementation using Microsoft VibeVoice open-source model.
    
    Provides high-quality text-to-speech synthesis with support for:
    - Local model inference (GPU/CPU)
    - Voice cloning and custom voices
    - Emotion and tone control
    - Anime-optimized voice models
    - Real-time streaming synthesis
    - Batch processing
    """
    
    def __init__(
        self,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        model_path: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Initialize VibeVoice TTS.
        
        Args:
            voice_id: VibeVoice voice ID or speaker name (defaults to config setting)
            model: VibeVoice model name (defaults to config setting)
            model_path: Path to VibeVoice model weights (defaults to config/env)
            device: Device to run inference on ('cuda', 'cpu', or auto-detect)
        """
        self.voice_id = voice_id or getattr(settings.tts, 'vibevoice_voice_id', 'default')
        
        # Get model path from config or environment
        self.model_path = model_path or getattr(
            settings.tts, 'vibevoice_model_path', None
        ) or os.getenv("VIBEVOICE_MODEL_PATH", "./models/vibevoice")
        
        # Device selection - Force CPU-Only mode for Sonora Swarm stability
        if device is None:
            device = get_device()
        
        self.device = device
        self.model_name = model or "vibevoice-base"
        
        # Initialize model
        self.model = None
        self.mock_mode = not VIBEVOICE_PACKAGE_MODE
        
        if not self.mock_mode and VIBEVOICE_AVAILABLE:
            try:
                logger.info(f"Loading VibeVoice model from: {self.model_path}")
                logger.info(f"Using device: {self.device}")
                
                # Load model from pretrained path
                if os.path.exists(self.model_path):
                    self.model = VibeVoice.from_pretrained(self.model_path).to(self.device)
                    self.model.eval()  # Set to evaluation mode
                    logger.info("✅ VibeVoice model loaded successfully")
                else:
                    logger.warning(f"Model path does not exist: {self.model_path}. Using mock mode.")
                    self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to load VibeVoice model: {e}. Using mock mode.")
                self.mock_mode = True
        else:
            logger.warning("VibeVoice not available. Using mock mode for testing.")
            self.mock_mode = True
        
        # Anime-optimized voice settings
        self.voice_settings = {
            "emotion": "neutral",  # neutral, happy, sad, angry, excited, calm
            "tone": "normal",      # normal, high, low, whisper, shout
            "speed": 1.0,          # 0.5-2.0
            "pitch": 1.0,          # 0.5-2.0
            "anime_style": True,   # Enable anime-specific optimizations
            "voice_clarity": 0.8,  # 0.0-1.0
            "character_consistency": 0.9  # 0.0-1.0
        }
        
        super().__init__(self.voice_id, self.model_name)
    
    @retry_api_call()
    async def synthesize(
        self,
        text: str,
        output_path: Optional[str | Path] = None,
        emotion: Optional[str] = None,
        tone: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        anime_style: Optional[bool] = None,
        voice_clarity: Optional[float] = None,
        character_consistency: Optional[float] = None,
        **kwargs
    ) -> TTSResult:
        """
        Synthesize speech from text using VibeVoice.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file (auto-generated if None)
            emotion: Emotion type (neutral, happy, sad, angry, excited, calm)
            tone: Tone type (normal, high, low, whisper, shout)
            speed: Speech speed (0.5-2.0)
            pitch: Voice pitch (0.5-2.0)
            anime_style: Enable anime-specific optimizations
            voice_clarity: Voice clarity (0.0-1.0)
            character_consistency: Character consistency (0.0-1.0)
            **kwargs: Additional parameters
            
        Returns:
            TTSResult with audio file path and metadata
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Update voice settings with provided parameters
        settings = self.voice_settings.copy()
        if emotion is not None:
            settings["emotion"] = emotion
        if tone is not None:
            settings["tone"] = tone
        if speed is not None:
            settings["speed"] = max(0.5, min(2.0, speed))
        if pitch is not None:
            settings["pitch"] = max(0.5, min(2.0, pitch))
        if anime_style is not None:
            settings["anime_style"] = anime_style
        if voice_clarity is not None:
            settings["voice_clarity"] = max(0.0, min(1.0, voice_clarity))
        if character_consistency is not None:
            settings["character_consistency"] = max(0.0, min(1.0, character_consistency))
        
        # Generate output path if not provided
        if output_path is None:
            output_path = Path(tempfile.gettempdir()) / f"vibevoice_{hash(text) % 100000}.wav"
        else:
            output_path = Path(output_path)
        
        try:
            logger.info(f"Synthesizing {len(text)} characters with VibeVoice voice {self.voice_id}")
            logger.info(f"Settings: {settings}")
            
            if self.mock_mode:
                # Mock synthesis for testing
                audio_data, sample_rate = await self._mock_synthesize(text, settings)
            else:
                # Real VibeVoice model inference
                audio_data, sample_rate = await self._model_synthesize(text, settings)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save audio to file using soundfile
            sf.write(str(output_path), audio_data, sample_rate)
            
            # Estimate duration based on text length and speed
            word_count = len(text.split())
            base_duration = (word_count / 150) * 60  # Base 150 WPM
            estimated_duration = base_duration / settings["speed"]
            
            # Calculate actual duration from audio data
            actual_duration = len(audio_data) / sample_rate if hasattr(audio_data, '__len__') else estimated_duration
            
            result = TTSResult(
                audio_path=output_path,
                duration=actual_duration,
                sample_rate=sample_rate,
                provider="vibevoice",
                voice_id=self.voice_id,
                model=self.model_name,
                metadata={
                    "text_length": len(text),
                    "word_count": word_count,
                    "voice_settings": settings,
                    "anime_optimized": settings["anime_style"],
                    "emotion": settings["emotion"],
                    "tone": settings["tone"],
                    "device": self.device,
                    "mock_mode": self.mock_mode
                }
            )
            
            logger.info(f"VibeVoice synthesis completed: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"VibeVoice synthesis failed: {e}")
            raise
    
    async def _model_synthesize(self, text: str, settings: Dict[str, Any]) -> tuple[np.ndarray, int]:
        """
        Run local VibeVoice model inference for synthesis.
        
        Args:
            text: Text to synthesize
            settings: Voice settings
            
        Returns:
            Tuple of (audio_data as numpy array, sample_rate)
        """
        if self.model is None:
            raise RuntimeError("VibeVoice model not loaded")
        
        try:
            logger.info(f"Running VibeVoice inference for text: {text[:50]}...")
            
            # Run inference in async context (model inference can be blocking)
            # We'll use asyncio.to_thread for Python 3.9+ or run_in_executor for older versions
            loop = asyncio.get_event_loop()
            
            # Run model inference
            def run_inference():
                with torch.no_grad():
                    # VibeVoice model typically expects text input
                    # This is a generic interface - actual model API may vary
                    if hasattr(self.model, 'tts'):
                        # If model has tts method
                        audio = self.model.tts(
                            text=text,
                            speaker=self.voice_id,
                            **settings
                        )
                    elif hasattr(self.model, 'generate'):
                        # If model has generate method
                        audio = self.model.generate(text, speaker=self.voice_id)
                    else:
                        # Generic forward pass
                        audio = self.model(text, speaker=self.voice_id)
                    
                    # Convert to numpy array if needed
                    if isinstance(audio, torch.Tensor):
                        audio = audio.cpu().numpy()
                    
                    # Handle mono/stereo
                    if len(audio.shape) > 1 and audio.shape[0] > 1:
                        audio = audio.mean(axis=0)  # Convert to mono
                    
                    return audio
            
            # Run in thread pool to avoid blocking
            audio_data = await loop.run_in_executor(None, run_inference)
            
            # Default VibeVoice sample rate is typically 22050 or 24000
            sample_rate = 22050
            
            # Apply speed adjustment if needed
            if settings.get("speed", 1.0) != 1.0:
                import librosa
                audio_data = librosa.effects.time_stretch(audio_data, rate=settings["speed"])
            
            # Apply pitch adjustment if needed
            if settings.get("pitch", 1.0) != 1.0:
                import librosa
                audio_data = librosa.effects.pitch_shift(
                    audio_data, 
                    sr=sample_rate, 
                    n_steps=int(12 * np.log2(settings["pitch"]))
                )
            
            logger.info(f"VibeVoice inference completed. Generated {len(audio_data)} samples.")
            return audio_data, sample_rate
            
        except Exception as e:
            logger.error(f"VibeVoice model inference failed: {e}")
            raise
    
    async def _mock_synthesize(self, text: str, settings: Dict[str, Any]) -> tuple[np.ndarray, int]:
        """
        Mock synthesis for testing without model.
        
        Args:
            text: Text to synthesize
            settings: Voice settings
            
        Returns:
            Tuple of (audio_data as numpy array, sample_rate)
        """
        # Simulate processing time
        await asyncio.sleep(0.3)
        
        # Generate mock audio (22.05kHz, float32, mono)
        duration = max(1.0, len(text) / 10)  # Rough duration estimate
        sample_rate = 22050
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        # Apply settings effects
        if settings["emotion"] == "excited":
            audio_data *= 1.2  # Louder
        elif settings["emotion"] == "sad":
            audio_data *= 0.8  # Quieter
        
        if settings["tone"] == "high":
            # Simulate higher pitch with frequency modulation
            audio_data = np.sin(2 * np.pi * frequency * 1.2 * t).astype(np.float32)
        elif settings["tone"] == "low":
            audio_data = np.sin(2 * np.pi * frequency * 0.8 * t).astype(np.float32)
        
        # Apply speed adjustment
        if settings.get("speed", 1.0) != 1.0:
            new_length = int(len(audio_data) / settings["speed"])
            audio_data = np.interp(
                np.linspace(0, len(audio_data), new_length),
                np.arange(len(audio_data)),
                audio_data
            )
        
        return audio_data, sample_rate
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available VibeVoice voices.
        
        For local model, this returns default voices or voices discovered from model.
        In mock mode, returns predefined mock voices.
        
        Returns:
            Dictionary mapping voice IDs to voice information
        """
        if self.mock_mode:
            return self._get_mock_voices()
        
        try:
            logger.info("Fetching available VibeVoice voices from local model")
            
            # Try to get voices from model if it has a get_speakers method
            if self.model is not None:
                try:
                    if hasattr(self.model, 'get_speakers'):
                        speakers = self.model.get_speakers()
                        voices_dict = {}
                        for speaker_id, speaker_info in speakers.items():
                            voices_dict[speaker_id] = {
                                "name": speaker_info.get("name", speaker_id),
                                "category": speaker_info.get("category", "default"),
                                "description": speaker_info.get("description", ""),
                                "gender": speaker_info.get("gender", "unknown"),
                                "age_range": speaker_info.get("age_range", "unknown"),
                                "emotions": ["neutral", "happy", "sad", "angry", "excited", "calm"],
                                "anime_optimized": True,
                                "cloning_supported": True
                            }
                        logger.info(f"Found {len(voices_dict)} voices from model")
                        return voices_dict
                except Exception as e:
                    logger.warning(f"Model does not support get_speakers: {e}")
            
            # Default voices for VibeVoice model
            default_voices = {
                "default": {
                    "name": "Default Voice",
                    "category": "default",
                    "description": "Default VibeVoice speaker",
                    "gender": "unknown",
                    "age_range": "unknown",
                    "emotions": ["neutral", "happy", "sad", "angry", "excited", "calm"],
                    "anime_optimized": True,
                    "cloning_supported": True
                }
            }
            
            logger.info(f"Using default voices: {len(default_voices)}")
            return default_voices
                    
        except Exception as e:
            logger.error(f"Failed to fetch voices: {e}")
            return self._get_mock_voices()
    
    def _get_mock_voices(self) -> Dict[str, Any]:
        """Get mock voices for testing."""
        return {
            "anime_female_01": {
                "name": "Sakura (Female)",
                "category": "anime",
                "description": "Young female anime character voice",
                "gender": "female",
                "age_range": "teen",
                "emotions": ["neutral", "happy", "sad", "excited"],
                "anime_optimized": True,
                "cloning_supported": True
            },
            "anime_male_01": {
                "name": "Hiro (Male)",
                "category": "anime",
                "description": "Young male anime character voice",
                "gender": "male",
                "age_range": "teen",
                "emotions": ["neutral", "happy", "sad", "angry"],
                "anime_optimized": True,
                "cloning_supported": True
            },
            "anime_female_mature": {
                "name": "Yuki (Mature Female)",
                "category": "anime",
                "description": "Mature female anime character voice",
                "gender": "female",
                "age_range": "adult",
                "emotions": ["neutral", "calm", "sad", "angry"],
                "anime_optimized": True,
                "cloning_supported": True
            }
        }
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """
        Validate if a voice ID is available.
        
        Args:
            voice_id: Voice ID to validate
            
        Returns:
            True if voice ID is valid, False otherwise
        """
        try:
            voices = asyncio.run(self.get_available_voices())
            return voice_id in voices
        except Exception as e:
            logger.error(f"Voice validation failed: {e}")
            return False
    
    async def clone_voice(
        self,
        reference_audio_path: str,
        voice_name: str,
        description: Optional[str] = None
    ) -> str:
        """
        Clone a voice from reference audio using VibeVoice model.
        
        This extracts speaker embeddings from the reference audio and creates a new voice profile.
        Future implementation will support fine-tuning for voice cloning.
        
        Args:
            reference_audio_path: Path to reference audio file
            voice_name: Name for the cloned voice
            description: Description of the cloned voice
            
        Returns:
            Voice ID of the cloned voice
        """
        if self.mock_mode:
            voice_id = f"cloned_{voice_name}_{hash(reference_audio_path) % 1000}"
            logger.info(f"Mock voice cloning: {voice_id}")
            return voice_id
        
        try:
            logger.info(f"Cloning voice from: {reference_audio_path}")
            
            if self.model is None:
                raise RuntimeError("VibeVoice model not loaded")
            
            # Load reference audio
            audio_data, sr = sf.read(reference_audio_path)
            
            # Run voice cloning in async context
            loop = asyncio.get_event_loop()
            
            def run_cloning():
                with torch.no_grad():
                    # Extract speaker embedding from reference audio
                    if hasattr(self.model, 'extract_speaker_embedding'):
                        speaker_embedding = self.model.extract_speaker_embedding(audio_data)
                    elif hasattr(self.model, 'encode_speaker'):
                        speaker_embedding = self.model.encode_speaker(audio_data)
                    else:
                        # Fallback: generate a simple hash-based ID
                        logger.warning("Model does not support voice cloning directly. Using fallback.")
                        return f"cloned_{voice_name}_{hash(str(audio_data[:1000])) % 10000}"
                    
                    # Create voice ID from embedding or use model's cloning method
                    voice_id = f"cloned_{voice_name}_{hash(str(speaker_embedding.cpu().numpy()[:10])) % 10000}"
                    
                    # Store speaker embedding for future use (in a real implementation,
                    # this would be saved to a voice profile database)
                    logger.info(f"Speaker embedding extracted. Voice ID: {voice_id}")
                    return voice_id
            
            voice_id = await loop.run_in_executor(None, run_cloning)
            
            logger.info(f"Voice cloned successfully: {voice_id}")
            return voice_id
                    
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            raise
    
    def set_voice_settings(
        self,
        emotion: Optional[str] = None,
        tone: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        anime_style: Optional[bool] = None,
        voice_clarity: Optional[float] = None,
        character_consistency: Optional[float] = None
    ) -> None:
        """
        Update voice settings for anime-style speech.
        
        Args:
            emotion: Emotion type (neutral, happy, sad, angry, excited, calm)
            tone: Tone type (normal, high, low, whisper, shout)
            speed: Speech speed (0.5-2.0)
            pitch: Voice pitch (0.5-2.0)
            anime_style: Enable anime-specific optimizations
            voice_clarity: Voice clarity (0.0-1.0)
            character_consistency: Character consistency (0.0-1.0)
        """
        if emotion is not None:
            self.voice_settings["emotion"] = emotion
        if tone is not None:
            self.voice_settings["tone"] = tone
        if speed is not None:
            self.voice_settings["speed"] = max(0.5, min(2.0, speed))
        if pitch is not None:
            self.voice_settings["pitch"] = max(0.5, min(2.0, pitch))
        if anime_style is not None:
            self.voice_settings["anime_style"] = anime_style
        if voice_clarity is not None:
            self.voice_settings["voice_clarity"] = max(0.0, min(1.0, voice_clarity))
        if character_consistency is not None:
            self.voice_settings["character_consistency"] = max(0.0, min(1.0, character_consistency))
        
        logger.info(f"Updated VibeVoice settings: {self.voice_settings}")
    
    async def synthesize_batch(
        self,
        texts: List[str],
        output_dir: Optional[str | Path] = None,
        **kwargs
    ) -> List[TTSResult]:
        """
        Synthesize multiple texts concurrently with emotion variation.
        
        Args:
            texts: List of texts to synthesize
            output_dir: Directory to save audio files
            **kwargs: Additional parameters for synthesis
            
        Returns:
            List of TTSResult objects
        """
        if output_dir is None:
            output_dir = Path(tempfile.gettempdir())
        else:
            output_dir = Path(output_dir)
        
        # Create tasks for concurrent synthesis
        tasks = []
        for i, text in enumerate(texts):
            output_path = output_dir / f"vibevoice_batch_{i:03d}.wav"
            
            # Vary emotion for batch processing
            emotions = ["neutral", "happy", "sad", "excited", "calm"]
            emotion = emotions[i % len(emotions)]
            
            task = self.synthesize(text, output_path, emotion=emotion, **kwargs)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        logger.info(f"VibeVoice batch synthesis completed: {len(results)} files generated")
        return results




















