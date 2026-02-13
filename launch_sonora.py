
import os
import sys
import time
import subprocess
import requests
from pathlib import Path

def check_swarm_health():
    print("--- Sonora Swarm Health Audit ---")
    services = [("Separator", 8000), ("Transcriber", 8001), ("Synthesizer", 8002)]
    for name, port in services:
        try:
            res = requests.get(f"http://localhost:{port}/health", timeout=1)
            print(f"[OK] {name} Node: ONLINE")
        except:
            print(f"[!!] {name} Node: OFFLINE")

def bootstrap():
    # Ensure Shared Volume
    SHARED_DATA = Path("/tmp/sonora")
    SHARED_DATA.mkdir(parents=True, exist_ok=True)
    for folder in ["uploads", "takes", "stems"]:
        (SHARED_DATA / folder).mkdir(exist_ok=True)
        os.chmod(SHARED_DATA / folder, 0o777)
    
    print("✅ Shared Volume Initialized: /tmp/sonora")
    
    # Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ Audio Engine: FFmpeg Found")
    except:
        print("❌ Critical Error: FFmpeg NOT FOUND.")
        sys.exit(1)

    print("\n🚀 Ready to Launch Swarm. Run 'SHIP_SONORA.bat' to orchestrate Docker nodes.")

if __name__ == "__main__":
    bootstrap()
