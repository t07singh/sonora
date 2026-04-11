import os
import logging
from typing import List, Dict, Any
from src.core.shadow_providers import cloud_transcribe, cloud_translate, cloud_generate_voice

logger = logging.getLogger("sonora.shadow")

class ShadowProvider:
    """
    Bridge provider for Cloud-Offload services.
    Enables Zero-GPU execution by routing ASR, Translation, and TTS to APIs.
    """
    
    @staticmethod
    async def transcribe(audio_path: str) -> Dict[str, Any]:
        return await cloud_transcribe(audio_path)
    
    @staticmethod
    async def translate(text: str, target_lang: str) -> str:
        return await cloud_translate(text, target_lang)
    
    @staticmethod
    async def synthesize(text: str, voice_id: str) -> bytes:
        return await cloud_generate_voice(text, voice_id)
