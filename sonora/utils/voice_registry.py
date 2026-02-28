import os
import json
import numpy as np
from pathlib import Path
import logging
import soundfile as sf

logger = logging.getLogger("sonora.voice_registry")

# Root directory for production assets. Configurable via environment variable for persistent storage.
VOICE_DIR = Path(os.getenv("REGISTRY_PATH", "sonora/data/voices"))

def extract_embedding_from_audio(audio_path: str):
    """
    Simulates high-fidelity embedding extraction from a source sample.
    In production, this would call the VibeVoice encoder node.
    """
    try:
        data, sr = sf.read(audio_path)
        # Mocking a 256-dim embedding for the demo
        # Seeded by the audio data sum to ensure deterministic 'voice identity'
        np.random.seed(int(np.abs(data.sum() * 1000) % 2**32))
        embedding = np.random.randn(256).astype(np.float32)
        return embedding
    except Exception as e:
        logger.error(f"EMBED_EXTRACTOR: Failed to read {audio_path}: {e}")
        return None

def save_character_voice(character_name: str, source_input: any, metadata: dict = None):
    """
    Saves a high-fidelity speaker embedding to the production registry.
    Can take either a direct embedding or a path to a source audio file.
    """
    os.makedirs(VOICE_DIR, exist_ok=True)
    
    embedding = None
    if isinstance(source_input, (str, Path)):
        logger.info(f"REGISTRY: Extracting profile from {source_input}...")
        embedding = extract_embedding_from_audio(str(source_input))
    else:
        embedding = source_input

    if embedding is None:
        return False
        
    # Convert numpy array to list for JSON serialization
    emb_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
    
    profile_data = {
        "character_name": character_name.upper(),
        "embedding": emb_list,
        "metadata": metadata or {},
        "version": "v1.0-PROD",
        "digitized_at": str(Path(source_input).name) if isinstance(source_input, (str, Path)) else "direct_memory"
    }
    
    file_path = VOICE_DIR / f"{character_name.lower().replace(' ', '_')}.json"
    
    try:
        with open(file_path, "w") as f:
            json.dump(profile_data, f, indent=2)
        logger.info(f"REGISTRY: Saved production asset for '{character_name}' at {file_path}")
        return True
    except Exception as e:
        logger.error(f"REGISTRY: Failed to save voice profile: {e}")
        return False

def get_character_voice(character_name: str):
    """
    Retrieves a saved speaker embedding from the registry.
    """
    file_path = VOICE_DIR / f"{character_name.lower().replace(' ', '_')}.json"
    
    if not file_path.exists():
        logger.warning(f"REGISTRY: No profile found for '{character_name}'. Check path: {file_path}")
        return None
        
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return np.array(data["embedding"])
    except Exception as e:
        logger.error(f"REGISTRY: Error loading profile '{character_name}': {e}")
        return None

def list_registered_characters():
    """Returns a list of all character profiles currently in the registry."""
    if not VOICE_DIR.exists():
        return []
    return [f.stem.replace('_', ' ').upper() for f in VOICE_DIR.glob("*.json")]
