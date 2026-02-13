import os
import logging
import time
import gc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from faster_whisper import WhisperModel
from src.core.reliability import get_device

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora-asr")

app = FastAPI(title="Sonora ASR Microservice (Faster-Whisper INT8)")

# Configuration
DEVICE = "cpu"  # Hardened for CPU efficiency
COMPUTE_TYPE = "int8"
MODEL_SIZE = "large-v3"
SHARED_PATH = "/tmp/sonora"

class TranscribeRequest(BaseModel):
    audio_path: str # Path relative to /tmp/sonora

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "node": "Faster-Whisper-V3",
        "device": DEVICE,
        "compute": COMPUTE_TYPE,
        "mode": "Transient_Worker"
    }

@app.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    # Resolve full internal path within shared volume
    full_path = os.path.join(SHARED_PATH, request.audio_path)
    
    if not os.path.exists(full_path):
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"Audio file not found at {full_path}")

    try:
        logger.info(f"👂 Transient Node Ingesting: {request.audio_path}")
        
        # 1. Load model in INT8 mode (Optimized for CPU)
        # Transient pattern: Load weight into RAM only during inference
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        
        # 2. Transcribe with VAD filter to prevent hallucinations
        segments, info = model.transcribe(
            full_path, 
            beam_size=5, 
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        results = []
        full_text = ""
        for segment in segments:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            full_text += segment.text + " "

        # 3. CRITICAL: Manual memory flush
        # Freeing resources for the next swarm agent
        del model
        gc.collect()
        
        logger.info(f"✅ Transcription Success: {len(results)} segments generated.")
        
        return {
            "text": full_text.strip(),
            "segments": results,
            "language": info.language,
            "language_probability": info.language_probability,
            "engine": "Faster-Whisper-V3-INT8"
        }
    except Exception as e:
        logger.error(f"❌ Transcription error: {str(e)}")
        # Ensure garbage collection if it crashed mid-inference
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
