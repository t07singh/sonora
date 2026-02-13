import os
import subprocess
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.reliability import retry_api_call, get_device

app = FastAPI(title="Sonora Separator Service")
logger = logging.getLogger("sonora.separator")

class SeparateRequest(BaseModel):
    rel_path: str
    model: str = "htdemucs"

@app.get("/health")
def health():
    return {"status": "healthy", "device": get_device(), "engine": "Demucs v4"}

@app.post("/separate")
@retry_api_call(max_retries=2)
async def separate(request: SeparateRequest):
    full_path = os.path.join("/tmp/sonora", request.rel_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    output_dir = os.path.join("/tmp/sonora/stems", os.path.basename(full_path).split('.')[0])
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Separating {request.rel_path} using {request.model}...")
    
    cmd = [
        "demucs",
        "-o", output_dir,
        "-n", request.model,
        full_path
    ]
    if get_device() == "cpu":
        cmd.extend(["-d", "cpu"])

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            "status": "success",
            "stems_path": output_dir,
            "stems": ["vocals.wav", "no_vocals.wav", "bass.wav", "drums.wav", "other.wav"]
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Demucs Error: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Separation engine error: {e.stderr}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)