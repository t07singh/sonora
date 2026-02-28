from fastapi import FastAPI, HTTPException, Body
import os
import torch
import logging
from src.core.reliability import get_device, HardwareLock
import demucs.separate
import shlex

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.separator.service")

app = FastAPI(title="Sonora Separator (Demucs v4)")

SHARED_PATH = os.getenv("SHARED_PATH", "/tmp/sonora")

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "separator", 
        "device": get_device(),
        "model": "htdemucs (Demucs v4)"
    }

@app.post("/separate")
@app.post("/process")
async def separate_audio(payload: dict = Body(...)):
    filename = payload.get("filename") or payload.get("rel_path")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename missing")
    
    input_path = os.path.join(SHARED_PATH, filename)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail=f"File not found: {input_path}")

    output_dir = os.path.join(SHARED_PATH, "stems")
    os.makedirs(output_dir, exist_ok=True)

    # Guard GPU resources - Separation is Priority 2 (Heavy)
    async with HardwareLock.locked_async("Demucs-Separation", priority=2):
        try:
            logger.info(f"🏗️ [PROCESSING] Starting Demucs separation for {input_path}")
            
            # Using demucs.separate main entry point
            # Standard htdemucs model
            model = "htdemucs"
            
            # Construct arguments for demucs
            args = ["-n", model, "-o", output_dir, input_path]
            
            # Execute separation
            demucs.separate.main(args)
            
            # Demucs creates a folder structure: output_dir/model/filename_no_ext/stems...
            # We need to locate the stems and Return them
            # For simplicity in this swarm, we'll Return the stem paths
            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            stem_path = os.path.join(output_dir, model, base_filename)
            
            logger.info(f"✅ [SUCCESS] Separation complete. Stems at {stem_path}")
            return {
                "status": "success",
                "stems_dir": stem_path,
                "vocals": os.path.join(stem_path, "vocals.wav"),
                "no_vocals": os.path.join(stem_path, "no_vocals.wav")
            }
            
        except Exception as e:
            logger.error(f"❌ Separation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
