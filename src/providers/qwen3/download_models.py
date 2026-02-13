import os
from huggingface_hub import snapshot_download

def download_models():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    models = [
        "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
    ]
    
    print(f"Downloading models to {models_dir}...")
    
    for model_id in models:
        try:
            print(f"Downloading {model_id}...")
            snapshot_download(
                repo_id=model_id, 
                local_dir=os.path.join(models_dir, model_id.split("/")[-1]),
                local_dir_use_symlinks=False
            )
            print(f"Successfully downloaded {model_id}")
        except Exception as e:
            print(f"Failed to download {model_id}: {e}")

if __name__ == "__main__":
    download_models()
