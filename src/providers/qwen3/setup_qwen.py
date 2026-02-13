import subprocess
import sys
import os

def install(package, extra_args=None):
    cmd = [sys.executable, "-m", "pip", "install", package]
    if extra_args:
        cmd.extend(extra_args)
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

def setup():
    print("=== Qwen3 Environment Setup ===")
    
    # 1. Install Torch with CUDA 12.1
    print("\n[1/3] Installing PyTorch with CUDA 12.1 support...")
    try:
        install("torch", ["torchaudio", "--index-url", "https://download.pytorch.org/whl/cu121"])
    except subprocess.CalledProcessError:
        print("Warning: Failed to install CUDA version of PyTorch. Falling back to CPU version...")
        install("torch", ["torchaudio"])

    # 2. Install Qwen dependencies
    print("\n[2/3] Installing Qwen dependencies...")
    dependencies = [
        "transformers",
        "accelerate", 
        "scipy",
        "soundfile",
        "fastapi",
        "uvicorn",
        "python-multipart"
    ]
    for dep in dependencies:
        try:
            install(dep)
        except subprocess.CalledProcessError as e:
            print(f"Error installing {dep}: {e}")

    # 3. Flash Attention (Optional)
    print("\n[3/3] Attempting to install Flash Attention (Optional)...")
    try:
        # Note: vllm-omni and qwen3-tts would be installed here if they are on PyPI or local wheels
        # For this implementation, we assume they are reachable via pip or simulated by the service wrapper
        install("vllm-omni") 
    except subprocess.CalledProcessError:
        print("Note: vllm-omni installation failed. The Qwen3 service will fallback to standard attention mechanisms.")

    print("\n=== Setup Complete ===")

if __name__ == "__main__":
    setup()
