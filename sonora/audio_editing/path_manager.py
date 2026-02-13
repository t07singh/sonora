import os
import uuid
import shutil
import logging
import subprocess
import time
import functools
from pathlib import Path
from io import BytesIO

# Configure logging
logger = logging.getLogger("sonora.path_manager")

def get_data_dir() -> Path:
    """Returns the root data directory from env or default."""
    env_path = os.getenv("SONORA_DATA_DIR")
    if env_path:
        return Path(env_path).absolute()
    # Default: project_root/sonora/data
    return Path("sonora/data").absolute()

class SonoraProcessingError(Exception):
    """Custom exception for Sonora processing failures."""
    def __init__(self, message, hint="Check FFmpeg status"):
        self.message = f"{message} | Hint: {hint}"
        super().__init__(self.message)

class SessionManager:
    """Tracks and deletes temporary files created during a user session."""
    def __init__(self):
        self.registry = []

    def track(self, path: str):
        abs_path = str(Path(path).absolute())
        if abs_path not in self.registry:
            self.registry.append(abs_path)
            logger.debug(f"SessionManager: Tracking {abs_path}")

    def purge_all(self):
        """Deletes all tracked files."""
        for path in self.registry:
            try:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    logger.info(f"SessionManager: Purged {path}")
            except Exception as e:
                logger.error(f"SessionManager: Failed to purge {path}: {e}")
        self.registry = []

def get_secure_path(file_obj) -> str:
    """
    Converts Streamlit UploadedFile (BytesIO) to a physical disk path.
    Generates a unique UUID-based filename.
    """
    temp_dir = get_data_dir() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract extension if possible
    filename = getattr(file_obj, 'name', 'input.wav')
    ext = filename.split('.')[-1]
    
    unique_id = uuid.uuid4().hex
    target_path = temp_dir / f"secure_{unique_id}.{ext}"
    
    try:
        # If it's a Streamlit UploadedFile or BytesIO
        if hasattr(file_obj, 'getvalue'):
            with open(target_path, "wb") as f:
                f.write(file_obj.getvalue())
        else:
            # Assume it's already a path or needs reading
            with open(target_path, "wb") as f:
                f.write(file_obj.read())
                
        logger.info(f"get_secure_path: Created {target_path}")
        return str(target_path)
    except Exception as e:
        raise SonoraProcessingError(f"Failed to write secure path: {str(e)}", "Insufficient Permissions or Disk Full")

def validate_output(path: str):
    """
    Safety check for model outputs. Raises error if file is missing or 0 bytes.
    """
    if not os.path.exists(path):
        raise SonoraProcessingError(f"Output file missing at {path}", "Model failed to write output")
        
    if os.path.getsize(path) == 0:
        raise SonoraProcessingError(f"Output file at {path} is 0 bytes", "FFmpeg or AI model produced empty stream")
        
    logger.info(f"validate_output: {path} is healthy")

def file_lock(timeout: int = 30):
    """
    Decorator to ensure file streams are closed and stable before execution.
    Used to prevent race conditions in bus_system.py.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find a path in the arguments
            path_to_check = None
            for arg in args:
                if isinstance(arg, str) and (arg.endswith('.wav') or arg.endswith('.mp4')):
                    path_to_check = arg
                    break
            
            if path_to_check:
                start_time = time.time()
                last_size = -1
                while time.time() - start_time < timeout:
                    if os.path.exists(path_to_check):
                        current_size = os.path.getsize(path_to_check)
                        if current_size > 0 and current_size == last_size:
                            break
                        last_size = current_size
                    time.sleep(1)
                else:
                    raise SonoraProcessingError(f"Timeout waiting for file stability: {path_to_check}")
                    
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_ffmpeg() -> bool:
    """
    Startup utility to verify FFmpeg accessibility.
    """
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        logger.info("check_ffmpeg: FFmpeg is accessible")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("check_ffmpeg: FFmpeg NOT FOUND in system PATH")
        return False