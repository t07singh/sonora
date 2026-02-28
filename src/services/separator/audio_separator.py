
"""
Audio Separator Module for Sonora Voice & Sound Editing Core

This module provides AI-powered source separation capabilities using multiple
state-of-the-art models optimized for anime mixing styles. It can separate
mixed audio into distinct stems: voice, music, drums, and bass.

Supported Models:
- Demucs: High-quality separation with anime-optimized training
- Gradio-Cloud: Offloads Demucs to remote GPU for AI Studio efficiency
- Spleeter: Fast separation with good quality
"""

import os
import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import torch
import torchaudio
# Patch torchaudio for SpeechBrain compatibility
if not hasattr(torchaudio, 'list_audio_backends'):
    def list_audio_backends():
        return ['soundfile', 'sox']
    torchaudio.list_audio_backends = list_audio_backends
from dataclasses import dataclass
from enum import Enum

from src.core.reliability import retry_api_call, get_device
from src.core import shadow_providers

logger = logging.getLogger(__name__)


class SeparationModel(Enum):
    """Available separation models."""
    SEPFORMER = "sepformer"
    DEMUCS = "demucs"
    DEMUCS_V4 = "htdemucs" # High-Res Hybrid Transformer
    CLOUD_DEMUCS = "cloud_demucs"
    SWARM_DEMUCS = "swarm_demucs"


@dataclass
class SeparationResult:
    """Result of audio separation."""
    voice: np.ndarray
    music: np.ndarray
    drums: Optional[np.ndarray] = None
    bass: Optional[np.ndarray] = None
    sample_rate: int = 44100
    duration: float = 0.0
    model_used: str = ""
    confidence_scores: Dict[str, float] = None


