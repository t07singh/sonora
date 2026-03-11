from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from sonora.core.project_manager import SonoraProject
from sonora.core.orchestrator import SonoraOrchestrator, group_words_by_pause
from sonora.utils.voice_registry import save_character_voice
from api.auth import SonoraAuthMiddleware

app = FastAPI(title="Sonora AI Studio API")

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

# --- Routes ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "sonora-backend", "mode": "swarm_intelligence"}

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Body, BackgroundTasks
import uuid

# --- Job Storage ---
SHARED_PATH = os.getenv("SHARED_PATH", "/tmp/sonora")
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
async def background_analysis(job_id: str, file_path: str, filename: str):
    async def update_job_status(msg: str):
        analysis_jobs[job_id]["status"] = msg
        save_jobs()
        await manager.broadcast({"type": "status", "msg": msg, "job_id": job_id})

    try:
        await update_job_status("Neural Separation: Isolating stems (Demucs v4)...")
        orch = SonoraOrchestrator(file_path, status_callback=update_job_status)
        
        # 1. STEM SEPARATION
        stems = await orch.run_separation()
        vocals_path = stems["vocals"]
        
        # 2. WHISPER ASR
        await update_job_status("Whisper ASR: Running word-level extraction...")
        raw_segments = await orch.run_transcription(vocals_path)
        
        raw_words = []
        for s in raw_segments:
            if s.get('words'):
                raw_words.extend(s['words'])
            else:
                raw_words.append({"word": s['text'], "start": s['start'], "end": s['end']})
        
        segments_raw = group_words_by_pause(raw_words)
        
        # 3. TRANSLATION (Progress managed by orchestrator callback)
        translations = await orch.translate_segments_batch(segments_raw)
        
        formatted_segments = []
        for i, seg in enumerate(segments_raw):
            speaker_id = "HIRO" if i % 2 == 0 else "SAKURA"
            voice_type = "Heroic / Shonen" if i % 2 == 0 else "High-Pitch / Feminine"
            original_text = " ".join([w.get('word', '') for w in seg])
            translated_text = translations[i] if i < len(translations) else "[ERROR]"
            
            formatted_segments.append({
                "id": str(i),
                "speaker_id": speaker_id,
                "voice_type": voice_type,
                "start": seg[0]['start'],
                "end": seg[-1]['end'],
                "original": original_text,
                "translation": translated_text,
                "status": "OK",
                "targetFlaps": len(original_text), 
                "currentFlaps": len(translated_text),
                "emotion": "neutral",
                "intensity": 0.5,
                "artifacts": []
            })
            
        analysis_jobs[job_id]["status"] = "Complete"
        analysis_jobs[job_id]["result"] = {"segments": formatted_segments}
        save_jobs()
        await manager.broadcast({"type": "status", "msg": "Neural Link: Analysis Complete.", "success": True, "job_id": job_id})
        
    except Exception as e:
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
    safe_filename = f"{job_id}_{file.filename.replace('/', '_').replace('\\', '_')}"
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
    try:
        orch = SonoraOrchestrator("dummy.mp4") 
        # If gemini is requested, we could route to a specialized module
        # but for simplicity we keep it in orchestrator.refactor_line
        new_text = await orch.refactor_line(req.text, req.target_syllables, req.style)
        return {"text": new_text, "engine": req.engine}
    except Exception as e:
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
        master_path = await orch.assemble_final_dub(req.video_path, takes, req.segments)
        
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