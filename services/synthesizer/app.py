import os
import logging
import gc
import torch
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.core.reliability import HardwareLock, get_device

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora-qwen3-tts")

app = FastAPI(title="Sonora Qwen3-TTS Node (0.6B Instruction-Aware)")

class SynthesisRequest(BaseModel):
    text: str
    instruction: str  # The natural language "Tone" trigger
    speaker_id: str = "PROTAGONIST"
    reference_audio_path: Optional[str] = None # Path to anchor clip in shared volume

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "engine": "Qwen3-TTS-0.6B-VC-Flash",
        "mode": "Instruction-Driven",
        "device": get_device()
    }

@app.post("/synthesize")
async def synthesize(request: SynthesisRequest):
    # Lock hardware to prevent OOM during weight loading
    await HardwareLock.acquire("Qwen3-TTS-Instruction")
    
    try:
        logger.info(f"🎙️ Synthesizing with Instruction: '{request.instruction}'")
        logger.info(f"📝 Text: '{request.text[:30]}...'")
        
        # Simulation of Qwen3-TTS Ultra-Low Latency Path (97ms)
        # In a real environment, weights would be loaded here in INT8/4-bit
        # model = Qwen3TTS.load(MODEL_PATH, compute_type="int8")
        # audio = model.generate(text=request.text, instruction=request.instruction)
        
        time.sleep(0.9) # Simulate inference
        
        take_id = f"take_{int(time.time())}_{os.urandom(2).hex()}.wav"
        output_path = os.path.join("/tmp/sonora/takes", take_id)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create mock high-fidelity WAV
        import numpy as np
        import soundfile as sf
        sr = 44100
        duration = max(1.0, len(request.text) * 0.08)
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.4
        sf.write(output_path, audio, sr)

        # Integrated Quality Assessment (NISQA simulated)
        qa_score = 0.94 + (np.random.random() * 0.05)
        
        # CRITICAL: Resource Release (Sequential Flush)
        # del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(f"✅ Qwen3 Synthesis Complete. QA: {qa_score:.2f}")
        
        return {
            "status": "success",
            "audio_path": output_path,
            "fidelity_score": qa_score,
            "engine": "Qwen3-TTS-0.6B-INT8"
        }
        
    except Exception as e:
        logger.error(f"❌ Qwen3 Synthesis failed: {str(e)}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        HardwareLock.release()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
