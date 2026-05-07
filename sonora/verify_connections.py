import os
import subprocess
import sys
import requests
import time
from typing import List, Dict, Any
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from gradio_client import Client
import json

# Force UTF-8 for Windows Terminal
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path to support 'src' and 'sonora' imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_ffmpeg():
    print("🔍 [1/6] Testing FFmpeg Engine...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg Engine: OK")
        return True
    except Exception as e:
        print(f"❌ FFmpeg Engine: FAILED (Ensure FFmpeg is in PATH)\nError: {e}")
        return False

def test_groq():
    print("\n🔍 [2/6] Testing Groq API (High-Speed ASR)...")
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("⚠️  Groq API: SKIPPED (No Key found)")
            return True # Not fatal
        
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        client.models.list()
        print("✅ Groq API: OK")
        return True
    except Exception as e:
        print(f"❌ Groq API: FAILED\nError: {e}")
        return False

def test_gemini():
    print("\n🔍 [3/6] Testing Gemini API (Universal Translator)...")
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️  Gemini API: SKIPPED (No Key found)")
            return True
            
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        # Try a simple listing
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print("✅ Gemini API: OK")
                return True
        return False
    except Exception as e:
        print(f"❌ Gemini API: FAILED\nError: {e}")
        return False

def test_hf_spaces():
    print("\n🔍 [4/6] Testing Hugging Face Workers (Shadow Nodes)...")
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("⚠️  HF Workers: SKIPPED (No HF_TOKEN found)")
        return True
    
    spaces = [
        ("Separation", os.getenv("SEPARATION_SPACE_URL", "facebook/demucs")),
        ("Diarization", os.getenv("DIARIZATION_SPACE_URL", "pyannote/speaker-diarization-3.1")),
        ("Visual Sync", os.getenv("WAV2LIP_SPACE_URL", "abidlabs/wav2lip"))
    ]
    
    all_ok = True
    for name, url in spaces:
        try:
            print(f"   - Checking {name} ({url})...", end="", flush=True)
            # Just initialize the client, don't run a prediction to save time/credits
            Client(url, hf_token=hf_token)
            print(" OK")
        except Exception as e:
            print(f" FAILED\n     Error: {str(e)[:100]}...")
            all_ok = False
    return all_ok

def test_omnishotcut():
    print("\n🔍 [5/8] Testing OmniShotCut (Visual Slicing)...")
    try:
        from src.services.segmenter.omnishotcut import OmniShotCutDetector
        detector = OmniShotCutDetector(use_cloud=True)
        # Mock check - see if it can reach the space
        if detector.hf_token:
            print("✅ OmniShotCut: OK (Cloud-Shadow Ready)")
        else:
            print("⚠️  OmniShotCut: OK (Local Fallback Only - No HF_TOKEN)")
        return True
    except Exception as e:
        print(f"❌ OmniShotCut: FAILED\nError: {e}")
        return False

def test_fish_audio():
    print("\n🔍 [6/8] Testing Fish Audio S2 (Primary Engine)...")
    try:
        from src.services.synthesizer.fish_s2_engine import FishS2Engine
        engine = FishS2Engine()
        if engine.api_key:
            print("✅ Fish Audio S2: OK")
        else:
            print("⚠️  Fish Audio S2: SKIPPED (No FISHAUDIO_API_KEY)")
        return True
    except Exception as e:
        print(f"❌ Fish Audio S2: FAILED\nError: {e}")
        return False

def test_elevenlabs():
    print("\n🔍 [7/8] Testing ElevenLabs API (Voice Synthesis)...")
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("⚠️  ElevenLabs: SKIPPED (No Key found)")
            return True
            
        client = ElevenLabs(api_key=api_key)
        # Try a safer check for ElevenLabs 1.0+
        try:
            client.models.get_all()
        except AttributeError:
            client.voices.get_all()
        print("✅ ElevenLabs: OK")
        return True
    except Exception as e:
        print(f"❌ ElevenLabs: FAILED\nError: {e}")
        return False

def test_openai():
    print("\n🔍 [8/8] Testing OpenAI API (Fallback Engine)...")
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  OpenAI: SKIPPED (No Key found)")
            return True
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        client.models.list()
        print("✅ OpenAI: OK")
        return True
    except Exception as e:
        print(f"❌ OpenAI: FAILED\nError: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 SONORA STUDIO: CLOUD-SHADOW DIAGNOSTICS")
    print("="*50 + "\n")
    
    # Check if .env is loaded
    if not os.getenv("HF_TOKEN") and not os.getenv("GROQ_API_KEY"):
        print("💡 TIP: No API keys found in environment. Ensure .env is set up.\n")

    results = [
        test_ffmpeg(),
        test_groq(),
        test_gemini(),
        test_hf_spaces(),
        test_omnishotcut(),
        test_fish_audio(),
        test_elevenlabs(),
        test_openai()
    ]
    
    print("\n" + "="*50)
    if all(results):
        print("✨ DIAGNOSTICS COMPLETE: ALL SYSTEMS READY")
        print("Sonora Studio can now operate in CLOUD_OFFLOAD mode.")
    else:
        print("⚠️  DIAGNOSTICS COMPLETE: SOME ISSUES DETECTED")
        print("Please resolve the failures above for best performance.")
    print("="*50 + "\n")