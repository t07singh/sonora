#!/usr/bin/env python3
"""
Verification script for the CPU-Hardened Sonora Swarm.
Tests the "Plumbing Handshake" by simulating the UI workflow.
"""

import requests
import json
import time
import os
from pathlib import Path

SHARED_DATA = Path("./shared_data")
TRANSCRIBER_URL = "http://localhost:8001"
SEPARATOR_URL = "http://localhost:8000"
SYNTHESIZER_URL = "http://localhost:8002"
UI_URL = "http://localhost:8501"

def test_service_health(service_name, url):
    """Test if a service is healthy and responding."""
    print(f"\n[*] Testing {service_name}...")
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            device = data.get("device", "unknown")
            print(f"[OK] {service_name} is healthy (Device: {device})")
            return True
        else:
            print(f"[FAIL] {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] {service_name} is not reachable: {e}")
        return False

def test_shared_volume():
    """Test if the shared volume is accessible."""
    print(f"\n[*] Testing shared volume at {SHARED_DATA}...")
    SHARED_DATA.mkdir(exist_ok=True)
    
    test_file = SHARED_DATA / "test_handshake.txt"
    test_file.write_text("CPU-Hardened Swarm Test")
    
    if test_file.exists():
        print(f"[OK] Shared volume is writable")
        test_file.unlink()
        return True
    else:
        print(f"[FAIL] Shared volume is not accessible")
        return False

def test_transcriber_handshake():
    """Test the transcriber processing handshake."""
    print(f"\n[*] Testing Transcriber handshake...")
    
    # Create a dummy audio file
    dummy_audio = SHARED_DATA / "test_audio.wav"
    dummy_audio.write_bytes(b"RIFF" + b"\x00" * 100)  # Minimal WAV header
    
    try:
        payload = {"filename": "test_audio.wav"}
        response = requests.post(f"{TRANSCRIBER_URL}/process", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Transcriber processed successfully")
            print(f"   Status: {result.get('status')}")
            print(f"   Text: {result.get('text', 'N/A')[:50]}...")
            
            # Check if transcript.json was created
            transcript_file = SHARED_DATA / "transcript.json"
            if transcript_file.exists():
                print(f"[OK] Transcript file created in shared volume")
                transcript_file.unlink()
            
            dummy_audio.unlink()
            return True
        else:
            print(f"[FAIL] Transcriber returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Transcriber request failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("CPU-Hardened Sonora Swarm Verification")
    print("=" * 60)
    
    results = {
        "Shared Volume": test_shared_volume(),
        "Transcriber": test_service_health("Transcriber", TRANSCRIBER_URL),
        "Separator": test_service_health("Separator", SEPARATOR_URL),
        "Synthesizer": test_service_health("Synthesizer", SYNTHESIZER_URL),
    }
    
    # Only test handshake if transcriber is healthy
    if results["Transcriber"]:
        results["Transcriber Handshake"] = test_transcriber_handshake()
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test:.<40} {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All tests passed! The Sonora Swarm is ready.")
        print("   Next: Open http://localhost:8501 to access the Cockpit UI")
    else:
        print("WARNING: Some tests failed. Check the logs above for details.")
        print("   Ensure all services are running: docker compose up --build")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
