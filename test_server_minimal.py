#!/usr/bin/env python3
"""
Minimal test server to verify FastAPI and Streamlit setup.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Sonora Test API",
    description="Minimal test server",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Sonora API is running!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sonora-api"}

if __name__ == "__main__":
    print("Starting minimal test server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")










