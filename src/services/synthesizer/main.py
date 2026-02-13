from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from src.core.reliability import retry_api_call, get_device
from src.services.synthesizer.vibevoice import VibeVoiceTTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.synthesizer.service")

app = FastAPI(title="Sonora Synthesizer Service")
# Initialize engine on startup to warm up GPU/CPU models
tts_engine = VibeVoiceTTS()

class SynthesisRequest(BaseModel):
    text: str
    speaker_id: str = "Alice [EN]"
    emotion: str = "Neutral" # Options: Happy, Sad, Excited, Angry
    speed: float = 1.0

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "synthesizer", 
        "device": get_device(),
        "engine": "VibeVoice v5.2"
    }

@app.post("/synthesize")
@retry_api_call # Using Hardened Armor!
async def run_synthesis(request: SynthesisRequest):
    """
    Hardened entry point for voice synthesis.
    Routes to the high-end VibeVoice core.
    """
    try:
        logger.info(f"🎤 Request: [{request.speaker_id}] Emotion={request.emotion} Text='{request.text[:30]}...'")
        
        # Pass the request to the core VibeVoice logic
        audio_path = tts_engine.generate(
            text=request.text,
            speaker=request.speaker_id,
            emotion=request.emotion,
            speed=request.speed
        )
        
        return {
            "status": "success", 
            "file_path": audio_path,
            "metadata": {
                "latency_optimized": True,
                "device": get_device()
            }
        }
    except Exception as e:
        logger.error(f"❌ Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
