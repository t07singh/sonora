from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from src.core.reliability import retry_api_call, get_device, HardwareLock
from src.services.synthesizer.qwen3_engine import Qwen3Engine
from src.services.synthesizer.fish_s2_engine import FishS2Engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.synthesizer.service")

# Initialize engines
qwen3_stability = Qwen3Engine()
fish_s2_primary = FishS2Engine()

app = FastAPI(title="Sonora Synthesizer Service")

class SynthesisRequest(BaseModel):
    text: str
    speaker_id: str = "Alice [EN]"
    emotion: str = "Neutral"
    speed: float = 1.0
    is_main_character: bool = True

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "synthesizer", 
        "device": get_device(),
        "engines": {
            "primary": "Fish Audio S2 (High-Fidelity)",
            "stability": "Qwen3-TTS (1.7B Hardened)"
        }
    }

@app.post("/synthesize")
@retry_api_call
async def run_synthesis(request: SynthesisRequest):
    """
    Dual-Engine Entry Point:
    - Main Characters -> Fish Audio S2 (Priority 2)
    - Background Characters -> Qwen3-TTS (Priority 3)
    """
    engine_name = "Fish-S2" if request.is_main_character else "Qwen3-TTS"
    priority = 2 if request.is_main_character else 3
    
    # Guard GPU resources
    async with HardwareLock.locked_async(engine_name, priority=priority):
        try:
            logger.info(f"🎤 [{engine_name}] Request: [{request.speaker_id}] Text='{request.text[:30]}...'")
            
            if request.is_main_character:
                audio_data, sr = fish_s2_primary.generate(
                    text=request.text,
                    voice_id=request.speaker_id,
                    emotion=request.emotion
                )
            else:
                audio_data, sr = qwen3_stability.generate(
                    text=request.text,
                    voice_id=request.speaker_id,
                    emotion=request.emotion
                )
            
            # Save to temporary path
            from fastapi.responses import FileResponse
            from pathlib import Path
            import soundfile as sf
            import time
            
            temp_dir = Path("/tmp/sonora/outputs")
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_name = f"{engine_name.lower()}_{int(time.time())}.wav"
            output_path = temp_dir / output_name
            sf.write(str(output_path), audio_data, sr)
            
            return FileResponse(
                path=str(output_path), 
                media_type="audio/wav",
                filename=output_name
            )
        except Exception as e:
            logger.error(f"❌ {engine_name} Synthesis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, timeout_keep_alive=1200)
