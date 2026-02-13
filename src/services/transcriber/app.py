
import os
import logging
import time
import gc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from faster_whisper import WhisperModel
from src.core.reliability import get_device, log_path_consistency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora-asr")

app = FastAPI(title="Sonora ASR Microservice (Faster-Whisper INT8)")

# Configuration
DEVICE = "cpu"  # Hardened for CPU efficiency
COMPUTE_TYPE = "int8"
MODEL_SIZE = "base"
SHARED_PATH = "/tmp/sonora"

class TranscribeRequest(BaseModel):
    rel_path: str # Path relative to /tmp/sonora

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "node": "Faster-Whisper-Base",
        "device": DEVICE,
        "compute": COMPUTE_TYPE,
        "mode": "Transient_Worker",
        "vram_allocated": "N/A (CPU Mode)"
    }

@app.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    # Resolve and log absolute path for debugging ghost paths
    full_path = log_path_consistency(os.path.join(SHARED_PATH, request.rel_path), "ASR_NODE")
    
    if not os.path.exists(full_path):
        logger.error(f"❌ Handshake Failure: File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"Audio file not found at {full_path}")

    try:
        logger.info(f"👂 Swarm Ingesting: {request.rel_path}")
        
        # Load model in INT8 mode (Optimized for CPU balance)
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        
        segments, info = model.transcribe(full_path, beam_size=5)
        
        results = []
        full_text = ""
        for segment in segments:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            full_text += segment.text + " "

        # Memory management
        del model
        gc.collect()
        
        logger.info(f"✅ Success: {len(results)} segments processed.")
        
        return {
            "text": full_text.strip(),
            "segments": results,
            "language": info.language,
            "engine": "Faster-Whisper-INT8"
        }
    except Exception as e:
        logger.error(f"❌ Inference error: {str(e)}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
