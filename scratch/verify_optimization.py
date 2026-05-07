import requests
import time
import os
from pathlib import Path
import json

API_BASE = "http://127.0.0.1:8000"
HEADERS = {"X-Sonora-Key": "admin123"}

def verify_mode(mode_name, payload):
    print(f"\n--- Testing {mode_name} ---")
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE}/api/pipeline/segment", json=payload, headers=HEADERS)
        if response.status_code != 200:
            print(f"FAILED: API returned {response.status_code}")
            print(response.text)
            return False

        job_id = response.json().get("job_id")
        print(f"Job queued. ID: {job_id}")
        
        while True:
            job_res = requests.get(f"{API_BASE}/api/job/{job_id}", headers=HEADERS).json()
            status = job_res.get("status")
            
            if status == "Complete":
                end_time = time.time()
                segments = job_res.get("result", {}).get("segments", [])
                print(f"SUCCESS: {mode_name} complete in {end_time - start_time:.2f}s")
                print(f"Segments found: {len(segments)}")
                if segments:
                    print(f"First segment text: {segments[0].get('text')}")
                return True
            elif status == "Error":
                print(f"FAILED: {mode_name} error: {job_res.get('error')}")
                return False
            
            time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    # 1. Test Bypass Mode (on the dummy video file)
    verify_mode("BYPASS MODE", {
        "video_path": "test_video.mp4",
        "bypass": True
    })

    # 2. Test Turbo Mode (on the real audio file)
    verify_mode("TURBO MODE", {
        "video_path": "test_audio.mp3",
        "turbo": True,
        "mode": "fast"
    })

if __name__ == "__main__":
    main()
