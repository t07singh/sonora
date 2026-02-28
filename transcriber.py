"""
Audio transcription module for Sonora/Auralis.

Refactored to call the dedicated 'sonora-asr' microservice with hardened retries.
"""

import os
import requests
import logging
import torch
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import performance profiling and resilience
from sonora.utils.perf_timer import PerfTimer, time_function
from sonora.utils.reliability import retry_api_call


class Transcriber:
    """Hardened Local Transcriber using Faster-Whisper."""

    def __init__(self, model_size: str = "large-v3") -> None:
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.use_mock = os.getenv("SONORA_MOCK_MODE", "false").lower() == "true"
        self._model = None
        
        logger = logging.getLogger("transcriber-local")
        logger.info(f"Initialized Transcriber (Model: {model_size}, Device: {self.device})")

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            model_path = "models/whisper"
            os.makedirs(model_path, exist_ok=True)
            self._model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type="float16" if self.device == "cuda" else "int8", 
                download_root=model_path
            )

    @retry_api_call(max_retries=3, base_delay=1)
    def transcribe(self, audio_file: str) -> Dict[str, Any]:
        """
        Transcribes audio by calling the sonora-transcriber microservice.
        """
        if self.use_mock:
            return {
                "text": "こんにちは Hello [laugh]",
                "segments": [],
                "language": "ja"
            }

        # Handle microservice routing
        ASR_URL = os.getenv("TRANSCRIBER_URL", "http://sonora-transcriber:8001/transcribe")
        
        try:
            logger.info(f"🧬 [HANDSHAKE] Routing ASR request to {ASR_URL}")
            
            # Send the filename/path. In the swarm shared volume, 
            # we just need the relative path or the agreed shared path.
            payload = {"filename": audio_file}
            
            response = requests.post(ASR_URL, json=payload, timeout=300) # Long timeout for large-v3
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ [SUCCESS] ASR Microservice Handover Complete.")
            return result
            
        except Exception as e:
            logger.error(f"❌ Microservice ASR failed: {e}")
            # Fallback to local if service is missing? 
            # No, for "All Models Enabled" swarm, we expect the service.
            raise e

    def transcribe_segments(self, audio_file: str) -> List[Dict[str, Any]]:
        """Helper for list-based segment retrieval."""
        result = self.transcribe(audio_file)
        return result.get("segments", [])
