
import os
import time
import random
import logging
import functools
import torch
import asyncio
import redis
from typing import Callable, Any, TypeVar, Optional, Union

T = TypeVar('T')
logger = logging.getLogger("sonora.core.reliability")

# Initialize Redis client for distributed locking
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-cache:6379/0")
try:
    r_client = redis.from_url(REDIS_URL)
except Exception as e:
    logger.warning(f"Distributed Lock: Redis unavailable, falling back to local safety. {e}")
    r_client = None

class HardwareLock:
    """
    Distributed guard for VRAM/CPU resources using Redis.
    Ensures services (Transcriber, Synthesizer, LipSync) run sequentially 
    across separate Docker containers to prevent GPU OOM crashes.
    """
    _local_lock = asyncio.Lock()
    _lock_key = "swarm:hardware_mutex"
    _lock_timeout = 120 # 2 minute safety timeout

    @classmethod
    async def acquire(cls, model_name: str):
        logger.info(f"🔒 Requesting HardwareLock for {model_name}...")
        
        if r_client:
            # Distributed Lock Logic: Poll until we can set the key
            while not r_client.set(cls._lock_key, model_name, ex=cls._lock_timeout, nx=True):
                await asyncio.sleep(0.5)
            logger.info(f"🛰️ Distributed HardwareLock ACQUIRED by {model_name} node.")
        else:
            await cls._local_lock.acquire()
            logger.info(f"🔒 Local HardwareLock ACQUIRED by {model_name}.")

    @classmethod
    def release(cls):
        if r_client:
            r_client.delete(cls._lock_key)
            logger.info(f"🔓 Distributed HardwareLock RELEASED.")
        else:
            try:
                cls._local_lock.release()
                logger.info(f"🔓 Local HardwareLock RELEASED.")
            except RuntimeError:
                pass

def retry_api_call(
    _func: Optional[Callable] = None,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"[FAILURE] All {max_retries} retries exhausted for {func.__name__}. Error: {e}")
                        raise e
                    
                    delay = min(max_delay, base_delay * (backoff_factor ** (retries - 1)))
                    if jitter:
                        delay = random.uniform(0.5 * delay, delay)
                    
                    logger.warning(f"[RETRY] Attempt {retries} for {func.__name__} failed. Retrying in {delay:.2f}s....")
                    time.sleep(delay)
        return wrapper

    if _func is None:
        return decorator
    return decorator(_func)

def get_device():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        logger.info("Sonora Health Check: No GPU found. Hardening for CPU-Only mode.")
    return device

def log_path_consistency(path: str, node: str):
    """Utility to verify absolute pathing across the shared volume."""
    abs_path = os.path.abspath(path)
    logger.info(f"📁 PATH_CONSISTENCY [{node}]: Accessing absolute path -> {abs_path}")
    if not os.path.exists(abs_path):
        logger.error(f"❌ GHOST_PATH DETECTED: {abs_path} is invisible to this container.")
    return abs_path
