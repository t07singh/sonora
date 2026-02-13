
import os
import whisper
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asr-service")

app = FastAPI(title="Sonora ASR Service")

# Shared data directory (mapped via Docker)
DATA_PATH = "/tmp/sonora"
MODEL_TYPE = os.getenv("WHISPER_MODEL", "base")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

logger.info(f"🚀 Initializing Whisper '{MODEL_TYPE}' on {DEVICE}...")
model = whisper.load_model(MODEL_TYPE, device=DEVICE)
logger.info("✅ Whisper Model Ready.")

class TranscribeRequest(BaseModel):
    file_path: str # Path relative to /tmp/sonora

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "device": DEVICE,
        "model": MODEL_TYPE
    }

@app.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    # Construct full internal path
    full_path = os.path.join(DATA_PATH, request.file_path)
    
    if not os.path.exists(full_path):
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"Audio file not found at {full_path}")

    try:
        logger.info(f"👂 Transcribing: {request.file_path}")
        # Run inference
        result = model.transcribe(full_path, verbose=False)
        
        # Structure response to match Sonora's expected format
        return {
            "text": result["text"],
            "segments": result["segments"],
            "language": result.get("language", "ja")
        }
    except Exception as e:
        logger.error(f"❌ Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
