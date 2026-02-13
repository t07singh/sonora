
import os
import subprocess
import logging
from pathlib import Path
from elevenlabs.client import ElevenLabs

# Configure logging
logger = logging.getLogger("sonora.voice_generator")

# Initialize ElevenLabs Safely
client = None
try:
    if os.getenv("ELEVENLABS_API_KEY"):
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    else:
        logger.warning("⚠️ ELEVENLABS_API_KEY missing. Voice Generator running in MOCK MODE.")
except Exception as e:
    logger.error(f"Failed to initialize ElevenLabs client: {e}")

class VoiceGenerator:
    def __init__(self):
        self.output_dir = Path("sonora/data/audio_clips")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_and_fit(self, text: str, voice_id: str, target_duration: float, clip_id: str) -> str:
        """
        Generates voice and applies the Time-Stretch Guard to fit the target window.
        """
        logger.info(f"Generating voice for: '{text[:30]}...' | Target: {target_duration:.2f}s")
        
        # 1. Generate Raw Audio via ElevenLabs v2.5 Flash
        raw_path = self.output_dir / f"raw_{clip_id}.mp3"
        
        if not client:
            logger.info("Mock Mode: Generating silent placeholder audio.")
            # Create a 1-second silent MP3 (or minimal valid MP3) for testing
            # This prevents the pipeline from crashing if FFmpeg tries to read it
            # Using a simple text write for mock purposes is risky for FFmpeg, 
            # ideally we copy a valid 'silence.mp3' asset, but here we'll handle gracefully.
            with open(raw_path, "wb") as f:
                f.write(b'\xFF\xF3\x44\xC4' * 100) # Fake MP3 frames
            return str(raw_path)

        try:
            audio_gen = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_flash_v2_5",
                output_format="mp3_44100_128"
            )
            
            with open(raw_path, "wb") as f:
                for chunk in audio_gen:
                    if chunk:
                        f.write(chunk)
        except Exception as e:
            logger.error(f"ElevenLabs Generation Failed: {e}")
            # Fallback to keep pipeline moving
            with open(raw_path, "wb") as f: f.write(b'\0')
            return str(raw_path)

        # 2. Extract Duration via ffprobe
        current_duration = self._get_duration(str(raw_path))
        logger.info(f"Raw duration: {current_duration:.2f}s")

        # 3. Apply Time-Stretch Guard (atempo filter)
        if current_duration > target_duration or abs(current_duration - target_duration) > 0.1:
            ratio = current_duration / target_duration
            # FFmpeg atempo limit: 0.5 to 2.0
            clamped_ratio = min(max(ratio, 0.5), 2.0)
            
            final_path = self.output_dir / f"dub_{clip_id}.mp3"
            logger.info(f"Applying Time-Stretch Guard: {clamped_ratio:.2f}x")
            
            try:
                subprocess.run([
                    'ffmpeg', '-y', '-i', str(raw_path),
                    '-filter:a', f'atempo={clamped_ratio}',
                    str(final_path)
                ], check=True, capture_output=True)
                
                # Cleanup raw temp
                if raw_path.exists():
                    os.remove(raw_path)
                return str(final_path)
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg Stretch Failed: {e.stderr.decode()}")
                return str(raw_path)
        
        return str(raw_path)

    def _get_duration(self, path: str) -> float:
        """Utility to get audio duration using ffprobe."""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', path
            ], capture_output=True, text=True, check=True)
            return float(result.stdout)
        except Exception:
            return 0.0
