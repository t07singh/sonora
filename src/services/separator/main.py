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

from src.core.path_manager import SHARED_ROOT

app = FastAPI(title="Sonora Separator (Demucs v4)")

SHARED_PATH = str(SHARED_ROOT)

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
            cloud_offload = os.getenv("CLOUD_OFFLOAD", "false").lower() == "true"
            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            stem_path = os.path.join(output_dir, "htdemucs", base_filename)
            
            if cloud_offload:
                logger.info(f"☁️ [CLOUD OFFLOAD] Offloading separation to HF Spaces for {input_path}")
                from gradio_client import Client
                import shutil
                import asyncio
                import soundfile as sf
                
                hf_token = os.getenv("HF_TOKEN")
                if not hf_token:
                    logger.warning("HF_TOKEN is missing. Separation may fail or be heavily rate-limited.")
                
                try:
                    logger.info("Connecting to afrideva/demucs...")
                    client = Client("afrideva/demucs", hf_token=hf_token)
                except Exception as e:
                    logger.warning(f"Primary space failed: {e}. Trying fallback...")
                    client = Client("facebook/demucs", hf_token=hf_token)
                
                logger.info("Sending audio to Cloud Demucs... (This may take several minutes)")
                res_vocals, res_bass, res_drums, res_other = await asyncio.to_thread(
                    client.predict,
                    audio=input_path,
                    api_name="/predict"
                )
                
                os.makedirs(stem_path, exist_ok=True)
                shutil.move(res_vocals, os.path.join(stem_path, "vocals.wav"))
                
                # Combine bass, drums, and other into a single 'no_vocals' track
                logger.info("Mixing instrumental stems into no_vocals.wav...")
                v_bass, sr_bass = sf.read(res_bass)
                v_drums, sr_drums = sf.read(res_drums)
                v_other, sr_other = sf.read(res_other)
                
                no_vocals_mix = v_bass + v_drums + v_other
                no_vocals_path = os.path.join(stem_path, "no_vocals.wav")
                sf.write(no_vocals_path, no_vocals_mix, sr_bass)
                
                # Also save the individual stems for Audio Surgery Phase 5
                shutil.move(res_drums, os.path.join(stem_path, "drums.wav"))
                shutil.move(res_bass, os.path.join(stem_path, "bass.wav"))
                shutil.move(res_other, os.path.join(stem_path, "other.wav"))

            else:
                logger.info(f"🏗️ [PROCESSING] Starting local Demucs separation for {input_path}")
                model = "htdemucs"
                device = get_device()
                args = ["-n", model, "-o", output_dir, "--device", device, input_path]
                
                # Execute separation
                demucs.separate.main(args)
            
            logger.info(f"✅ [SUCCESS] Separation complete. Stems at {stem_path}")
            
            # Granular Mappings for Sound Engineering 2.0
            results = {
                "status": "success",
                "stems_dir": stem_path,
                "vocals": os.path.join(stem_path, "vocals.wav"),
                "no_vocals": os.path.join(stem_path, "no_vocals.wav"),
                "music": os.path.join(stem_path, "no_vocals.wav"),
                "chat": os.path.join(stem_path, "vocals.wav"), # Initial fallback
                "cues": os.path.join(stem_path, "vocals.wav"),
                "songs": os.path.join(stem_path, "no_vocals.wav")
            }
            
            # If granular files exist (from sub-isolation or cloud), use them
            if os.path.exists(c_path := os.path.join(stem_path, "vocal_chat.wav")):
                results["chat"] = c_path
            if os.path.exists(e_path := os.path.join(stem_path, "emotional_cues.wav")):
                results["cues"] = e_path
            if os.path.exists(s_path := os.path.join(stem_path, "background_songs.wav")):
                results["songs"] = s_path
                
            return results
            
        except Exception as e:
            logger.error(f"❌ Separation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=1200)
