#!/usr/bin/env python3
"""
Test script to verify API configuration and connectivity.
"""

import os
import asyncio
import logging
from sonora.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_environment_variables():
    """Test that environment variables are set correctly."""
    logger.info("Testing environment variables...")
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your_openai_key_here":
        logger.info("✅ OpenAI API key is set")
    else:
        logger.warning("⚠️  OpenAI API key not set or using placeholder")
    
    # Check ElevenLabs API key
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    if elevenlabs_key and elevenlabs_key != "your_elevenlabs_key_here":
        logger.info("✅ ElevenLabs API key is set")
    else:
        logger.warning("⚠️  ElevenLabs API key not set or using placeholder")
    
    # Check Anthropic API key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
        logger.info("✅ Anthropic API key is set")
    else:
        logger.info("ℹ️  Anthropic API key not set (optional)")


def test_configuration():
    """Test that configuration is loaded correctly."""
    logger.info("Testing configuration...")
    
    try:
        # Test ASR config
        logger.info(f"ASR Model: {settings.asr.model_name}")
        logger.info(f"ASR Temperature: {settings.asr.temperature}")
        
        # Test Translation config
        logger.info(f"Translation Provider: {settings.translation.provider}")
        logger.info(f"Translation Model: {settings.translation.model_name}")
        
        # Test TTS config
        logger.info(f"TTS Provider: {settings.tts.provider}")
        logger.info(f"ElevenLabs Voice ID: {settings.tts.elevenlabs_voice_id}")
        
        # Test Audio config
        logger.info(f"Sample Rate: {settings.audio.sample_rate}")
        logger.info(f"Channels: {settings.audio.channels}")
        
        logger.info("✅ Configuration loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")


import pytest


@pytest.mark.external
async def test_translation_connection():
    """Test translation service connectivity."""
    logger.info("Testing translation service...")
    
    try:
        from sonora.translate import LLMTranslator
        
        translator = LLMTranslator()
        logger.info(f"Translation provider: {translator.provider}")
        
        # Test with a simple phrase
        test_text = "こんにちは、世界！"
        logger.info(f"Testing translation of: {test_text}")
        
        result = await translator.translate(test_text, "ja", "en")
        logger.info(f"Translation result: {result.translated_text}")
        logger.info("✅ Translation service working")
        
    except Exception as e:
        logger.error(f"❌ Translation test failed: {e}")


@pytest.mark.external
async def test_tts_connection():
    """Test TTS service connectivity."""
    logger.info("Testing TTS service...")
    
    try:
        from sonora.tts import ElevenLabsTTS
        
        tts = ElevenLabsTTS()
        logger.info(f"TTS provider: {tts.provider}")
        
        # Test voice availability
        voices = await tts.get_available_voices()
        logger.info(f"Available voices: {len(voices)}")
        logger.info("✅ TTS service working")
        
    except Exception as e:
        logger.error(f"❌ TTS test failed: {e}")


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Sonora/Auralis configuration tests...")
    
    # Test environment variables
    test_environment_variables()
    print()
    
    # Test configuration
    test_configuration()
    print()
    
    # Test service connections
    await test_translation_connection()
    print()
    
    await test_tts_connection()
    print()
    
    logger.info("🎉 Configuration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

