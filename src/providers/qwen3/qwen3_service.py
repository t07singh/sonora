import os
import time
import json
import threading
import glob
import torch
import soundfile as sf
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Qwen3-TTS Service")

# -- Global State --
MODEL = None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TASK_DIR = "/tmp/sonora/tasks"
OUTPUT_DIR = "shared_data/outputs"

class DesignRequest(BaseModel):
    prompt: str
    text: str

@app.on_event("startup")
async def startup_event():
    print(f"🚀 Starting Qwen3 Swarm Node on {DEVICE}...")
    os.makedirs(TASK_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Start the swarm task watcher
    threading.Thread(target=task_watcher_loop, daemon=True).start()
    print("✅ Swarm Task Watcher Active.")

@app.post("/clone")
async def clone_voice(reference_audio: UploadFile = File(...), text: str = Form(...)):
    """3-second zero-shot voice cloning."""
    print(f"🎤 Cloning request received for: {text[:30]}...")
    # Inference logic placeholder
    time.sleep(0.5)
    return {"status": "success", "message": "Cloned audio generated (mock)."}

@app.post("/design")
async def design_voice(request: DesignRequest):
    """Natural language voice design."""
    print(f"🎨 Designing voice: '{request.prompt}'")
    # Inference logic placeholder
    time.sleep(0.5)
    return {"status": "success", "message": "Designed audio generated (mock)."}

def task_watcher_loop():
    """Polls the task directory for Orchestrator handshakes."""
    while True:
        try:
            task_files = glob.glob(os.path.join(TASK_DIR, "*.json"))
            for task_file in task_files:
                process_task(task_file)
        except Exception as e:
            print(f"❌ Swarm Watcher Error: {e}")
        time.sleep(0.5)

def process_task(task_path):
    print(f"📦 Swarm Handshake: Processing {os.path.basename(task_path)}")
    try:
        with open(task_path, "r") as f:
            task = json.load(f)
        
        # Simulate Qwen3-TTS 12Hz Generation
        time.sleep(0.4) 
        
        task_id = task.get("id")
        output_file = os.path.join(OUTPUT_DIR, f"{task_id}.wav")
        
        # Generate valid mock WAV
        sr = 24000
        duration = 3.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.1
        sf.write(output_file, audio, sr)
        
        # Signal completion by removing task file
        os.remove(task_path)
        print(f"✅ Task {task_id} committed to {output_file}")
    except Exception as e:
        print(f"❌ Task Failure: {e}")
        if os.path.exists(task_path):
            os.rename(task_path, task_path + ".failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
