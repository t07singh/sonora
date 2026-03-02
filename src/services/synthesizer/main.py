from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from src.core.reliability import retry_api_call, get_device, HardwareLock
from src.services.synthesizer.qwen3_engine import Qwen3Engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.synthesizer.service")

app = FastAPI(title="Sonora Qwen3 Synthesizer Service")
# Initialize engine on startup
tts_engine = Qwen3Engine()

class SynthesisRequest(BaseModel):
    text: str
    speaker_id: str = "Alice [EN]"
    emotion: str = "Neutral"
    speed: float = 1.0

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "synthesizer", 
        "device": get_device(),
        "engine": "Qwen3-TTS (Hardened)"
    }

@app.post("/synthesize")
@retry_api_call
async def run_synthesis(request: SynthesisRequest):
    """
    Hardened entry point for Qwen3-TTS.
    Uses HardwareLock to prevent VRAM spikes.
    """
    # Guard GPU resources - Synthesis is Priority 3
    async with HardwareLock.locked_async("Qwen3-TTS", priority=3):
        try:
            logger.info(f"🎤 Qwen3 Request: [{request.speaker_id}] Text='{request.text[:30]}...'")
            
            # Generate audio data
            audio_data, sr = tts_engine.generate(
                text=request.text,
                voice_id=request.speaker_id,
                emotion=request.emotion
            )
            
            # Save to temporary path for the orchestrator to pick up
            from fastapi.responses import FileResponse
            from pathlib import Path
            import soundfile as sf
            import time
            
            temp_dir = Path("/tmp/sonora/outputs")
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_path = temp_dir / f"qwen3_{int(time.time())}.wav"
            sf.write(str(output_path), audio_data, sr)
            
            # Return the file directly so the Orchestrator's r.content works
            return FileResponse(
                path=str(output_path), 
                media_type="audio/wav",
                filename=output_path.name
            )
        except Exception as e:
            logger.error(f"❌ Qwen3 Synthesis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, timeout_keep_alive=1200)
