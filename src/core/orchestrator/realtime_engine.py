import os
import librosa
import soundfile as sf
import redis
import json
import logging
import time
from src.core.reliability import retry_api_call

logger = logging.getLogger("sonora.orchestrator")

class RealTimeProcessingEngine:
    def __init__(self, redis_url="redis://redis-cache:6379/0"):
        try:
            self.r = redis.from_url(redis_url)
        except Exception as e:
            logger.error(f"Redis Connection Failed: {e}")
            self.r = None

    @retry_api_call(max_retries=3)
    def align_audio_to_duration(self, audio_path: str, target_duration: float, output_path: str) -> str:
        """
        Sync-Master Logic: Time-stretches audio to align with original Japanese timestamps.
        Clamps at 0.8x and 1.3x to prevent artifacts.
        """
        start_time = time.time()
        y, sr = librosa.load(audio_path, sr=None)
        current_duration = librosa.get_duration(y=y, sr=sr)
        
        if current_duration <= 0 or target_duration <= 0:
            return audio_path

        stretch_rate = current_duration / target_duration
        clamped_rate = max(0.8, min(1.3, stretch_rate))
        
        if stretch_rate != clamped_rate:
            logger.warning(f"Stretch rate {stretch_rate:.2f} clamped to {clamped_rate:.2f}")

        y_stretched = librosa.effects.time_stretch(y, rate=clamped_rate)
        sf.write(output_path, y_stretched, sr)
        
        # Telemetry
        process_time = (time.time() - start_time) * 1000
        if self.r:
            self.r.set("global:last_alignment_latency_ms", f"{process_time:.2f}")
            self.r.incrby("global:total_processed_ms", int(target_duration * 1000))
            
        return output_path

    def update_hud_state(self, session_id: str, stage: str, progress: float):
        """Stateless status updates via Redis."""
        if not self.r: return
        
        state = {
            "stage": stage,
            "progress": progress,
            "timestamp": time.time()
        }
        self.r.set(f"{session_id}:hud", json.dumps(state))
        self.r.set("global:last_op_status", stage)
        self.r.incr("global:swarm_request_count")