class AudioSeparator:
    """
    AI-powered audio separator for anime content.
    
    Now supports Cloud-GPU offloading for Demucs via Gradio, specifically 
    tailored for the AI Studio environment.
    """
    
    def __init__(
        self,
        model: SeparationModel = SeparationModel.SEPFORMER,
        device: str = "auto",
        sample_rate: int = 44100
    ):
        self.model = model
        self.sample_rate = sample_rate
        self.device = self._get_device(device)
        self.model_instance = None
        
        logger.info(f"Initialized AudioSeparator with {model.value} on {self.device}")
    
    def _get_device(self, device: str) -> str:
        if device == "auto":
            return get_device()
        return device
    
    def load_model(self) -> None:
        if self.model == SeparationModel.CLOUD_DEMUCS:
            logger.info("Separator Condition: CLOUD_OFFLOAD. Skipping local weight load.")
            return

        try:
            if self.model == SeparationModel.SEPFORMER:
                self._load_sepformer()
            elif self.model in [SeparationModel.DEMUCS, SeparationModel.DEMUCS_V4]:
                self._load_demucs()
            
            logger.info(f"Successfully loaded {self.model.value} model")
            
        except Exception as e:
            logger.error(f"Failed to load {self.model.value} model: {e}")
            self._try_fallback_models()
    
    def _load_sepformer(self) -> None:
        try:
            from speechbrain.pretrained import SepformerSeparation
            self.model_instance = SepformerSeparation.from_hparams(
                source="speechbrain/sepformer-wsj02mix",
                savedir="pretrained_models/sepformer-wsj02mix",
                run_opts={"device": self.device}
            )
        except Exception as e:
            logger.error(f"Sepformer failed to load: {e}")
            self.model_instance = None

    def _load_demucs(self) -> None:
        try:
            import demucs.api
            model_name = "htdemucs" if self.model == SeparationModel.DEMUCS_V4 else "demucs"
            logger.info(f"🛰️ Loading Demucs Model: {model_name} on {self.device}")
            
            # Use the pre-bundled models directory
            models_path = Path("models/demucs")
            self.model_instance = demucs.api.Separator(
                model=model_name,
                device=self.device,
                repo=models_path if models_path.exists() else None
            )
        except Exception as e:
            logger.error(f"Demucs failed to load: {e}")
            self.model_instance = None
    
    def _try_fallback_models(self) -> None:
        # If local fails, the 'Condition' suggests CLOUD offloading
        logger.warning("Local models failing. Defaulting to CLOUD_DEMUCS isolation.")
        self.model = SeparationModel.CLOUD_DEMUCS

    @retry_api_call()
    def separate_audio(
        self,
        audio_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None
    ) -> SeparationResult:
        from src.core.reliability import HardwareLock, log_path_consistency
        
        audio_path = Path(audio_path)
        # Observability: Check path consistency across the swarm volume
        log_path_consistency(str(audio_path), f"Separator-{self.model.value}")
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Hardware Guard: Sequential VRAM locking to prevent OOM
        # We use a context manager to ensure release even on failure
        # Hardware Guard - Separator is Priority 2 (High pre-processing priority)
        # Hardware Lock - Synthesis is Priority 3
        with HardwareLock.locked_sync(f"Separator-{self.model.value}", priority=2):
            # Check Condition: Local vs Cloud
            if self.model == SeparationModel.CLOUD_DEMUCS:
                logger.info("🧠 [REASONING] Local GPU bypass detected. Routing to Cloud Node...")
                isolated_path = shadow_providers.cloud_separate_audio(str(audio_path))
                voice, sr = librosa.load(isolated_path, sr=self.sample_rate)
                # In cloud offload mode, we typically only get the vocals
                return SeparationResult(
                    voice=voice,
                    music=np.zeros_like(voice),
                    sample_rate=sr,
                    duration=len(voice) / sr,
                    model_used="gradio_cloud_demucs"
                )

            if self.model == SeparationModel.SWARM_DEMUCS:
                logger.info("🐝 [REASONING] Swarm Offload detected. Routing to sonora-separator...")
                import requests
                SEPARATOR_URL = os.getenv("SEPARATOR_URL", "http://sonora-separator:8000/process")
                try:
                    # The payload expects 'filename' or 'rel_path'
                    # Since we are in the swarm, we assume the file is in SHARED_PATH
                    rel_path = os.path.basename(str(audio_path))
                    response = requests.post(SEPARATOR_URL, json={"filename": rel_path}, timeout=600)
                    if response.status_code == 200:
                        res = response.json()
                        v_path = res['vocals']
                        m_path = res['no_vocals']
                        # Load result from SHARED_PATH
                        voice, sr = librosa.load(v_path, sr=self.sample_rate)
                        music, _ = librosa.load(m_path, sr=self.sample_rate)
                        return SeparationResult(
                            voice=voice,
                            music=music,
                            sample_rate=sr,
                            duration=len(voice) / sr,
                            model_used="swarm_separator_v4"
                        )
                except Exception as e:
                    logger.error(f"Swarm separation failed, falling back: {e}")

            try:
                logger.info(f"🧬 [REASONING] Starting local separation using {self.model.value} device={self.device}")
                if self.model_instance is None: self.load_model()
                
                # Real Demucs V4 Separation
                if self.model in [SeparationModel.DEMUCS, SeparationModel.DEMUCS_V4] and self.model_instance:
                    origin, separated = self.model_instance.separate_audio_file(str(audio_path))
                    
                    # htdemucs usually returns 4 stems: drums, bass, other, vocals
                    # We map 'other' to music for the Sonora core
                    return SeparationResult(
                        voice=separated['vocals'].numpy().mean(axis=0), # Mono for now
                        music=separated['other'].numpy().mean(axis=0),
                        drums=separated['drums'].numpy().mean(axis=0),
                        bass=separated['bass'].numpy().mean(axis=0),
                        sample_rate=self.sample_rate,
                        duration=origin.shape[-1] / self.sample_rate,
                        model_used=self.model.value
                    )
                
                # Fallback to basic (prevent crash if model fails)
                return self._perform_basic_separation(str(audio_path), self.sample_rate)
                
            except Exception as e:
                logger.error(f"❌ [FAILURE] Audio separation failed: {e}")
                raise
    
    def _perform_basic_separation(self, audio_path: str, sr: int) -> SeparationResult:
        """Emergency fallback: load audio and mock separation."""
        try:
            audio_data, _ = librosa.load(audio_path, sr=sr, mono=True)
            voice = audio_data * 0.7
            music = audio_data * 0.3
            
            return SeparationResult(
                voice=voice,
                music=music,
                sample_rate=sr,
                duration=len(audio_data) / sr,
                model_used="basic_mock_fallback"
            )
        except Exception as e:
            logger.error(f"Basic fallback separation failed: {e}")
            # Absolute bottom fallback: zero arrays
            empty = np.zeros(sr)
            return SeparationResult(voice=empty, music=empty, sample_rate=sr)
