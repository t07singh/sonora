from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import os
import sys
import logging

logger = logging.getLogger("sonora.api")

# Ensure project root is in path
sys.path.append(os.getcwd())

from sonora.core.project_manager import SonoraProject
from sonora.core.orchestrator import SonoraOrchestrator, group_words_by_pause, count_syllables, estimate_japanese_morae
from sonora.utils.voice_registry import save_character_voice
from api.auth import SonoraAuthMiddleware
# Segmenter service URL (new dedicated segmentation microservice)
SEGMENTER_URL = os.getenv("SEGMENTER_URL", "http://sonora-segmenter:8004")

app = FastAPI(title="Sonora AI Studio API")

# --- Request Models ---
class SegmentRequest(BaseModel):
    video_path: str
    project_id: Optional[str] = "default"
    language: Optional[str] = "ja"
    mode: Optional[str] = "fast"  # "fast" or "precise"
    aligner: Optional[str] = "qwen3"  # "qwen3" (SOTA) or "wav2vec2" (legacy)
    cut_clips: Optional[bool] = True
    isolate_vocals: Optional[bool] = True
    num_speakers: Optional[int] = None

class TranslateRequest(BaseModel):
    segments: List[Dict]
    style: Optional[str] = "Anime"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Middleware
app.add_middleware(SonoraAuthMiddleware)

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# --- Request Models ---
class RefactorRequest(BaseModel):
    text: str
    target_syllables: int
    style: str = "Anime"
    engine: str = "local" # local or gemini

class RegistrySaveRequest(BaseModel):
    character_name: str
    audio_path: str
    metadata: Optional[Dict] = {}

class SynthesizeRequest(BaseModel):
    segments: List[Dict]
    translations: List[str]
    voice_id: str
    video_path: str
    stems: Optional[Dict] = None

# --- Routes ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "sonora-backend", "mode": "swarm_intelligence"}

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Body, BackgroundTasks
import uuid

from src.core.path_manager import SHARED_ROOT
# --- Job Storage ---
SHARED_PATH = str(SHARED_ROOT)
JOBS_FILE = os.path.join(SHARED_PATH, "jobs.json")
analysis_jobs = {}

def save_jobs():
    try:
        os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
        with open(JOBS_FILE, "w") as f:
            json.dump(analysis_jobs, f)
    except Exception as e:
        logger.error(f"Failed to save jobs: {e}")

def load_jobs():
    global analysis_jobs
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                analysis_jobs = json.load(f)
        except:
            analysis_jobs = {}

# Load on startup
load_jobs()

# --- Helper for Background Processing ---
async def background_segmentation(job_id: str, video_path: str, language: str = "ja",
                                       mode: str = "fast", cut_clips: bool = True,
                                       isolate_vocals: bool = True, num_speakers: Optional[int] = None,
                                       **kwargs):
    """
    Proxy segmentation request to the dedicated Segmenter service (port 8004).
    This replaces the old transcriber-based segmentation with the full pipeline:
    Demucs → Silero VAD → Whisper → pyannote → Merge → Cut
    """
    import httpx

    try:
        await manager.broadcast({
            "type": "status",
            "msg": "Initiating Neural Segmentation (Sonora Segmenter Service)...",
            "job_id": job_id
        })

        # Call the dedicated segmenter service
        segment_url = f"{SEGMENTER_URL}/segment"
        payload = {
            "video_path": video_path,
            "language": language,
            "mode": mode,
            "aligner": kwargs.get("aligner", "qwen3"),
            "cut_clips": cut_clips,
            "isolate_vocals": isolate_vocals,
            "num_speakers": num_speakers
        }

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(segment_url, json=payload)

            if response.status_code != 200:
                raise Exception(f"Segmenter service returned error {response.status_code}: {response.text}")

            data = response.json()
            segmenter_job_id = data.get("job_id")

        # Now poll the segmenter service for completion
        poll_url = f"{SEGMENTER_URL}/job/{segmenter_job_id}"
        max_polls = 120  # 10 minutes at 5s intervals
        poll_count = 0

        while poll_count < max_polls:
            await asyncio.sleep(5)
            poll_count += 1

            async with httpx.AsyncClient(timeout=30.0) as client:
                poll_response = await client.get(poll_url)
                if poll_response.status_code != 200:
                    continue

                poll_data = poll_response.json()
                status = poll_data.get("status", "")
                progress = poll_data.get("progress", 0)

                # Broadcast progress
                if status == "Processing":
                    await manager.broadcast({
                        "type": "status",
                        "msg": f"Segmenting: {status} ({progress:.0%})",
                        "job_id": job_id,
                        "progress": progress
                    })
                elif status == "Complete":
                    result = poll_data.get("result", {})
                    segments = result.get("segments", [])

                    analysis_jobs[job_id]["status"] = "Complete"
                    analysis_jobs[job_id]["result"] = {
                        "segments": segments,
                        "num_speakers": result.get("num_speakers", 0),
                        "duration": result.get("duration", 0),
                        "language": result.get("language", language),
                        "mode": result.get("mode", mode),
                        "processing_time": result.get("processing_time", 0)
                    }
                    save_jobs()

                    await manager.broadcast({
                        "type": "status",
                        "msg": f"Segmentation Complete: {len(segments)} segments, "
                               f"{result.get('num_speakers', 0)} speakers.",
                        "success": True,
                        "job_id": job_id,
                        "segments_count": len(segments)
                    })
                    return

                elif status == "Error":
                    error_msg = poll_data.get("error", "Unknown segmentation error")
                    raise Exception(error_msg)

        raise Exception("Segmentation timed out after 10 minutes")

    except Exception as e:
        logger.error(f"Segmentation Proxy Job {job_id} failed: {e}")
        analysis_jobs[job_id]["status"] = "Error"
        analysis_jobs[job_id]["error"] = str(e)
        save_jobs()
        await manager.broadcast({"type": "status", "msg": f"Segmentation Failed: {str(e)}", "error": True, "job_id": job_id})

