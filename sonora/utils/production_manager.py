import os
import uuid
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger("sonora.production_manager")

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    URGENT = "urgent"

class BatchProcessor:
    """Manages high-volume dubbing queues for anime seasons."""
    def __init__(self, storage_root: str = "sonora/data/production"):
        self.root = Path(storage_root)
        self.queue_path = self.root / "queue.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.jobs: List[Dict[str, Any]] = self._load_queue()

    def _load_queue(self) -> List[Dict]:
        if self.queue_path.exists():
            with open(self.queue_path, 'r') as f:
                return json.load(f)
        return []

    def _save_queue(self):
        with open(self.queue_path, 'w') as f:
            json.dump(self.jobs, f, indent=2)

    def add_job(self, video_path: str, project_id: str, episode: str, priority: Priority = Priority.NORMAL):
        job = {
            "job_id": str(uuid.uuid4())[:8],
            "video_path": video_path,
            "filename": os.path.basename(video_path),
            "project_id": project_id,
            "episode": episode,
            "priority": priority.value,
            "status": JobStatus.QUEUED.value,
            "progress": 0.0,
            "quality_score": 0.0,
            "created_at": time.time(),
            "error": None
        }
        self.jobs.append(job)
        self._save_queue()
        return job["job_id"]

    def get_stats(self):
        total = len(self.jobs)
        completed = sum(1 for j in self.jobs if j["status"] == "completed")
        failed = sum(1 for j in self.jobs if j["status"] == "failed")
        processing = sum(1 for j in self.jobs if j["status"] == "processing")
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "avg_quality": sum(j["quality_score"] for j in self.jobs if j["quality_score"] > 0) / (completed or 1)
        }

class ProductionProjectManager:
    """Handles multi-series and multi-season organization."""
    def __init__(self, storage_root: str = "sonora/data/projects"):
        self.root = Path(storage_root)
        self.projects_path = self.root / "registry.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, Dict] = self._load_projects()

    def _load_projects(self) -> Dict:
        if self.projects_path.exists():
            with open(self.projects_path, 'r') as f:
                return json.load(f)
        return {
            "demo-01": {
                "name": "My Hero Academia S06",
                "episodes": 24,
                "completed": 12,
                "characters": ["Deku", "Bakugo", "All Might"]
            }
        }

    def _save_projects(self):
        with open(self.projects_path, 'w') as f:
            json.dump(self.projects, f, indent=2)

    def create_project(self, name: str, episodes: int):
        pid = f"proj-{str(uuid.uuid4())[:6]}"
        self.projects[pid] = {
            "name": name,
            "episodes": episodes,
            "completed": 0,
            "characters": [],
            "created_at": time.time()
        }
        self._save_projects()
        return pid
