#!/usr/bin/env python3
"""
Sonora/Auralis Dubbing Pipeline Orchestrator.
Refactored for 'Sync-Master' accuracy.
"""

import argparse
import logging
import os
import time
from pathlib import Path

from sonora.asr.transcriber import Transcriber
from sonora.translate.translator import Translator
from sonora.tts.tts_provider import TTSProvider
from sonora.utils.muxer import AudioMuxer
from sonora.core.audio_mixing import align_audio_to_duration

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("sonora-pipeline")

def main():
    parser = argparse.ArgumentParser(description="Run the Sonora dubbing pipeline with Sync-Master alignment.")
    parser.add_argument("input", help="Path to input audio/video file")
    parser.add_argument("-o", "--output", help="Final output path", default="sonora_demo_final.wav")
    args = parser.parse_args()

    print("\n" + "="*50)
    print(" 🎬 SONORA STUDIO: 'SYNC-MASTER' PIPELINE")
    print("="*50 + "\n")

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    try:
        # Initialize Swarm Components
        transcriber = Transcriber()
        translator = Translator()
        tts = TTSProvider()
        muxer = AudioMuxer()

        # STAGE 1: INGESTION & ASR
        print("🎤 [1/4] Analyzing original performance...")
        transcription_result = transcriber.transcribe(str(input_path))
        
        # Calculate source duration for sync
        duration_orig = 0
        if transcription_result.get('timestamps') and len(transcription_result['timestamps']) > 0:
            duration_orig = transcription_result['timestamps'][-1]['end'] - transcription_result['timestamps'][0]['start']
        else:
            # Fallback to total audio duration if timestamps missing
            import librosa
            duration_orig = librosa.get_duration(path=str(input_path))

        print(f"✅ Analysis complete. Detected length: {duration_orig:.2f}s")

        # STAGE 2: ADAPTATION
        print("\n🌐 [2/4] Adapting dialogue to English...")
        translation = translator.translate(transcription_result['text'])
        print(f"✅ Text adapted: \"{translation}\"")

        # STAGE 3: SYNTHESIS & SYNC-MASTER ALIGNMENT
        print("\n🔊 [3/4] Generating high-fidelity AI voice...")
        temp_tts_output = "temp_raw_tts.wav"
        tts.synthesize(translation, temp_tts_output)
        
        # Apply Time-Stretching to lock sync
        print(f"⏳ [SYNC-MASTER] Aligning voice to target window ({duration_orig:.2f}s)...")
        aligned_voice_path = "aligned_voice_final.wav"
        final_voice_path = align_audio_to_duration(
            temp_tts_output, 
            duration_orig, 
            aligned_voice_path
        )
        print("✅ Temporal alignment successful.")

        # STAGE 4: MASTER MIXING
        print("\n🎵 [4/4] Finalizing Studio Master...")
        muxer.mix_audio([final_voice_path], args.output)
        
        # Cleanup intermediary takes
        if os.path.exists(temp_tts_output): os.remove(temp_tts_output)
        
        print("\n" + "="*50)
        print(f" 🎉 SUCCESS! Final Master available at: {args.output}")
        print("="*50 + "\n")
        return 0

    except Exception as e:
        logger.error(f"Studio Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
