"""
Whisper-based ASR implementation for Sonora/Auralis.

REFACTORED: Now acts as a lightweight client for the sonora-asr microservice.
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.core.settings import settings
from src.core.reliability import retry_api_call

logger = logging.getLogger(__name__)

class TranscriptionResult:
    """Container for transcription results with metadata."""
    def __init__(
        self,
        text: str,
        language: str,
        segments: List[Dict],
        word_timestamps: Optional[List[Dict]] = None
    ):
        self.text = text
        self.language = language
        self.segments = segments
        self.word_timestamps = word_timestamps or []

class WhisperASR:
    """
    Lightweight client for the Whisper ASR microservice.
    """
    
    def __init__(self, service_url: Optional[str] = None):
        """
        Initialize the ASR client.
        
        Args:
            service_url: Endpoint for the ASR service (defaults to internal swarm DNS)
        """
        self.service_url = service_url or os.getenv("ASR_SERVICE_URL", "http://sonora-asr:8000")
        logger.info(f"Initialized ASR Client pointing to {self.service_url}")

    @retry_api_call(max_retries=3, base_delay=2.0)
    def transcribe(
        self,
        audio_path: str | Path,
        language: Optional[str] = None,
        word_timestamps: Optional[bool] = None
    ) -> TranscriptionResult:
        """
        Routes transcription request to the sonora-asr microservice.
        """
        # Ensure we send just the filename or relative path within the shared volume
        audio_filename = os.path.basename(str(audio_path))
        
        logger.info(f"Dispatching ASR request for {audio_filename} to microservice...")
        
        try:
            response = requests.post(
                f"{self.service_url}/transcribe",
                json={"audio_path": audio_filename},
                timeout=300 # Whisper can take significant time for long clips
            )
            response.raise_for_status()
            result = response.json()
            
            return TranscriptionResult(
                text=result["text"],
                language=result["language"],
                segments=result["segments"],
                word_timestamps=result.get("word_timestamps", [])
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ASR microservice request failed: {e}")
            raise

    def detect_language(self, audio_path: str | Path) -> str:
        """
        Detects language by calling the microservice.
        """
        result = self.transcribe(audio_path)
        return result.language
