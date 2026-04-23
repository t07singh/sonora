import requests
import time
import os
from pathlib import Path
import json

API_BASE = "http://127.0.0.1:8000"
HEADERS = {"X-Sonora-Key": "admin123"}

def test_segmentation():
    print("Finding test media file...")
    temp_dir = Path("sonora/data/temp")
    
    test_files = []
    if temp_dir.exists():
        test_files = [f for f in temp_dir.glob("*") if f.suffix.lower() in ['.mp4', '.mp3', '.wav']]
    
    if not test_files:
        print("No test files found in sonora/data/temp. Creating a dummy file...")
        os.makedirs("sonora/data/temp", exist_ok=True)
        # Create a small dummy text file matching extension
        dummy_path = Path("sonora/data/temp/dummy_test.mp3")
        with open(dummy_path, "wb") as f:
            f.write(b"0" * 1024)
        file_to_test = "dummy_test.mp3"
    else:
        file_to_test = test_files[0].name
        print(f"Found test file: {file_to_test}")

    print(f"\nSending request to /api/pipeline/segment with {file_to_test}...")
    try:
        response = requests.post(f"{API_BASE}/api/pipeline/segment", json={"video_path": file_to_test}, headers=HEADERS)
        if response.status_code != 200:
            print(f"FAILED: API returned {response.status_code}")
            print(response.text)
            return

        job_id = response.json().get("job_id")
        print(f"Job queued successfully. Job ID: {job_id}")
        
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    print("\nPolling for job completion...")
    while True:
        try:
            job_res = requests.get(f"{API_BASE}/api/job/{job_id}", headers=HEADERS).json()
            status = job_res.get("status")
            
            print(f"Status: {status}")
            
            if status == "Complete":
                segments = job_res.get("result", {}).get("segments", [])
                print(f"\nSUCCESS: Processing complete! Found {len(segments)} segments.")
                print("First segment sample:")
                if segments:
                    print(json.dumps(segments[0], indent=2))
                break
            elif status == "Error":
                print(f"\nFAILED: Backend Analysis Error!")
                print(job_res.get("error"))
                break
                
            time.sleep(3)
        except Exception as e:
            print(f"Polling Exception: {e}")
            break

if __name__ == "__main__":
    test_segmentation()
