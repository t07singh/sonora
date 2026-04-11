import os
from huggingface_hub import snapshot_download
import torch

def download_qwen3():
    print("📥 [1/5] Downloading Qwen3-TTS (0.6B) weights...")
    repo_id = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
    local_dir = "models/qwen3"
    os.makedirs(local_dir, exist_ok=True)
    snapshot_download(repo_id=repo_id, local_dir=local_dir, local_dir_use_symlinks=False)
    print("✅ Qwen3 weights ready.")

def download_whisper_large():
    print("📥 [2/5] Downloading Faster-Whisper (Large-v3) weights...")
    from faster_whisper import WhisperModel
    local_dir = "models/whisper"
    os.makedirs(local_dir, exist_ok=True)
    # This will trigger an optimized CTranslate2 download
    WhisperModel("large-v3", device="cpu", download_root=local_dir)
    print("✅ Whisper Large-v3 weights ready.")

def download_qwen7b():
    print("📥 [3/5] Downloading Qwen2.5-7B-Instruct (INT4) weights...")
    # Using GPTQ version for extreme VRAM efficiency (fits in ~6GB)
    repo_id = "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"
    local_dir = "models/qwen7b"
    os.makedirs(local_dir, exist_ok=True)
    snapshot_download(repo_id=repo_id, local_dir=local_dir, local_dir_use_symlinks=False)
    print("✅ Qwen 7B INT4 weights ready.")

def download_wav2lip_hq():
    print("📥 [4/5] Downloading Wav2Lip-HQ weights...")
    # Standard HF mirrors for Wav2Lip weights
    repo_id = "camenduru/Wav2Lip"
    local_dir = "models/wav2lip"
    os.makedirs(local_dir, exist_ok=True)
    snapshot_download(repo_id=repo_id, local_dir=local_dir, local_dir_use_symlinks=False)
    print("✅ Wav2Lip-HQ weights ready.")

def download_demucs_v4():
    print("📥 [5/5] Downloading Demucs v4 (htdemucs) weights...")
    import demucs.api
    local_dir = "models/demucs"
    os.makedirs(local_dir, exist_ok=True)
    # This will trigger a download of the htdemucs model
    # We set the repo to ensure it knows where to look/store
    separator = demucs.api.Separator(model="htdemucs", device="cpu")
    print("✅ Demucs v4 ready.")

def create_sample_voices():
    print("👤 Initializing Sample Character Registry...")
    from sonora.utils.voice_registry import save_character_voice
    import numpy as np
    
    # Create a few default characters so the UI isn't empty
    characters = [
        ("Alice [EN]", "Calm, Professional"),
        ("Bob [JP]", "Energetic, Youthful"),
        ("Charlie [ES]", "Deep, Narrative")
    ]
    
    for name, desc in characters:
        # Mock embedding for default library
        mock_embedding = np.random.randn(256).astype(np.float32)
        save_character_voice(name, mock_embedding, metadata={"description": desc})
    print("✅ Sample voices initialized.")

def main():
    cloud_offload = os.getenv("CLOUD_OFFLOAD", "false").lower() == "true"
    
    os.makedirs("models", exist_ok=True)
    
    if cloud_offload:
        print("\n☁️ CLOUD OFFLOAD ACTIVE: Bypassing heavy local GPU weights (Qwen3, Whisper-v3, Demucs).")
        # We only need the sample voices so the UI DB initializes
        create_sample_voices()
        print("\n📦 BUNDLE SCRIPT COMPLETE (Lightweight Cloud Mode).")
    else:
        download_qwen3()
        download_whisper_large()
        download_qwen7b()
        download_wav2lip_hq()
        download_demucs_v4()
        create_sample_voices()
        print("\n📦 ALL HEAVYWEIGHT MODEL WEIGHTS BUNDLED SUCCESSFULLY (~18GB).")

if __name__ == "__main__":
    main()
