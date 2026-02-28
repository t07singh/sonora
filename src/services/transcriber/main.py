from fastapi import FastAPI, HTTPException
import os
import json
import torch
import time
import logging
from src.core.reliability import get_device, HardwareLock
from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.transcriber.service")

app = FastAPI(title="Sonora Transcriber")

SHARED_PATH = os.getenv("SHARED_PATH", "/tmp/sonora")
MODEL_SIZE = os.getenv("WHISPER_MODEL", "large-v3")
MODEL_PATH = "models/whisper"

# Lazy load model to prevent OOM on startup
_model = None

def load_model():
    global _model
    if _model is None:
        device = get_device()
        logger.info(f"🚀 Loading Whisper {MODEL_SIZE} on {device}...")
        _model = WhisperModel(
            MODEL_SIZE, 
            device=device, 
            compute_type="float16" if device == "cuda" else "int8",
            download_root=MODEL_PATH
        )
    return _model

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "transcriber",
        "device": get_device(),
        "model": MODEL_SIZE
    }

@app.post("/transcribe")
@app.post("/process")
async def process_audio(payload: dict):
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename missing")
    
    # Path Resolution: Try SHARED_PATH first, then fallback to direct path
    input_path = os.path.join(SHARED_PATH, filename)
    if not os.path.exists(input_path):
        input_path = filename # Try absolute/relative path if not in SHARED_PATH
        
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail=f"Audio file not found: {input_path}")
    
    # Sequential Hardware Guard
    async with HardwareLock.locked_async("Whisper-ASR", priority=1):
        try:
            model = load_model()
            logger.info(f"🧬 [INFERENCE] Transcribing {input_path}...")
            
            segments, info = model.transcribe(input_path, beam_size=5, word_timestamps=True)
            
            # Extract detailed segment data for dubbing sync
            processed_segments = []
            full_text = []
            for s in segments:
                processed_segments.append({
                    "start": s.start,
                    "end": s.end,
                    "text": s.text.strip(),
                    "words": [{"word": w.word, "start": w.start, "end": w.end} for w in s.words] if s.words else []
                })
                full_text.append(s.text.strip())
            
            result = {
                "status": "success",
                "text": " ".join(full_text),
                "segments": processed_segments,
                "language": info.language,
                "device": get_device(),
                "timestamp": time.time()
            }
            
            # Optional: persist to SHARED_PATH
            output_path = os.path.join(SHARED_PATH, f"transcript_{int(time.time())}.json")
            with open(output_path, "w") as f:
                json.dump(result, f)
            
            logger.info(f"✅ [SUCCESS] Transcription complete for {filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
