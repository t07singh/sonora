import os
import subprocess
import sys
from openai import OpenAI
from elevenlabs.client import ElevenLabs

def test_ffmpeg():
    print("🔍 [1/3] Testing FFmpeg Engine...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg Engine: OK (Globally Accessible)")
        return True
    except Exception as e:
        print(f"❌ FFmpeg Engine: FAILED (Ensure FFmpeg is in your system PATH)\nError: {e}")
        return False

def test_openai():
    print("\n🔍 [2/3] Testing OpenAI API (Transcription Bridge)...")
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI Bridge: FAILED (OPENAI_API_KEY not found in environment)")
            return False
        
        client = OpenAI(api_key=api_key)
        # Tiny test request
        client.models.list()
        print("✅ OpenAI Bridge: OK (Authenticated)")
        return True
    except Exception as e:
        print(f"❌ OpenAI Bridge: FAILED\nError: {e}")
        return False

def test_elevenlabs():
    print("\n🔍 [3/3] Testing ElevenLabs API (Voice Surgery)...")
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ ElevenLabs Surgery: FAILED (ELEVENLABS_API_KEY not found in environment)")
            return False
            
        client = ElevenLabs(api_key=api_key)
        # List models to verify authentication
        client.models.get_all()
        print("✅ ElevenLabs Surgery: OK (Authenticated)")
        return True
    except Exception as e:
        print(f"❌ ElevenLabs Surgery: FAILED\nError: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*40)
    print("🚀 SONORA STUDIO SYSTEM DIAGNOSTICS")
    print("="*40 + "\n")
    
    results = [test_ffmpeg(), test_openai(), test_elevenlabs()]
    
    print("\n" + "="*40)
    if all(results):
        print("🏁 DIAGNOSTICS COMPLETE: ALL SYSTEMS GO")
        print("Run 'streamlit run sonora/app.py' to launch.")
    else:
        print("⚠️  DIAGNOSTICS COMPLETE: ISSUES DETECTED")
        print("Please resolve the failures above before dubbing.")
    print("="*40 + "\n")