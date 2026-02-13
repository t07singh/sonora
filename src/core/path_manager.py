import os
from pathlib import Path
import logging

logger = logging.getLogger("sonora.core.path_manager")

# Shared mount point for all Sonora microservices
SHARED_ROOT = Path("/tmp/sonora")

def ensure_shared_workspace():
    """Ensures the shared volume structure exists."""
    os.makedirs(SHARED_ROOT, exist_ok=True)
    os.makedirs(SHARED_ROOT / "uploads", exist_ok=True)
    os.makedirs(SHARED_ROOT / "stems", exist_ok=True)
    os.makedirs(SHARED_ROOT / "takes", exist_ok=True)
    os.makedirs(SHARED_ROOT / "exports", exist_ok=True)

def resolve_shared_path(filename: str, category: str = "uploads") -> str:
    """
    Resolves a simple filename to its absolute path within the shared volume.
    Category can be: uploads, stems, takes, exports.
    """
    path = SHARED_ROOT / category / filename
    return str(path)

def get_relative_shared_path(full_path: str) -> str:
    """Returns the path relative to SHARED_ROOT for API transmission."""
    try:
        return str(Path(full_path).relative_to(SHARED_ROOT))
    except ValueError:
        # Fallback if path is already relative or outside root
        return os.path.basename(full_path)
