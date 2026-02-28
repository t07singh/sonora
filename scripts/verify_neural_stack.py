import os
import requests
import torch
import time
import hashlib
from typing import Dict

def check_file_health(path: str, expected_min_gb: float = 0.0) -> bool:
    if not os.path.exists(path):
        print(f"❌ MISSING: {path}")
        return False
    
    size_gb = os.path.getsize(path) / (1024**3)
    if size_gb < expected_min_gb:
        print(f"⚠️ UNDERSIZED: {path} ({size_gb:.2f} GB, expected > {expected_min_gb} GB)")
        return False
    
    print(f"✅ HEALTHY: {path} ({size_gb:.2f} GB)")
    return True

def verify_swarm_connectivity() -> Dict[str, str]:
    endpoints = {
        "API": "http://sonora-api:8000/health",
        "Transcriber": "http://sonora-transcriber:8001/health",
        "Synthesizer": "http://sonora-synthesizer:8002/health",
        "Separator": "http://sonora-separator:8000/health"
    }
    
    results = {}
    for name, url in endpoints.items():
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                results[name] = "ONLINE"
                print(f"🛰️ {name}: ONLINE")
            else:
                results[name] = f"ERROR ({r.status_code})"
                print(f"🛰️ {name}: ERROR ({r.status_code})")
        except Exception as e:
            results[name] = "UNREACHABLE"
            print(f"🛰️ {name}: UNREACHABLE")
    return results

def main():
    print("🎬 Starting Sonora Neural Handshake Diagnostic...")
    print("-" * 50)
    
    # 1. Hardware Check
    print("💻 [1/3] Checking Hardware Acceleration...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device Node: {device.upper()}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    
    print("\n📦 [2/3] Auditing 18GB AI Stack Persistence...")
    # Check key model folders
    models = {
        "models/qwen3": 0.5,
        "models/whisper": 1.5,
        "models/qwen7b": 4.5,
        "models/wav2lip": 0.1,
        "models/demucs": 0.1
    }
    
    all_models_ok = True
    for path, min_size in models.items():
        if not os.path.isdir(path):
            print(f"❌ MISSING DIRECTORY: {path}")
            all_models_ok = False
        else:
            print(f"✅ FOLDER DETECTED: {path}")

    print("\n🛰️ [3/3] Verifying Swarm Connectivity...")
    connectivity = verify_swarm_connectivity()
    
    print("-" * 50)
    if all_models_ok and all(s == "ONLINE" for s in connectivity.values()):
        print("✅ NEURAL HANDSHAKE SUCCESSFUL: Cluster is ready for High-Res Dubbing.")
    else:
        print("❌ NEURAL HANDSHAKE FAILED: Please check the missing components above.")

if __name__ == "__main__":
    main()
