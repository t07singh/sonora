"""
Sonora Segmenter Service — FastAPI microservice for video segmentation.

Runs on port 8004 as part of the Sonora Docker swarm.
Provides endpoints for segmenting video into per-sentence, per-speaker clips.

Pipeline: Demucs → Silero VAD → Whisper ASR → pyannote Diarization → Merge → ffmpeg Cut
"""

import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.services.segmenter.engine import (
    VideoSegmenter, SegmentationResult, Segment, Word
)
from src.core.reliability import HardwareLock

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sonora.segmenter")

PORT = int(os.getenv("SEGMENTER_PORT", "8004"))
HF_TOKEN = os.getenv("HF_TOKEN")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3")
DEFAULT_MODE = os.getenv("SEGMENTER_MODE", "fast")  # "fast" or "precise"
SHARED_PATH = os.getenv("SHARED_PATH", "/tmp/sonora")
SONORA_DATA_DIR = os.getenv("SONORA_DATA_DIR", str(Path.home() / "sonora" / "data"))

# ─────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sonora Segmenter Service",
    description="Anime-first video segmentation: extract per-sentence, per-speaker clips",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────

class SegmentRequest(BaseModel):
    """Request model for video segmentation."""
    video_path: str = Field(..., description="Path to video file in shared volume, or filename")
    language: str = Field("ja", description="Language code (ja, en, etc.)")
    mode: str = Field(DEFAULT_MODE, description="Segmentation mode: 'fast' or 'precise'")
    min_segment_duration: float = Field(0.5, description="Minimum segment duration in seconds")
    max_segment_duration: float = Field(15.0, description="Maximum segment duration in seconds")
    cut_clips: bool = Field(True, description="Whether to cut video into individual clips")
    isolate_vocals: bool = Field(True, description="Whether to isolate vocals with Demucs first")
    num_speakers: Optional[int] = Field(None, description="Hint: number of speakers (None=auto)")
    whisper_model: Optional[str] = Field(None, description="Override Whisper model name")

class QuickSegmentRequest(BaseModel):
    """Quick segment request — metadata only, no clip cutting."""
    video_path: str
    language: str = "ja"
    num_speakers: Optional[int] = None

class WordResponse(BaseModel):
    text: str
    start: float
    end: float
    speaker: str
    confidence: float

class SegmentResponse(BaseModel):
    id: str
    index: int
    start: float
    end: float
    duration: float
    speaker: str
    text: str
    words: List[WordResponse] = []
    clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

class SegmentationResponse(BaseModel):
    segments: List[SegmentResponse]
    duration: float
    language: str
    num_speakers: int
    device: str
    mode: str
    processing_time: float
    job_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    device: str
    whisper_model: str
    hf_token_present: bool
    pyannote_available: bool
    mode: str

# ─────────────────────────────────────────────────────────────
# Job Storage (in-memory with optional persistence)
# ─────────────────────────────────────────────────────────────

segmentation_jobs: Dict[str, dict] = {}
JOBS_FILE = os.path.join(SHARED_PATH, "segmentation_jobs.json")


