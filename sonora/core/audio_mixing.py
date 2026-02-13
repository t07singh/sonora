import os
import logging
import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)

def align_audio_to_duration(audio_path: str, target_duration: float, output_path: str) -> str:
    """
    Time-stretches audio to match a target duration precisely.
    
    Args:
        audio_path: Path to the source WAV/MP3 file.
        target_duration: The duration (in seconds) the audio should fit into.
        output_path: Where to save the processed file.
        
    Returns:
        The path to the resulting aligned audio file.
    """
    try:
        if not os.path.exists(audio_path):
            logger.error(f"Alignment error: File not found {audio_path}")
            return audio_path

        # Load audio (sr=None preserves native sampling rate)
        y, sr = librosa.load(audio_path, sr=None)
        current_duration = librosa.get_duration(y=y, sr=sr)
        
        if current_duration <= 0 or target_duration <= 0:
            return audio_path

        # Calculate stretch rate: input_len / target_len
        # rate > 1.0: speeds up (original is too long)
        # rate < 1.0: slows down (original is too short)
        stretch_rate = current_duration / target_duration
        
        # Apply "Studio Demo" Safety Thresholds
        # Max speedup 1.3x, Max slowdown 0.8x
        clamped_rate = max(0.8, min(1.3, stretch_rate))
        
        if stretch_rate != clamped_rate:
            logger.warning(f"Stretch rate {stretch_rate:.2f} exceeds bounds. Clamping to {clamped_rate:.2f} to preserve quality.")

        # Perform high-quality time stretching
        y_stretched = librosa.effects.time_stretch(y, rate=clamped_rate)
        
        # Hard alignment: Force exact sample count match to avoid drift
        target_samples = int(target_duration * sr)
        if len(y_stretched) > target_samples:
            y_stretched = y_stretched[:target_samples]
        elif len(y_stretched) < target_samples:
            y_stretched = np.pad(y_stretched, (0, target_samples - len(y_stretched)))

        # Save to disk
        sf.write(output_path, y_stretched, sr)
        logger.info(f"Audio aligned: {current_duration:.2f}s -> {target_duration:.2f}s (Rate: {clamped_rate:.2f})")
        return output_path
        
    except Exception as e:
        logger.error(f"Critical failure during audio alignment: {e}")
        # Fallback to original path on failure
        return audio_path
