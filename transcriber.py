"""
Audio transcription module for Sonora/Auralis.

Refactored to call the dedicated 'sonora-asr' microservice with hardened retries.
"""

import os
import requests
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import performance profiling and resilience
from sonora.utils.perf_timer import PerfTimer, time_function
from sonora.utils.reliability import retry_api_call


class Transcriber:
    """Hardened Client for the sonora-asr microservice."""

    def __init__(self, service_url: str = None) -> None:
        # Default to internal docker DNS name
        self.service_url = service_url or os.getenv("ASR_SERVICE_URL", "http://sonora-asr:8001")
        self.use_mock = os.getenv("SONORA_MOCK_MODE", "false").lower() == "true"
        
        logger = logging.getLogger("transcriber-client")
        logger.info(f"Initialized Transcriber Client pointing to {self.service_url}")

    @retry_api_call(max_retries=3, base_delay=1)
    @time_function("ASR Microservice Call")
    def _call_asr_service(self, filename: str):
        """Internal method to call the sonora-asr microservice with retry protection."""
        response = requests.post(
            f"{self.service_url}/transcribe",
            json={"file_path": filename},
            timeout=120 # Transcription can take time
        )
        response.raise_for_status()
        return response.json()

    def transcribe(self, audio_file: str) -> Dict[str, Any]:
        """
        Transcribes audio by routing to the dedicated ASR microservice.
        Expects audio_file to be a path relative to the shared data volume.
        """
        if self.use_mock:
            return {
                "text": "こんにちは Hello [laugh]",
                "timestamps": [],
                "language": "ja"
            }

        try:
            # We pass only the filename as the service sees the same /tmp/sonora mount
            filename = os.path.basename(audio_file)
            result = self._call_asr_service(filename)
            
            return {
                "text": result["text"],
                "timestamps": result.get("segments", []),
                "language": result.get("language", "ja")
            }
            
        except Exception as e:
            logging.error(f"ASR Service unreachable or failed after retries: {e}")
            return {
                "text": "[TRANSCRIPTION_FAILED]",
                "timestamps": [],
                "language": "unknown",
                "error": str(e)
            }

    def transcribe_segments(self, audio_file: str) -> List[Dict[str, Any]]:
        """Helper for list-based segment retrieval."""
        result = self.transcribe(audio_file)
        return result.get("timestamps", [])
