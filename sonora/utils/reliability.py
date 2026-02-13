import time
import functools
import logging
import random

# Configure logger to be visible in console for studio demos
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.reliability")

def retry_api_call(max_retries=3, base_delay=1):
    """
    Studio-Hardened Retry Decorator.
    Logic: Exponential backoff (1s, 2s, 4s) for cloud API resilience.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"[FAILURE] All {max_retries} retries exhausted for {func.__name__}. Error: {e}")
                        raise e
                    
                    # Exponential Backoff: 2^(n-1) * base_delay
                    delay = base_delay * (2 ** (retries - 1))
                    
                    # Log with specific format for visibility during demos
                    logger.warning(f"[RETRY] Attempt {retries} for {func.__name__} failed. Retrying in {delay}s....")
                    
                    time.sleep(delay)
        return wrapper
    return decorator