def save_jobs():
    """Persist job state to disk."""
    try:
        os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
        with open(JOBS_FILE, "w") as f:
            json.dump(segmentation_jobs, f, default=str, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save jobs: {e}")


def load_jobs():
    """Load job state from disk."""
    global segmentation_jobs
    try:
        if os.path.exists(JOBS_FILE):
            with open(JOBS_FILE, "r") as f:
                segmentation_jobs = json.load(f)
                logger.info(f"Loaded {len(segmentation_jobs)} existing jobs.")
    except Exception as e:
        logger.warning(f"Failed to load jobs: {e}")


load_jobs()

# ─────────────────────────────────────────────────────────────
# WebSocket-like status broadcasting (simple version)
# ─────────────────────────────────────────────────────────────

_status_listeners = []


async def broadcast_status(job_id: str, msg: str, progress: float = 0.0):
    """Broadcast status update for a job."""
    if job_id in segmentation_jobs:
        segmentation_jobs[job_id]["status"] = msg
        segmentation_jobs[job_id]["progress"] = progress
        save_jobs()
    logger.info(f"[Job {job_id}] {msg} ({progress:.0%})")


# ─────────────────────────────────────────────────────────────
# Background Segmentation Task
# ─────────────────────────────────────────────────────────────

async def background_segmentation(job_id: str, req: SegmentRequest):
    """Run segmentation in the background and update job state."""
    try:
        # Update job status
        segmentation_jobs[job_id]["status"] = "Processing"
        segmentation_jobs[job_id]["progress"] = 0.0
        save_jobs()

        async def status_cb(msg: str):
            # Parse progress from status messages
            progress_map = {
                "Extracting": 0.05,
                "Isolating": 0.15,
                "Detecting": 0.25,
                "Transcribing": 0.40,
                "Identifying": 0.60,
                "Merging": 0.70,
                "Running forced": 0.75,
                "Grouping": 0.80,
                "Cutting": 0.90,
                "complete": 1.0,
            }
            progress = 0.0
            for keyword, pct in progress_map.items():
                if keyword.lower() in msg.lower():
                    progress = pct

            await broadcast_status(job_id, msg, progress)

        # Create segmenter
        segmenter = VideoSegmenter(
            mode=req.mode,
            whisper_model=req.whisper_model or WHISPER_MODEL,
            hf_token=HF_TOKEN,
            num_speakers=req.num_speakers,
            output_dir=SONORA_DATA_DIR,
            status_callback=status_cb
        )

        # Acquire hardware lock (GPU)
        async with HardwareLock.locked_async("Segmenter", priority=2):
            result = await segmenter.segment_video(
                video_path=req.video_path,
                language=req.language,
                min_segment_duration=req.min_segment_duration,
                max_segment_duration=req.max_segment_duration,
                cut_clips=req.cut_clips,
                isolate_vocals=req.isolate_vocals
            )

        # Convert to response format
        response_data = _result_to_dict(result)
        response_data["job_id"] = job_id

        # Update job
        segmentation_jobs[job_id]["status"] = "Complete"
        segmentation_jobs[job_id]["progress"] = 1.0
        segmentation_jobs[job_id]["result"] = response_data
        save_jobs()

        await broadcast_status(job_id, "Segmentation complete", 1.0)

    except Exception as e:
        logger.error(f"Segmentation job {job_id} failed: {e}", exc_info=True)
        segmentation_jobs[job_id]["status"] = "Error"
        segmentation_jobs[job_id]["error"] = str(e)
        segmentation_jobs[job_id]["progress"] = 0.0
        save_jobs()
        await broadcast_status(job_id, f"Error: {str(e)}", 0.0)


def _result_to_dict(result: SegmentationResult) -> dict:
    """Convert SegmentationResult to a JSON-serializable dict."""
    segments = []
    for seg in result.segments:
        words = []
        for w in seg.words:
            words.append({
                "text": w.text,
                "start": w.start,
                "end": w.end,
                "speaker": w.speaker,
                "confidence": w.confidence
            })
        segments.append({
            "id": seg.id,
            "index": seg.index,
            "start": seg.start,
            "end": seg.end,
            "duration": seg.duration,
            "speaker": seg.speaker,
            "text": seg.text,
            "words": words,
            "clip_path": seg.clip_path,
            "thumbnail_path": seg.thumbnail_path
        })

    return {
        "segments": segments,
        "duration": result.duration,
        "language": result.language,
        "num_speakers": result.num_speakers,
        "device": result.device,
        "mode": result.mode,
        "processing_time": result.processing_time
    }


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    import torch

    # Check pyannote availability
    pyannote_available = HF_TOKEN is not None
    try:
        from pyannote.audio import Pipeline
        pyannote_available = True
    except ImportError:
        pyannote_available = False

    return HealthResponse(
        status="healthy",
        device="cuda" if torch.cuda.is_available() else "cpu",
        whisper_model=WHISPER_MODEL,
        hf_token_present=HF_TOKEN is not None,
        pyannote_available=pyannote_available,
        mode=DEFAULT_MODE
    )


@app.post("/segment", response_model=SegmentationResponse)
async def segment_video(req: SegmentRequest, background_tasks: BackgroundTasks):
    """
    Full segmentation pipeline: video → segments + clips.
    Runs as a background task for long videos.
    Returns a job_id immediately; poll /job/{job_id} for results.
    """
    import uuid

    job_id = str(uuid.uuid4())[:8]

    # Validate video path
    video_path = req.video_path
    if not os.path.isabs(video_path):
        video_path = os.path.join(SHARED_PATH, "uploads", video_path)

    if not os.path.exists(video_path):
        raise HTTPException(
            status_code=404,
            detail=f"Video file not found: {video_path}. "
                   f"Upload to shared volume first."
        )

    # Create job
    segmentation_jobs[job_id] = {
        "status": "Queued",
        "progress": 0.0,
        "video_path": video_path,
        "mode": req.mode,
        "result": None,
        "error": None,
        "created_at": time.time()
    }
    save_jobs()

    # Add to background tasks
    background_tasks.add_task(background_segmentation, job_id, req)

    # Return immediate response with job_id
    return SegmentationResponse(
        segments=[],
        duration=0,
        language=req.language,
        num_speakers=0,
        device="pending",
        mode=req.mode,
        processing_time=0,
        job_id=job_id
    )


@app.post("/segment/sync", response_model=SegmentationResponse)
async def segment_video_sync(req: QuickSegmentRequest):
    """
    Synchronous segmentation — metadata only, no clip cutting.
    Blocks until complete. Use for short clips only.
    """
    video_path = req.video_path
    if not os.path.isabs(video_path):
        video_path = os.path.join(SHARED_PATH, "uploads", video_path)

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video not found: {video_path}")

    try:
        segmenter = VideoSegmenter(
            mode="fast",
            whisper_model=WHISPER_MODEL,
            hf_token=HF_TOKEN,
            num_speakers=req.num_speakers,
            output_dir=SONORA_DATA_DIR
        )

        async with HardwareLock.locked_async("Segmenter", priority=2):
            result = await segmenter.segment_video(
                video_path=video_path,
                language=req.language,
                min_segment_duration=0.5,
                max_segment_duration=15.0,
                cut_clips=False,  # No cutting in sync mode
                isolate_vocals=True
            )

        response_data = _result_to_dict(result)
        return SegmentationResponse(**response_data)

    except Exception as e:
        logger.error(f"Sync segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status and result of a segmentation job."""
    if job_id not in segmentation_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return segmentation_jobs[job_id]


@app.get("/jobs")
async def list_jobs():
    """List all segmentation jobs."""
    return {
        "jobs": [
            {"id": jid, **job}
            for jid, job in segmentation_jobs.items()
        ]
    }


@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a segmentation job."""
    if job_id not in segmentation_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    del segmentation_jobs[job_id]
    save_jobs()
    return {"status": "deleted", "job_id": job_id}


@app.post("/speakers/rename")
async def rename_speaker(job_id: str, old_name: str, new_name: str):
    """
    Rename a speaker across all segments in a job.
    Returns updated segments.
    """
    if job_id not in segmentation_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = segmentation_jobs[job_id]
    if job.get("result") is None:
        raise HTTPException(status_code=400, detail="Job has no results yet")

    segments = job["result"]["segments"]
    for seg in segments:
        if seg["speaker"] == old_name:
            seg["speaker"] = new_name
        for w in seg.get("words", []):
            if w["speaker"] == old_name:
                w["speaker"] = new_name

    save_jobs()
    return {"status": "renamed", "old_name": old_name, "new_name": new_name}


@app.post("/segments/merge")
async def merge_segments(job_id: str, segment_ids: List[str]):
    """Merge two or more adjacent segments into one."""
    if job_id not in segmentation_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = segmentation_jobs[job_id]
    if job.get("result") is None:
        raise HTTPException(status_code=400, detail="Job has no results yet")

    segments = job["result"]["segments"]
    id_to_seg = {s["id"]: s for s in segments}

    # Validate all IDs exist
    for sid in segment_ids:
        if sid not in id_to_seg:
            raise HTTPException(status_code=404, detail=f"Segment {sid} not found")

    # Sort by start time
    to_merge = sorted([id_to_seg[sid] for sid in segment_ids], key=lambda s: s["start"])

    # Merge
    merged = {
        "id": to_merge[0]["id"],
        "index": to_merge[0]["index"],
        "start": to_merge[0]["start"],
        "end": to_merge[-1]["end"],
        "duration": to_merge[-1]["end"] - to_merge[0]["start"],
        "speaker": to_merge[0]["speaker"],  # Use first segment's speaker
        "text": " ".join(s["text"] for s in to_merge),
        "words": [w for s in to_merge for w in s.get("words", [])],
        "clip_path": None,  # Merged clip needs re-cutting
        "thumbnail_path": to_merge[0].get("thumbnail_path")
    }

    # Remove merged segments, add merged one
    new_segments = [s for s in segments if s["id"] not in segment_ids]
    new_segments.append(merged)
    new_segments.sort(key=lambda s: s["start"])

    # Re-index
    for i, s in enumerate(new_segments):
        s["index"] = i

    job["result"]["segments"] = new_segments
    save_jobs()

    return {"status": "merged", "segment_count": len(new_segments)}


@app.post("/segments/split")
async def split_segment(job_id: str, segment_id: str, split_time: float):
    """Split a segment at a given timestamp."""
    if job_id not in segmentation_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = segmentation_jobs[job_id]
    if job.get("result") is None:
        raise HTTPException(status_code=400, detail="Job has no results yet")

    segments = job["result"]["segments"]
    seg = next((s for s in segments if s["id"] == segment_id), None)
    if not seg:
        raise HTTPException(status_code=404, detail=f"Segment {segment_id} not found")

    if split_time <= seg["start"] or split_time >= seg["end"]:
        raise HTTPException(status_code=400, detail="Split time must be within segment bounds")

    # Split words
    words_before = [w for w in seg.get("words", []) if w["start"] < split_time]
    words_after = [w for w in seg.get("words", []) if w["start"] >= split_time]

    import uuid

    seg1 = {
        "id": seg["id"],
        "index": seg["index"],
        "start": seg["start"],
        "end": split_time,
        "duration": split_time - seg["start"],
        "speaker": seg["speaker"],
        "text": " ".join(w["text"] for w in words_before) if words_before else seg["text"],
        "words": words_before,
        "clip_path": None,
        "thumbnail_path": seg.get("thumbnail_path")
    }

    seg2 = {
        "id": str(uuid.uuid4())[:8],
        "index": seg["index"] + 1,
        "start": split_time,
        "end": seg["end"],
        "duration": seg["end"] - split_time,
        "speaker": seg["speaker"],
        "text": " ".join(w["text"] for w in words_after) if words_after else "",
        "words": words_after,
        "clip_path": None,
        "thumbnail_path": None
    }

    new_segments = [s for s in segments if s["id"] != segment_id]
    new_segments.extend([seg1, seg2])
    new_segments.sort(key=lambda s: s["start"])

    for i, s in enumerate(new_segments):
        s["index"] = i

    job["result"]["segments"] = new_segments
    save_jobs()

    return {"status": "split", "segment_count": len(new_segments)}


# ─────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Pre-warm: log configuration on startup."""
    import torch

    logger.info("=" * 60)
    logger.info("Sonora Segmenter Service Starting")
    logger.info(f"  Port: {PORT}")
    logger.info(f"  Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    logger.info(f"  Whisper Model: {WHISPER_MODEL}")
    logger.info(f"  Mode: {DEFAULT_MODE}")
    logger.info(f"  HF Token: {'present' if HF_TOKEN else 'MISSING'}")
    logger.info(f"  Shared Path: {SHARED_PATH}")
    logger.info(f"  Data Dir: {SONORA_DATA_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
