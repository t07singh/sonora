
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

class SonoraProject:
    """
    Manages Sonora dubbing projects.
    """
    def __init__(self, data_root, name):
        self.data_root = Path(data_root)
        self.name = name
        self.path = self.data_root / name
        
    @staticmethod
    def list_projects(data_root):
        """List all available projects in the data directory."""
        root = Path(data_root)
        if not root.exists():
            return []
        
        projects = []
        for p in root.iterdir():
            if p.is_dir() and (p / "project_meta.json").exists():
                projects.append(p.name)
        return projects

    def create(self, source_lang="ja", target_lang="en", priority="Emotion"):
        """Creates a new project structure."""
        if self.path.exists():
            raise FileExistsError(f"Project {self.name} already exists.")
            
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "audio").mkdir(exist_ok=True)
        (self.path / "video").mkdir(exist_ok=True)
        (self.path / "transcripts").mkdir(exist_ok=True)
        
        meta = {
            "name": self.name,
            "created_at": datetime.now().isoformat(),
            "source_lang": source_lang,
            "target_lang": target_lang,
            "priority": priority,
            "status": "new"
        }
        
        self.save_metadata(meta)
        return meta

    def save_metadata(self, meta_data):
        with open(self.path / "project_meta.json", "w") as f:
            json.dump(meta_data, f, indent=2)

    def load_metadata(self):
        if not (self.path / "project_meta.json").exists():
            return None
        with open(self.path / "project_meta.json", "r") as f:
            return json.load(f)
