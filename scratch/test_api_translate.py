import requests
import json
import time

API_BASE = "http://localhost:8000"
HEADERS = {"X-Sonora-Key": "admin123"}

def test_translate():
    payload = {
        "segments": [
            {"text": "こんにちは", "start": 0, "end": 1, "original": "こんにちは"},
            {"text": "元気ですか", "start": 1, "end": 2, "original": "元気ですか"}
        ],
        "style": "Anime"
    }
    
    print(f"Sending translation request to {API_BASE}/api/pipeline/translate...")
    try:
        r = requests.post(f"{API_BASE}/api/pipeline/translate", json=payload, headers=HEADERS, timeout=60)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            print("Response: [PROTECTED KANA/UTF8 CONTENT]")
            # Verify format only
            data = r.json()
            if "segments" in data:
                print(f"Success: Received {len(data['segments'])} segments")
                for i, s in enumerate(data['segments']):
                     print(f"Segment {i}: translation is {type(s.get('translation')).__name__}")
        else:
            print("Error:", r.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_translate()
