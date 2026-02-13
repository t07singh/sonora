
import os
import time
import random
import logging
import functools
import torch
import asyncio
from typing import Callable, Any, TypeVar, Optional, Union

T = TypeVar('T')
logger = logging.getLogger("sonora.core.reliability")

class HardwareLock:
    """
    Global guard for VRAM/CPU resources.
    Ensures heavy models (Whisper, Demucs, Qwen) run sequentially to prevent crashes.
    """
    _lock = asyncio.Lock()
    _active_model: Optional[str] = None

    @classmethod
    async def acquire(cls, model_name: str):
        await cls._lock.acquire()
        cls._active_model = model_name
        logger.info(f"🔒 HardwareLock ACQUIRED by {model_name}. Loading weights...")

    @classmethod
    def release(cls):
        model = cls._active_model
        cls._active_model = None
        cls._lock.release()
        logger.info(f"🔓 HardwareLock RELEASED by {model}. Unloading weights...")

def retry_api_call(
    _func: Optional[Callable] = None,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0
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
                        logger.error(f"[LOCAL_HARDWARE_TIMEOUT] {func.__name__} failed after {max_retries} attempts.")
                        raise e
                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(f"[RETRY] {func.__name__} attempt {retries} failed. Waiting {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator if _func is None else decorator(_func)

def get_device():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        logger.info("Sonora Health Check: No GPU found. Hardening for CPU-Only mode.")
    return device