@app.post("/api/pipeline/segment")
async def pipeline_segment(background_tasks: BackgroundTasks, req: SegmentRequest):
    """
    Trigger the full segmentation pipeline via the dedicated Segmenter service.
    Pipeline: Demucs → Silero VAD → Whisper → pyannote → Merge → Cut clips
    Returns a job_id immediately; poll /api/job/{job_id} for results.
    """
    job_id = str(uuid.uuid4())

    analysis_jobs[job_id] = {
        "status": "Queued",
        "video_path": req.video_path,
        "project_id": req.project_id,
        "language": req.language,
        "mode": req.mode,
        "result": None,
        "error": None
    }
    save_jobs()

    background_tasks.add_task(
        background_segmentation, job_id, req.video_path,
        req.language, req.mode, req.cut_clips, req.isolate_vocals, req.num_speakers,
        **{"aligner": req.aligner}
    )
    return {"job_id": job_id, "status": "Segmentation Queued", "mode": req.mode, "aligner": req.aligner}

@app.post("/api/pipeline/translate")
async def pipeline_translate(req: TranslateRequest):
    """
    Translates a list of segments using high-speed neural link.
    """
    try:
        orch = SonoraOrchestrator("dummy.mp4")
        segments_for_orch = []
        for s in req.segments:
            if "words" in s:
                segments_for_orch.append(s["words"])
            else:
                segments_for_orch.append([{"word": s.get("original", ""), "start": s.get("start",0), "end": s.get("end",0)}])
        
        translations = await orch.translate_segments_batch(segments_for_orch, style=req.style)
        
        updated_segments = []
        for i, s in enumerate(req.segments):
            s["translation"] = translations[i] if i < len(translations) else "[ERROR]"
            s["targetFlaps"] = estimate_japanese_morae(s.get("original", ""))
            s["currentFlaps"] = count_syllables(s["translation"])
            updated_segments.append(s)
            
        return {"segments": updated_segments}
    except Exception as e:
        logger.error(f"Translation pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Original Analysis Logic ---
async def background_analysis(job_id: str, file_path: str, filename: str):
    async def update_job_status(msg: str):
        analysis_jobs[job_id]["status"] = msg
        save_jobs()
        await manager.broadcast({"type": "status", "msg": msg, "job_id": job_id})

    try:
        # Initialize orchestrator with the uploaded file path
        orch = SonoraOrchestrator(file_path)
        
        # 1. STEM SEPARATION
        await update_job_status("Neural Separation: Isolating stems (Demucs v4 Surgery)...")
        try:
            stems = await orch.run_separation()
            vocals_path = stems.get("vocals", file_path)
            music_path = stems.get("music", file_path)
            chat_path = stems.get("chat", file_path)
            cues_path = stems.get("cues", file_path)
            songs_path = stems.get("songs", file_path)
        except Exception as sep_error:
            logger.warning(f"Separation failed ({sep_error}), falling back to original audio for ASR.")
            await update_job_status(f"Separation Failed: Falling back to original audio.")
            vocals_path = music_path = chat_path = cues_path = songs_path = file_path

        
        # 2. WHISPER ASR
        await update_job_status("Whisper ASR: Running word-level extraction...")
        raw_words = await orch.run_transcription(chat_path or vocals_path)
        logger.info(f"🔍 [DIAGNOSTIC] Job {job_id}: Received {len(raw_words)} raw words.")
        
        # group_words_by_pause takes the flat word list and returns segments
        segments_raw = group_words_by_pause(raw_words)
        
        # 3. TRANSLATION
        await update_job_status("Neural Link: Translating content...")
        translations = await orch.translate_segments_batch(segments_raw)
        
        formatted_segments = []
        for i, seg in enumerate(segments_raw):
            original_text = " ".join([w.get('word', '') for w in seg])
            translated_text = translations[i] if i < len(translations) else "[ERROR]"
            
            # Skip noise/breath lines marked by the AI (Phase 2 Surgical Hygiene)
            if translated_text.upper() == "[EXTRANEOUS]":
                logger.info(f"✨ [HYGIENE] Purging noise segment {i}: '{original_text[:20]}...'")
                continue
            
            target_syllables = estimate_japanese_morae(original_text)
            
            formatted_segments.append({
                "id": str(i),
                "start": seg[0]['start'],
                "end": seg[-1]['end'],
                "original": original_text,
                "translation": translated_text,
                "targetFlaps": target_syllables, 
                "currentFlaps": count_syllables(translated_text),
                "speaker": seg[0].get('speaker', 'UNKNOWN'),
                "words": seg
            })
            
        analysis_jobs[job_id]["status"] = "Complete"
        analysis_jobs[job_id]["result"] = {
            "segments": formatted_segments,
            "stems": {
                "vocals": vocals_path,
                "music": music_path,
                "chat": chat_path,
                "cues": cues_path,
                "songs": songs_path
            }
        }
        save_jobs()
        await manager.broadcast({"type": "status", "msg": "Neural Link: Analysis Complete.", "success": True, "job_id": job_id})
        
    except Exception as e:
        import traceback
        logger.error(f"FATAL OUTER EXCEPTION: {e}")
        logger.error(traceback.format_exc())
        error_msg = f"Neural Link Error: {str(e)}"
        analysis_jobs[job_id]["status"] = "Error"
        analysis_jobs[job_id]["error"] = error_msg
        save_jobs()
        await manager.broadcast({"type": "status", "msg": error_msg, "error": True, "job_id": job_id})

@app.post("/api/analyze")
async def analyze_media(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_dir = SHARED_PATH
    os.makedirs(temp_dir, exist_ok=True)
    
    # Safe filename relative to SHARED_PATH (prevent collisions)
    clean_filename = file.filename.replace('/', '_').replace('\\', '_')
    safe_filename = f"{job_id}_{clean_filename}"
    file_path = os.path.join(temp_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    analysis_jobs[job_id] = {
        "status": "Starting...",
        "filename": safe_filename,
        "result": None,
        "error": None
    }
    save_jobs()
    
    background_tasks.add_task(background_analysis, job_id, file_path, safe_filename)
    return {"job_id": job_id, "status": "Queued"}

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    load_jobs() # Refresh from disk for cross-worker/restart consistency
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found in vault")
    return analysis_jobs[job_id]

@app.post("/api/refactor")
async def refactor_segment(req: RefactorRequest):
    """Surgical Rewrite: Now supports Gemini 3 Flash."""
    logger.info(f"Refactor request for: '{req.text[:50]}...' Target syllables: {req.target_syllables}")
    try:
        orch = SonoraOrchestrator("dummy.mp4") 
        result = await orch.refactor_line(req.text, req.target_syllables, req.style)
        new_text = result.get("text", "")
        provider = result.get("provider", "unknown")
        logger.info(f"Refactored result: '{new_text[:50]}...' (Engine: {provider})")
        return {"text": new_text, "engine": provider}
    except Exception as e:
        logger.error(f"Refactor failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/registry/save")
async def save_to_registry(req: RegistrySaveRequest):
    """Locks a character voice profile into the production asset vault."""
    try:
        success = save_character_voice(req.character_name, req.audio_path, req.metadata)
        if success:
            return {"status": "success", "msg": f"Character {req.character_name} asset locked."}
        raise Exception("Registry Write Failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def list_projects():
    # Return real projects plus a few demo ones if directory is empty
    projs = SonoraProject.list_projects("sonora/data")
    return {"projects": projs or ["NEO_TOKYO_PILOT", "SHIBUYA_INCIDENT_DUB"]}

@app.post("/api/synthesize")
async def synthesize_dub(req: SynthesizeRequest):
    """The Final Assembly: Neural Synthesis + Master Mix."""
    try:
        await manager.broadcast({"type": "status", "msg": "Neural Synthesis: Generating AI performance..."})
        orch = SonoraOrchestrator(req.video_path)
        
        # 1. Synthesis Pass
        takes = await orch.synthesize_segments(req.segments, req.translations, req.voice_id)
        
        # 2. Master Assembly Pass
        await manager.broadcast({"type": "status", "msg": "Master Continuity: Muxing with world track..."})
        master_path = await orch.assemble_final_dub(req.video_path, takes, req.segments, stems=req.stems)
        
        await manager.broadcast({"type": "status", "msg": "Dubbing Complete!", "success": True})
        return {"master_path": master_path}
        
    except Exception as e:
        error_msg = f"Synthesis Failed: {str(e)}"
        await manager.broadcast({"type": "status", "msg": error_msg, "error": True})
        raise HTTPException(status_code=500, detail=error_msg)

@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "ack", "msg": "Sync Active"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)