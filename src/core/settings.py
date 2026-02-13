"""
Configuration settings for Sonora/Auralis AI Dubbing System.

This module provides centralized configuration management with support for
environment variables and config file overrides.
"""

from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ASRConfig(BaseSettings):
    """ASR (Automatic Speech Recognition) configuration."""
    
    model_name: str = Field(default="whisper-1", description="Whisper model to use")
    language: Optional[str] = Field(default=None, description="Language code (auto-detect if None)")
    temperature: float = Field(default=0.0, description="Temperature for transcription")
    word_timestamps: bool = Field(default=True, description="Enable word-level timestamps")


class TranslationConfig(BaseSettings):
    """Translation configuration."""
    
    provider: Literal["local", "huggingface"] = Field(default="local", description="Translation provider (local offline)")
    model_name: str = Field(default="Helsinki-NLP/opus-mt-ja-en", description="Hugging Face model for translation")
    temperature: float = Field(default=0.3, description="Temperature for translation (not used for local models)")
    max_tokens: int = Field(default=2000, description="Maximum tokens per translation request (not used for local models)")


class TTSConfig(BaseSettings):
    """Text-to-Speech configuration."""
    
    provider: Literal["coqui", "vibevoice"] = Field(default="coqui", description="TTS provider (local offline)")
    
    # Coqui TTS specific
    coqui_model_name: str = Field(default="tts_models/en/ljspeech/tacotron2-DDC", description="Coqui TTS model name")
    coqui_voice_id: Optional[str] = Field(default=None, description="Coqui TTS voice ID")
    coqui_device: str = Field(default="auto", description="Device for Coqui TTS inference (cuda/cpu)")
    
    # VibeVoice specific
    vibevoice_model_path: Optional[str] = Field(default=None, description="Path to VibeVoice model")
    vibevoice_device: str = Field(default="auto", description="Device for VibeVoice inference")


class AudioConfig(BaseSettings):
    """Audio processing configuration."""
    
    sample_rate: int = Field(default=44100, description="Audio sample rate")
    channels: int = Field(default=2, description="Audio channels")
    bit_depth: int = Field(default=16, description="Audio bit depth")
    
    # Non-verbal preservation
    preserve_sfx: bool = Field(default=True, description="Preserve sound effects")
    preserve_laughs: bool = Field(default=True, description="Preserve laughs and shouts")
    preserve_bgm: bool = Field(default=True, description="Preserve background music")


class APIConfig(BaseSettings):
    """API configuration."""
    
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")


class Settings(BaseSettings):
    """Main application settings."""
    
    # Module configurations
    asr: ASRConfig = Field(default_factory=ASRConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    
    # General settings
    log_level: str = Field(default="INFO", description="Logging level")
    temp_dir: str = Field(default="./temp", description="Temporary files directory")
    output_dir: str = Field(default="./output", description="Output files directory")
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False


# Global settings instance
settings = Settings()

