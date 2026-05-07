import os
import logging
import subprocess
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger("sonora.segmenter.omnishotcut")

class OmniShotCutDetector:
    """
    OmniShotCut Detector — Holistic Relational Shot Boundary Detection.
    Detects visual transitions (cuts, fades, wipes) to guide neural clip slicing.
    """
    
    def __init__(self, use_cloud: bool = True):
        self.use_cloud = use_cloud
        self.cloud_url = os.getenv("OMNISHOTCUT_URL", "https://huggingface.co/spaces/sonora/omnishotcut")
        self.hf_token = os.getenv("HF_TOKEN")

    def detect_shots(self, video_path: str) -> List[float]:
        """
        Detect shot boundaries in a video file.
        Returns a list of timestamps (seconds) where cuts occur.
        """
        logger.info(f"🎬 Running OmniShotCut detection on {video_path}...")
        
        # 1. Try Cloud Shadow Provider (Preferred for SOTA accuracy)
        if self.use_cloud and self.hf_token:
            try:
                return self._detect_via_cloud(video_path)
            except Exception as e:
                logger.warning(f"☁️ Cloud OmniShotCut failed: {e}. Falling back to local engine.")
        
        # 2. Local Fallback: PySceneDetect (Adaptive)
        return self._detect_via_scenedetect(video_path)

    def _detect_via_cloud(self, video_path: str) -> List[float]:
        """Offload to a Hugging Face Space running the OmniShotCut Transformer."""
        from gradio_client import Client
        client = Client(self.cloud_url, hf_token=self.hf_token)
        result = client.predict(video_path, api_name="/predict")
        # Assuming the result is a JSON list of timestamps
        if isinstance(result, str):
            import json
            return json.loads(result)
        return result

    def _detect_via_ffmpeg(self, video_path: str, threshold: float = 0.3) -> List[float]:
        """
        Legacy: Heuristic-based shot detection using FFmpeg's scdet filter.
        """
        logger.info(f"🎞️ Using local FFmpeg scdet (threshold={threshold})...")
        cmd = [
            "ffmpeg", "-i", video_path,
            "-filter:v", f"scdet=threshold={threshold}",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stderr
            boundaries = []
            for line in output.split("\n"):
                if "lavfi.scdet.pts_time" in line:
                    match = re.search(r"pts_time:\s*([\d\.]+)", line)
                    if match:
                        boundaries.append(float(match.group(1)))
            return sorted(list(set(boundaries)))
        except Exception as e:
            logger.error(f"❌ Local FFmpeg shot detection failed: {e}")
            return []

    def _detect_via_scenedetect(self, video_path: str) -> List[float]:
        """
        High-Quality Local Fallback: PySceneDetect (Adaptive).
        Uses content-aware analysis to find transitions.
        """
        try:
            from scenedetect import detect, AdaptiveDetector
            logger.info("🎬 Using PySceneDetect (Adaptive) for visual slicing...")
            scenes = detect(video_path, AdaptiveDetector())
            # scenes is a list of (start_time, end_time) tuples
            boundaries = [scene[0].get_seconds() for scene in scenes[1:]]
            logger.info(f"✅ PySceneDetect found {len(boundaries)} boundaries.")
            return boundaries
        except ImportError:
            logger.warning("⚠️ PySceneDetect not installed. Falling back to FFmpeg scdet.")
            return self._detect_via_ffmpeg(video_path)
        except Exception as e:
            logger.error(f"❌ PySceneDetect failed: {e}")
            return self._detect_via_ffmpeg(video_path)

import re # Needed for re.search in _detect_via_ffmpeg
