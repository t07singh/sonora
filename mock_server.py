from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, Response
import uvicorn
import time
import os
import random

app = FastAPI(title="Sonora Mock Backend")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "sonora-mock"}

@app.get("/api/metrics")
async def metrics():
    return {
        "total_requests": random.randint(100, 500),
        "total_errors": random.randint(0, 5),
        "uptime_minutes": 120.5,
        "system": {"cpu_percent": 12.5, "memory_mb": 512},
        "latency": {"avg_latency_sec": 0.2},
        "audio": {"audio_files_processed": 45},
        "cache": {"cache_hit_rate_percent": 85.0}
    }

@app.get("/api/cache/stats")
async def cache_stats():
    return {
        "memory_items": 50,
        "disk_items": 120,
        "hit_rate": 0.85,
        "cache_size_mb": 24.5,
        "expired_entries": 10,
        "total_requests": 200,
        "uptime_minutes": 120.5
    }

@app.get("/api/analytics")
async def analytics():
    return {
        "system": {"cpu_percent": 15},
        "endpoints": {"/dub": {"requests": 50, "avg_latency": 1.2}}
    }

@app.post("/api/dub")
async def dub_audio(file: UploadFile = File(...)):
    # Simulate processing delay
    time.sleep(2)
    
    # Return the same audio as "dubbed" (echo)
    # We read into memory
    content = await file.read()
    return Response(content=content, media_type="audio/wav")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
