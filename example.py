#!/usr/bin/env python3
"""
Example usage of Sonora/Auralis AI Dubbing System.

This script demonstrates the complete real pipeline workflow using actual APIs:
- ASR (Whisper) → Translation (GPT-4o) → TTS (ElevenLabs)
"""

import os
import logging
from pathlib import Path

from asr.transcriber import Transcriber
from translate.translator import Translator
from tts.tts_provider import TTSProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def dub_audio_file(input_audio_path: str, output_audio_path: str):
    """
    Complete dubbing pipeline for an audio file using real APIs.
    
    Args:
        input_audio_path: Path to input audio file
        output_audio_path: Path to save dubbed audio
    """
    try:
        logger.info("=" * 60)
        logger.info("🎬 SONORA/AURALIS AI DUBBING PIPELINE")
        logger.info("=" * 60)
        logger.info(f"📁 Input: {input_audio_path}")
        logger.info(f"📁 Output: {output_audio_path}")
        logger.info("")
        
        # Check API keys and warn about missing ones
        check_api_keys()
        
        # Initialize components
        logger.info("🔧 Initializing components...")
        transcriber = Transcriber()
        translator = Translator()
        tts = TTSProvider()
        logger.info("✅ Components initialized")
        logger.info("")
        
        # Stage 1: ASR (Automatic Speech Recognition)
        logger.info("🎤 STAGE 1: AUTOMATIC SPEECH RECOGNITION (ASR)")
        logger.info("-" * 50)
        logger.info("Transcribing audio with Whisper...")
        
        transcription_result = transcriber.transcribe(input_audio_path)
        segments = transcriber.transcribe_segments(input_audio_path)
        
        logger.info(f"📝 Full transcription: {transcription_result['text']}")
        logger.info(f"🔍 Detected language: {transcription_result.get('language', 'Unknown')}")
        logger.info(f"📊 Found {len(segments)} segments")
        
        # Log each segment
        for i, segment in enumerate(segments):
            logger.info(f"   Segment {i+1}: [{segment['start']:.2f}s-{segment['end']:.2f}s] "
                       f"[{segment['lang']}] {segment['text']}")
        logger.info("✅ ASR completed")
        logger.info("")
        
        # Stage 2: Translation
        logger.info("🌐 STAGE 2: TRANSLATION")
        logger.info("-" * 50)
        
        translated_segments = []
        japanese_segments = [seg for seg in segments if seg['lang'] == 'JP']
        
        if japanese_segments:
            logger.info(f"🔄 Translating {len(japanese_segments)} Japanese segments with GPT-4o...")
            
            for i, segment in enumerate(japanese_segments):
                logger.info(f"   Translating segment {i+1}: {segment['text']}")
                translated_text = translator.translate(segment['text'], segment['lang'])
                logger.info(f"   → {translated_text}")
                
                # Create translated segment
                translated_segment = segment.copy()
                translated_segment['text'] = translated_text
                translated_segment['lang'] = 'EN'
                translated_segments.append(translated_segment)
        else:
            logger.info("ℹ️  No Japanese segments found, skipping translation")
            translated_segments = segments
        
        # Keep non-Japanese segments as-is
        for segment in segments:
            if segment['lang'] != 'JP':
                translated_segments.append(segment)
        
        logger.info("✅ Translation completed")
        logger.info("")
        
        # Stage 3: Text-to-Speech
        logger.info("🔊 STAGE 3: TEXT-TO-SPEECH (TTS)")
        logger.info("-" * 50)
        
        # Combine all text for TTS
        text_to_synthesize = " ".join([seg['text'] for seg in translated_segments if seg['lang'] in ['EN', 'JP']])
        
        if text_to_synthesize.strip():
            logger.info(f"🎵 Synthesizing speech with ElevenLabs...")
            logger.info(f"📝 Text to synthesize: {text_to_synthesize}")
            
            tts_result = tts.synthesize(text_to_synthesize, output_audio_path)
            
            if tts_result['success']:
                logger.info(f"✅ TTS completed successfully")
                logger.info(f"📁 Audio saved to: {tts_result['audio_path']}")
                logger.info(f"⏱️  Duration: {tts_result['duration']:.2f} seconds")
            else:
                logger.error(f"❌ TTS failed")
                return False
        else:
            logger.warning("⚠️  No text to synthesize")
            return False
        
        logger.info("")
        logger.info("🎉 DUBBING PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"❌ Dubbing pipeline failed: {e}")
        logger.exception("Full error details:")
        return False


def check_api_keys():
    """Check for required API keys and warn about missing ones."""
    logger.info("🔑 Checking API keys...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not openai_key:
        logger.warning("⚠️  OPENAI_API_KEY not found - Whisper ASR and GPT-4o translation will use mock mode")
    else:
        logger.info("✅ OPENAI_API_KEY found - Real Whisper ASR and GPT-4o translation enabled")
    
    if not elevenlabs_key:
        logger.warning("⚠️  ELEVENLABS_API_KEY not found - TTS will use mock mode")
    else:
        logger.info("✅ ELEVENLABS_API_KEY found - Real ElevenLabs TTS enabled")
    
    logger.info("")


def main():
    """Main function to run the example."""
    # Sample audio file path
    input_file = "assets/sample_jp.wav"
    output_file = "/tmp/dubbed_output.wav"
    
    # Check if input file exists
    if not Path(input_file).exists():
        logger.warning(f"Input file not found: {input_file}")
        logger.info("Creating a sample audio file for demonstration...")
        
        # Create assets directory if it doesn't exist
        assets_dir = Path("assets")
        assets_dir.mkdir(exist_ok=True)
        
        # Create a simple sample file (this would normally be a real audio file)
        sample_file = assets_dir / "sample_jp.wav"
        logger.info(f"Please place a Japanese audio file at: {sample_file}")
        logger.info("For now, the pipeline will run with mock data")
        
        # Use a placeholder file for demonstration
        input_file = "sample_placeholder.wav"
    
    # Run the dubbing pipeline
    success = dub_audio_file(input_file, output_file)
    
    if success:
        logger.info(f"🎉 Pipeline completed! Check output at: {output_file}")
    else:
        logger.error("❌ Pipeline failed. Check logs above for details.")


if __name__ == "__main__":
    # Run the example
    main()

