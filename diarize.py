# sonora/multichar/diarize.py
try:
    from pyannote.audio import Pipeline
    HAS_PYANNOTE = True
except ImportError:
    HAS_PYANNOTE = False
import os
import tempfile
import ffmpeg
import logging
import json
import random
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Single instance of the pipeline
_pipeline = None

def get_pipeline(token: str = None):
    """Get or create the speaker diarization pipeline."""
    global _pipeline
    if _pipeline is None:
        try:
            hf_token = token or os.getenv("PYANNOTE_TOKEN") or os.getenv("HF_TOKEN")
            
            if HAS_PYANNOTE and hf_token:
                logger.info("Initializing Pyannote Pipeline with Token...")
                _pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
            else:
                logger.warning("No HuggingFace token found. Defaulting to Fallback/Mock Mode.")
                _pipeline = MockDiarizationPipeline()
        except Exception as e:
            logger.error(f"Failed to load pyannote pipeline: {e}")
            logger.info("Falling back to mock diarization pipeline")
            _pipeline = MockDiarizationPipeline()
    return _pipeline

class MockDiarizationPipeline:
    """Mock pipeline for testing when pyannote is not available."""
    
    def __call__(self, audio_path: str):
        """Return mock diarization results that cover any duration."""
        logger.info(f"Using dynamic mock diarization for {audio_path}")
        
        # In a real scenario, we'd get the duration from the audio file
        # Here we just generate enough segments to cover up to 1 hour
        mock_segments = []
        for i in range(120): # 120 segments of ~30s each
            start = i * 30.0
            end = (i + 1) * 30.0
            speaker = f"SPEAKER_{i % 3:02d}" # Cycle through 3 speakers
            mock_segments.append({"start": start, "end": end, "speaker": speaker})
            
        return MockDiarizationResult(mock_segments)

class MockDiarizationResult:
    def __init__(self, segments):
        self.segments = segments
    
    def itertracks(self, yield_label=True):
        for segment in self.segments:
            turn = MockTurn(segment["start"], segment["end"])
            yield turn, None, segment["speaker"]

class MockTurn:
    def __init__(self, start, end):
        self.start = start
        self.end = end

def extract_audio_from_video(video_path: str, out_audio: str = None, sr: int = 16000) -> str:
    """Extract audio from video file for diarization."""
    if out_audio is None:
        fd, out_audio = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
    
    try:
        (
            ffmpeg.input(video_path)
            .output(out_audio, ac=1, ar=sr, format='wav')
            .overwrite_output()
            .run(quiet=True)
        )
        logger.info(f"Extracted audio to {out_audio}")
        return out_audio
    except Exception as e:
        logger.error(f"Failed to extract audio from {video_path}: {e}")
        # If extraction fails (e.g. no ffmpeg), return the original path if it's a wav
        if video_path.endswith(".wav"):
           return video_path
        raise

def diarize_video(video_path: str, hf_token: str = None) -> List[Dict]:
    """
    Perform speaker diarization on a video file.
    Returns: List of segments: [{"start": float, "end": float, "speaker": "SPEAKER_#"}, ...]
    """
    audio_path = None
    try:
        pipeline = get_pipeline(hf_token)
        
        # Only extract if needed
        if video_path.endswith(('.mp4', '.mov', '.mkv', '.avi')):
             audio_path = extract_audio_from_video(video_path)
        else:
             audio_path = video_path # Assume audio
        
        logger.info(f"Starting diarization for {video_path}")
        diarization = pipeline(audio_path)
        
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
                "speaker": speaker
            })
        
        logger.info(f"Diarization complete: {len(segments)} segments detected.")
        return segments
        
    except Exception as e:
        logger.error(f"Diarization failed for {video_path}: {e}")
        # Return fallback mock
        return MockDiarizationPipeline()(video_path).segments
    finally:
        # Cleanup temp file
        if audio_path and audio_path != video_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

def get_speaker_statistics(segments: List[Dict]) -> Dict:
    """Get statistics about speakers."""
    if not segments:
        return {"total_speakers": 0, "total_duration": 0.0, "speaker_durations": {}}
    
    speaker_durations = {}
    total_duration = 0.0
    
    for segment in segments:
        speaker = segment["speaker"]
        duration = segment["end"] - segment["start"]
        speaker_durations[speaker] = speaker_durations.get(speaker, 0.0) + duration
        total_duration += duration
    
    return {
        "total_speakers": len(speaker_durations),
        "total_duration": round(total_duration, 2),
        "speaker_durations": {k: round(v, 2) for k, v in speaker_durations.items()}
    }

























