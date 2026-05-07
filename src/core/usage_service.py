import os
import json
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("sonora.usage")

class UsageService:
    """
    Service responsible for tracking and persisting usage metrics across the Sonora Studio swarm.
    In production, this would sync to a database (e.g., Supabase/PostgreSQL).
    Currently logs to a persistent JSON file in the shared volume.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.getenv("SONORA_DATA_DIR", "sonora/data"),
            "usage_metrics.jsonl"
        )
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def log_event(self, provider: str, task: str, duration: float, metadata: Dict[str, Any] = None):
        """
        Records a usage event.
        
        Args:
            provider: The service provider (e.g., 'groq', 'elevenlabs', 'hf-space')
            task: The type of work done ('asr', 'tts', 'separation')
            duration: Processing time or media duration in seconds
            metadata: Additional context (model_id, file_size, language)
        """
        event = {
            "timestamp": time.time(),
            "provider": provider,
            "task": task,
            "duration": round(duration, 3),
            "metadata": metadata or {}
        }
        
        # 1. Log for immediate observability
        logger.info(f"📊 [USAGE_TRACKING] {json.dumps(event)}")
        
        # 2. Persist to local JSONL for audit
        try:
            with open(self.storage_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist usage event: {e}")

# Global singleton
usage_service = UsageService()

def record_usage(provider: str, task: str, duration: float, metadata: Dict[str, Any] = None):
    """Convenience wrapper for the global usage service."""
    usage_service.log_event(provider, task, duration, metadata)
