from fastapi import FastAPI, HTTPException
import os
import json
import torch
import time
import logging
from src.core.reliability import get_device, HardwareLock
from faster_whisper import WhisperModel
# from src.services.transcriber.segmenter import get_segmenter (Moved to lazy import)

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
            cloud_offload = os.getenv("CLOUD_OFFLOAD", "false").lower() == "true"
            
            if cloud_offload:
                logger.info(f"☁️ [CLOUD OFFLOAD] Offloading Transcription to Groq API for {input_path}")
                import groq
                import math
                import asyncio
                
                groq_key = os.getenv("GROQ_API_KEY")
                if not groq_key:
                    raise HTTPException(status_code=500, detail="GROQ_API_KEY missing for Cloud Offload")
                    
                client = groq.AsyncGroq(api_key=groq_key)
                
                # 5-attempt retry loop with exponential backoff
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        with open(input_path, "rb") as audio_file:
                            response = await client.audio.transcriptions.create(
                                file=(os.path.basename(input_path), audio_file),
                                model="whisper-large-v3",
                                prompt="Transcribe this Japanese audio. Pay attention to anime/dramatic nuances.",
                                response_format="verbose_json",
                                timestamp_granularities=["word"]
                            )
                        
                        # Process Groq verbose JSON response
                        segments = getattr(response, 'segments', [])
                        
                        processed_segments = []
                        full_text = []
                        
                        for s in segments:
                            # Groq verbose json returns dicts or objects
                            seg_dict = s if isinstance(s, dict) else s.dict() if hasattr(s, 'dict') else s
                            # In modern Groq sdk, it is usually a dict via json
                            
                            words_list = seg_dict.get('words', []) if isinstance(seg_dict, dict) else getattr(seg_dict, 'words', [])
                            words_formatted = []
                            for w in words_list:
                                w_dict = w if isinstance(w, dict) else w.dict() if hasattr(w, 'dict') else w.__dict__
                                words_formatted.append({
                                    "word": w_dict.get("word", ""),
                                    "start": w_dict.get("start", 0),
                                    "end": w_dict.get("end", 0)
                                })
                            
                            st = seg_dict.get("start", 0) if isinstance(seg_dict, dict) else getattr(seg_dict, "start", 0)
                            en = seg_dict.get("end", 0) if isinstance(seg_dict, dict) else getattr(seg_dict, "end", 0)
                            txt = (seg_dict.get("text", "") if isinstance(seg_dict, dict) else getattr(seg_dict, "text", "")).strip()
                            
                            processed_segments.append({
                                "start": st,
                                "end": en,
                                "text": txt,
                                "words": words_formatted
                            })
                            full_text.append(txt)
                            
                        result = {
                            "status": "success",
                            "text": " ".join(full_text),
                            "segments": processed_segments,
                            "language": getattr(response, "language", "ja"),
                            "device": "Cloud (Groq)",
                            "timestamp": time.time()
                        }
                        
                        logger.info(f"✅ [SUCCESS] Cloud Transcription complete for {filename}")
                        return result
                        
                    except Exception as e:
                        if attempt == max_retries - 1:
                            logger.error(f"❌ Groq Transcription failed after {max_retries} attempts: {e}")
                            raise HTTPException(status_code=500, detail=str(e))
                        
                        delay = min(60, 2 ** attempt * 5) # 5s, 10s, 20s, 40s, 60s
                        # Avoid rate limit floods
                        logger.warning(f"⚠️ Groq API Error (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {delay}s...")
                        import asyncio
                        await asyncio.sleep(delay)
            else:
                model = load_model()
                logger.info(f"🧬 [INFERENCE] Transcribing {input_path}...")
                
                segments, info = model.transcribe(input_path, beam_size=5, word_timestamps=True)
                
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
                
                logger.info(f"✅ [SUCCESS] Local Transcription complete for {filename}")
                return result
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/segment")
async def segment_video(payload: dict):
    video_path = payload.get("video_path")
    if not video_path:
        raise HTTPException(status_code=400, detail="video_path missing")
        
    # Guard against concurrent AI loading
    async with HardwareLock.locked_async("Whisper-Segmentation", priority=1):
        try:
            logger.info(f"✂️ [SEGMENTATION] Cutting video: {video_path}")
            from src.services.transcriber.segmenter import get_segmenter
            segmenter = get_segmenter()
            
            # Use to_thread for heavy CPU/GPU blocking operations
            import asyncio
            segments = await asyncio.to_thread(segmenter.segment_video, video_path)
            
            return {
                "status": "success",
                "segments": segments,
                "count": len(segments),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"❌ Segmentation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, timeout_keep_alive=1200)
