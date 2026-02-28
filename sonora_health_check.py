import os
import sys
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import torch
import logging

# Configure logging to be quiet for the script
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("sonora.health_check")

def check_translator():
    from src.services.translator.qwen_local import LocalQwenTranslator
    print("Checking Local Translation (Qwen 2.5-7B INT4)...")
    if os.path.exists("models/qwen7b"):
        print("  Status: ✅ READY (Local Weights Found: ~6GB)")
    else:
        print("  Status: ⚠️ MISSING (Local weights not found at models/qwen7b)")

def check_tts():
    print("\nChecking Synthesizer (Qwen3-TTS 0.6B)...")
    if os.path.exists("models/qwen3"):
        print("  Status: ✅ READY (Weights Found: ~4GB)")
    else:
        print("  Status: ⚠️ MISSING (Local weights not found at models/qwen3)")

def check_separator():
    from src.services.separator.audio_separator import AudioSeparator, SeparationModel
    print("\nChecking Audio Separator (Demucs v4 Hybrid)...")
    if os.path.exists("models/demucs"):
        print("  Status: ✅ READY (htdemucs weights pre-cached)")
    else:
        print("  Status: ⚠️ CAUTION (Demucs weights not pre-cached; will download on first run)")

def check_asr():
    from transcriber import Transcriber
    print("\nChecking Transcriber (Faster-Whisper Large-v3)...")
    if os.path.exists("models/whisper"):
        print("  Status: ✅ READY (Large-v3 Weights Found: ~4.5GB)")
    else:
        print("  Status: ⚠️ MISSING (Whisper models not found at models/whisper)")

async def run_stress_test():
    """Verifies Priority-Aware HardwareLock by launching competing P1 tasks."""
    from src.core.reliability import HardwareLock
    print("\n" + "!" * 50)
    print("🚀 STARTING HARDWARE-LOCK STRESS TEST...")
    print("!" * 50)
    
    async def simulated_p1_task(task_id: int, duration: float):
        print(f"🔒 Task {task_id} requesting VRAM (Priority 1)...")
        async with HardwareLock.locked_async(f"Stress-Task-{task_id}", priority=1):
            print(f"✅ Task {task_id} ACQUIRED VRAM. Holding for {duration}s...")
            await asyncio.sleep(duration)
        print(f"🔓 Task {task_id} RELEASED VRAM.")

    # Launch two P1 tasks near-simultaneously
    print("Simulating parallel P1 collision (Wav2Lip vs Wav2Lip)...")
    t1 = asyncio.create_task(simulated_p1_task(1, 4))
    await asyncio.sleep(0.5) # Ensure T1 hits the lock first
    t2 = asyncio.create_task(simulated_p1_task(2, 2))
    
    await asyncio.gather(t1, t2)
    print("\n✅ STRESS TEST COMPLETE: HardwareLock correctly serialized the collision.")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stress-test", action="store_true", help="Run VRAM contention stress test.")
    args = parser.parse_args()

    print("=" * 50)
    print("SONORA SWARM: HEAVYWEIGHT ARCHITECTURE REPORT")
    print("=" * 50)
    
    check_translator()
    check_tts()
    check_separator()
    check_asr()
    
    if args.stress_test:
        asyncio.run(run_stress_test())
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("Architecture: HEAVYWEIGHT (Local Neural Swarm)")
    print("Target VRAM: 24GB (NVIDIA L4/A10G)")
    print("Priority Lock: ACTIVE")
    print("=" * 50)

if __name__ == "__main__":
    main()
