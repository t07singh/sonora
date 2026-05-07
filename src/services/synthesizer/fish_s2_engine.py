import os
import logging
import requests
import numpy as np
import io
import soundfile as sf
from typing import Tuple

logger = logging.getLogger("sonora.synthesizer.fish_s2")

class FishS2Engine:
    """
    Fish Audio S2 Engine — Primary Engine for Main Character Dialogue.
    Provides high-fidelity emotional prosody and character-specific cloning.
    """
    
    def __init__(self):
        self.api_key = os.getenv("FISHAUDIO_API_KEY")
        self.api_url = "https://api.fish.audio/v1/tts"
        self.is_ready = self.api_key is not None
        
        if not self.is_ready:
            logger.warning("⚠️ FISHAUDIO_API_KEY missing. FishS2 will run in MOCK mode.")

    def generate(self, text: str, voice_id: str, emotion: str = "Neutral") -> Tuple[np.ndarray, int]:
        """
        Generate high-fidelity speech using Fish Audio S2.
        """
        if not self.is_ready:
            return self._mock_generate(text)
            
        logger.info(f"🐟 [FISH_S2] Synthesizing: '{text[:30]}...' [Voice: {voice_id}]")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "reference_id": voice_id, # Mapping to Fish Audio reference IDs
                "format": "wav",
                "latency": "balanced",
                "prosody": {
                    "emotion": emotion
                }
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            # Read WAV from response
            audio_io = io.BytesIO(response.content)
            data, sr = sf.read(audio_io)
            
            return data.astype(np.float32), sr
            
        except Exception as e:
            logger.error(f"❌ Fish Audio S2 failed: {e}")
            return self._mock_generate(text)

    def _mock_generate(self, text: str) -> Tuple[np.ndarray, int]:
        """Safety fallback if API fails or key is missing."""
        sr = 44100
        duration = 1.0 + (len(text) / 15.0)
        t = np.linspace(0, duration, int(sr * duration))
        # Slightly more complex wave than simple sine to distinguish from Qwen3
        audio = (np.sin(2 * np.pi * 440 * t) * 0.5 + np.sin(2 * np.pi * 880 * t) * 0.2).astype(np.float32)
        return audio, sr
