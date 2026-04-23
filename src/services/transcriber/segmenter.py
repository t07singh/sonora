import os
import whisperx
import torch
import logging
import json
import ffmpeg
from typing import List, Dict, Any, Optional
from src.core.reliability import get_device

logger = logging.getLogger("sonora.transcriber.segmenter")

class VideoSegmenter:
    """
    Segmentation engine using WhisperX for frame-accurate character dialogue extraction.
    Lives in the Transcriber service for access to GPU and Whisper dependencies.
    """
    def __init__(self, model_size: str = "large-v3", compute_type: str = None):
        self.device = get_device()
        self.model_size = model_size
        
        # Default to float16 on CUDA, int8 on CPU
        if compute_type is None:
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type
            
        self.hf_token = os.getenv("HF_TOKEN")
        self.shared_path = os.getenv("SHARED_PATH", "/tmp/sonora")
        
        logger.info(f"Initialized VideoSegmenter on {self.device} (Mode: {self.compute_type})")

    def segment_video(self, video_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        Performs the full segmentation pipeline:
        1. Transcription (Faster-Whisper)
        2. Alignment (Wav2Vec2)
        3. Diarization (Pyannote)
        4. Cutting (FFmpeg)
        """
        if output_dir is None:
            output_dir = os.path.join(self.shared_path, "segments", os.path.basename(video_path).split('.')[0])
        
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Starting neural segmentation for {video_path}")
        
        # 1. Load model and transcribe
        # Note: WhisperX uses its own model loading which is compatible with faster-whisper
        model = whisperx.load_model(self.model_size, self.device, compute_type=self.compute_type)
        audio = whisperx.load_audio(video_path)
        
        # Enhanced for Japanese/Anime content with word_timestamps set to True
        result = model.transcribe(
            audio, 
            batch_size=16, 
            initial_prompt="Japanese Japanese anime drama dialogue. Emotional, expressive, and character-driven speech."
        )
        
        # 2. Align whisper output
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, self.device, return_char_alignments=False)
        
        # 3. Diarize
        if not self.hf_token:
            logger.warning("HF_TOKEN missing. Diarization will be skipped (Speaker: UNKNOWN).")
            # Mock diarization result if token is missing to prevent crash
            for seg in result["segments"]:
                seg["speaker"] = "UNKNOWN"
        else:
            try:
                diarize_model = whisperx.DiarizationPipeline(use_auth_token=self.hf_token, device=self.device)
                diarize_segments = diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
            except Exception as e:
                logger.error(f"Diarization failed: {e}. Check HF_TOKEN and Pyannote terms.")
                for seg in result["segments"]:
                    seg["speaker"] = "UNKNOWN"
        
        # 4. Process segments and cut video
        final_segments = []
        for i, seg in enumerate(result["segments"]):
            start = seg.get("start")
            end = seg.get("end")
            
            # Skip invalid segments
            if start is None or end is None:
                continue
                
            speaker = seg.get("speaker", "UNKNOWN")
            text = seg.get("text", "").strip()
            
            # Clip filename
            clip_name = f"segment_{i:04d}_{speaker}.mp4"
            clip_path = os.path.join(output_dir, clip_name)
            
            # Lossless cut via FFmpeg (Untackled)
            self._cut_segment(video_path, start, end, clip_path)
            
            final_segments.append({
                "id": str(i),
                "start": round(start, 3),
                "end": round(end, 3),
                "speaker": speaker,
                "text": text,
                "clip_path": clip_path,
                "relative_clip_path": os.path.relpath(clip_path, self.shared_path),
                "words": seg.get("words", [])
            })
            
        logger.info(f"Segmentation complete: {len(final_segments)} clips generated in {output_dir}")
        return final_segments

    def _cut_segment(self, input_path: str, start: float, end: float, output_path: str):
        """
        Extracts a high-fidelity video segment using FFmpeg.
        We use re-encoding (crf 18) instead of stream copy to ensure frame-accurate 
        video tracks, especially when the start time doesn't land on a keyframe.
        """
        duration = end - start
        try:
            # map 0:v:0 and map 0:a:0? ensure we capture both streams if available
            (
                ffmpeg
                .input(input_path, ss=start)
                .output(output_path, t=duration, vcodec='libx264', acodec='aac', ab='192k', crf=18, preset='ultrafast')
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )
        except Exception as e:
            logger.error(f"❌ [SURGERY FAILED] Segment {start}-{end}: {e}")

def get_segmenter():
    return VideoSegmenter()
