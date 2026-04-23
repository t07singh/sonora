"""
Audio transcription module for Sonora/Auralis.

Refactored to call the dedicated 'sonora-asr' microservice with hardened retries.
"""

import os
import requests
import logging
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import performance profiling and resilience
from sonora.utils.perf_timer import PerfTimer, time_function
from sonora.utils.reliability import retry_api_call

logger = logging.getLogger("sonora.transcriber")


class Transcriber:
    """Hardened Local Transcriber using Faster-Whisper."""

    def __init__(self, model_size: str = "large-v3") -> None:
        self.model_size = model_size
        self.device = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"
        self.use_mock = os.getenv("SONORA_MOCK_MODE", "false").lower() == "true"
        self._model = None
        
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
        Transcribes audio by calling Cloud Groq ASR or the sonora-transcriber microservice.
        """
        if self.use_mock:
            return {
                "text": "こんにちは Hello [laugh]",
                "segments": [],
                "language": "ja"
            }

        # --- CLOUD OFFLOAD BRANCH (Zero-GPU) ---
        cloud_offload = os.getenv("CLOUD_OFFLOAD", "false").lower() == "true"
        if cloud_offload:
            logger.info("⚡ [CLOUD OFFLOAD] Routing ASR to Groq (Whisper Large-v3)...")
            from src.core.shadow_providers import cloud_run_transcription
            words = cloud_run_transcription(audio_file)
            
            # Formulate a basic transcription result from word-level stats
            full_text = " ".join([w['word'] for w in words])
            return {
                "text": full_text,
                "segments": [{"text": full_text, "start": words[0]['start'], "end": words[-1]['end'], "words": words}] if words else [],
                "language": "en" # Default to English for cloud
            }

        # --- SWARM MICROSERVICE BRANCH ---
        ASR_URL = os.getenv("TRANSCRIBER_URL", "http://sonora-transcriber:8001/transcribe")
        
        # Security: If hostname is Docker-specific and we seem to be on Windows/Local, skip or wrap
        is_docker_url = "sonora-transcriber" in ASR_URL
        
        try:
            if is_docker_url and os.name == 'nt':
                 logger.warning("🧪 [ASR] Detected Docker-internal URL on Windows. Skipping handshake to avoid DNS stall.")
                 raise requests.exceptions.ConnectionError("Docker host unreachable on local OS")

            logger.info(f"🧬 [HANDSHAKE] Routing ASR request to {ASR_URL}")
            
            # Send the filename/path
            payload = {"filename": audio_file}
            
            response = requests.post(ASR_URL, json=payload, timeout=3600)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ [SUCCESS] ASR Microservice Handover Complete.")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ [RESILIENCE] Microservice ASR failed or unreachable ({type(e).__name__}: {e}).")
            
            # --- EMERGENCY CLOUD FALLBACK ---
            # Even if cloud_offload was False, if we have keys and the microservice is down, 
            # we should TRY cloud before giving up entirely.
            if not cloud_offload:
                has_cloud_keys = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
                if has_cloud_keys:
                    logger.info("📡 [EMERGENCY] Microservice unreachable. Forcing Cloud Fallback (Keys detected)...")
                    try:
                        from src.core.shadow_providers import cloud_run_transcription
                        words = cloud_run_transcription(audio_file)
                        if words:
                           full_text = " ".join([w['word'] for w in words])
                           return {
                                "text": full_text,
                                "segments": [{"text": full_text, "start": words[0]['start'], "end": words[-1]['end'], "words": words}],
                                "language": "en"
                           }
                    except Exception as cloud_err:
                        logger.error(f"❌ [CRITICAL] Emergency Cloud Fallback also failed: {cloud_err}")
                
                # If still no luck, try local load
                logger.info("📡 [FALLBACK] Attempting local model load (Requires GPU/VRAM)...")
                try:
                    self._load_model()
                    segments, info = self._model.transcribe(audio_file, beam_size=5)
                    
                    segments_list = []
                    full_text = ""
                    for s in segments:
                        full_text += s.text + " "
                        segments_list.append({
                            "text": s.text,
                            "start": s.start,
                            "end": s.end
                        })
                    
                    return {
                        "text": full_text.strip(),
                        "segments": segments_list,
                        "language": info.language
                    }
                except Exception as local_err:
                    logger.error(f"❌ [CRITICAL] Local fallback also failed: {local_err}")
                    raise local_err
            
            # If Cloud Offload was expected but somehow we got here, re-raise the connection error
            raise e

    def transcribe_segments(self, audio_file: str) -> List[Dict[str, Any]]:
        """Helper for list-based segment retrieval."""
        result = self.transcribe(audio_file)
        return result.get("segments", [])
