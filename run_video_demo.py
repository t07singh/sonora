#!/usr/bin/env python3
"""
Demo script for Sonora video dubbing functionality.

This script demonstrates the complete video dubbing pipeline with lip-synchronization.
"""

import os
import sys
import logging
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import sonora modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sonora.video_sync.extractor import AudioExtractor
from sonora.video_sync.lipsync import LipSyncEngine
from sonora.video_sync.composer import VideoComposer
from sonora.video_sync.utils import VideoSyncUtils
from sonora.asr.transcriber import Transcriber
from sonora.translate.translator import Translator
from sonora.tts.tts_provider import TTSProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_demo_video(output_path: str, duration: float = 5.0):
    """
    Create a simple demo video for testing.
    
    Args:
        output_path: Path to save the demo video
        duration: Duration of the video in seconds
    """
    try:
        import cv2
        import numpy as np
        
        logger.info(f"Creating demo video: {output_path}")
        
        # Video properties
        width, height = 640, 480
        fps = 30
        total_frames = int(duration * fps)
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Create frames
        for i in range(total_frames):
            # Create a simple animated frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add a moving circle
            center_x = int(width * 0.5 + 100 * np.sin(2 * np.pi * i / total_frames))
            center_y = int(height * 0.5 + 50 * np.cos(2 * np.pi * i / total_frames))
            cv2.circle(frame, (center_x, center_y), 30, (0, 255, 0), -1)
            
            # Add text
            text = f"Demo Video - Frame {i+1}/{total_frames}"
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        logger.info(f"Demo video created successfully: {output_path}")
        
    except ImportError:
        logger.error("OpenCV not available. Cannot create demo video.")
        raise
    except Exception as e:
        logger.error(f"Failed to create demo video: {e}")
        raise


def create_demo_audio(output_path: str, duration: float = 5.0):
    """
    Create a simple demo audio for testing.
    
    Args:
        output_path: Path to save the demo audio
        duration: Duration of the audio in seconds
    """
    try:
        import numpy as np
        import soundfile as sf
        
        logger.info(f"Creating demo audio: {output_path}")
        
        # Audio properties
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a simple tone with some variation
        frequency = 440  # A4 note
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Add some envelope to make it more speech-like
        envelope = np.exp(-t / duration) * (1 + 0.5 * np.sin(2 * np.pi * 2 * t))
        audio_data *= envelope
        
        # Save audio
        sf.write(output_path, audio_data, sample_rate)
        logger.info(f"Demo audio created successfully: {output_path}")
        
    except ImportError:
        logger.error("SoundFile not available. Cannot create demo audio.")
        raise
    except Exception as e:
        logger.error(f"Failed to create demo audio: {e}")
        raise


def run_video_dubbing_demo():
    """Run the complete video dubbing demo."""
    try:
        logger.info("🎬 Starting Sonora Video Dubbing Demo")
        logger.info("=" * 60)
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="sonora_video_demo_")
        logger.info(f"Using temporary directory: {temp_dir}")
        
        # Create demo video
        demo_video_path = os.path.join(temp_dir, "demo_video.mp4")
        create_demo_video(demo_video_path, duration=3.0)
        
        # Initialize components
        logger.info("🔧 Initializing components...")
        extractor = AudioExtractor()
        lip_sync = LipSyncEngine(model_type="mock")
        composer = VideoComposer()
        utils = VideoSyncUtils()
        transcriber = Transcriber()
        translator = Translator()
        tts = TTSProvider()
        
        # Stage 1: Extract audio from video
        logger.info("\n🎵 STAGE 1: AUDIO EXTRACTION")
        logger.info("-" * 50)
        
        extracted_audio_path = extractor.extract_audio(demo_video_path)
        logger.info(f"✅ Audio extracted: {extracted_audio_path}")
        
        # Stage 2: Run dubbing pipeline
        logger.info("\n🎤 STAGE 2: DUBBING PIPELINE")
        logger.info("-" * 50)
        
        # ASR
        logger.info("Transcribing audio...")
        transcription_result = transcriber.transcribe(extracted_audio_path)
        logger.info(f"Transcription: {transcription_result['text']}")
        
        # Translation (mock for demo)
        logger.info("Translating text...")
        translated_text = "Hello, this is a demo of Sonora video dubbing system."
        logger.info(f"Translation: {translated_text}")
        
        # TTS
        logger.info("Generating dubbed audio...")
        dubbed_audio_path = os.path.join(temp_dir, "dubbed_audio.wav")
        tts_result = tts.synthesize(translated_text, dubbed_audio_path)
        
        if tts_result['success']:
            logger.info(f"✅ Dubbed audio generated: {dubbed_audio_path}")
        else:
            logger.error("❌ TTS failed")
            return False
        
        # Stage 3: Lip-synchronization
        logger.info("\n🎭 STAGE 3: LIP-SYNCHRONIZATION")
        logger.info("-" * 50)
        
        lip_synced_path = os.path.join(temp_dir, "lip_synced_video.mp4")
        result_path = lip_sync.sync_lips(demo_video_path, dubbed_audio_path, lip_synced_path)
        logger.info(f"✅ Lip-sync completed: {result_path}")
        
        # Stage 4: Final composition
        logger.info("\n🎬 STAGE 4: FINAL COMPOSITION")
        logger.info("-" * 50)
        
        final_output_path = os.path.join(temp_dir, "final_dubbed_video.mp4")
        composed_path = composer.compose_final_video(
            demo_video_path, dubbed_audio_path, result_path, final_output_path
        )
        logger.info(f"✅ Final video composed: {composed_path}")
        
        # Stage 5: Quality assessment
        logger.info("\n📊 STAGE 5: QUALITY ASSESSMENT")
        logger.info("-" * 50)
        
        quality_metrics = utils.calculate_lip_sync_quality(demo_video_path, composed_path)
        logger.info(f"Quality metrics: {quality_metrics}")
        
        # Display results
        logger.info("\n🎉 VIDEO DUBBING DEMO COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"📁 Original video: {demo_video_path}")
        logger.info(f"📁 Final dubbed video: {composed_path}")
        logger.info(f"📊 Overall quality score: {quality_metrics.get('overall_score', 'N/A')}")
        
        # Cleanup
        logger.info("\n🧹 Cleaning up temporary files...")
        extractor.cleanup_temp_files()
        lip_sync.cleanup_temp_files()
        composer.cleanup_temp_files()
        utils.cleanup_temp_files()
        
        import shutil
        shutil.rmtree(temp_dir)
        logger.info("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        logger.exception("Full error details:")
        return False


def main():
    """Main entry point."""
    print("🎬 Sonora Video Dubbing Demo")
    print("=" * 40)
    print("This demo will:")
    print("1. Create a sample video")
    print("2. Extract audio from the video")
    print("3. Run the dubbing pipeline (ASR → Translation → TTS)")
    print("4. Apply lip-synchronization")
    print("5. Compose the final dubbed video")
    print("6. Assess quality metrics")
    print()
    
    # Check if required dependencies are available
    try:
        import cv2
        import soundfile
        import ffmpeg
        logger.info("✅ All required dependencies are available")
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Please install required packages: pip install opencv-python soundfile ffmpeg-python")
        return 1
    
    # Run the demo
    success = run_video_dubbing_demo()
    
    if success:
        print("\n🎉 Demo completed successfully!")
        print("Check the logs above for detailed information.")
        return 0
    else:
        print("\n❌ Demo failed. Check the logs above for error details.")
        return 1


if __name__ == "__main__":
    exit(main())








































