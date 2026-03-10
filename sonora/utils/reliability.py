import time
import functools
import logging
import random

# Configure logger to be visible in console for studio demos
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.reliability")

def retry_api_call(max_retries=3, base_delay=1):
    """
    Studio-Hardened Retry Decorator with Quota-Aware coolness.
    Logic: 
    - Normal errors: Exponential backoff (1s, 2s, 4s).
    - Rate Limit (429/Quota): Mandatory 65s sleep to reset token bucket.
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
                    err_str = str(e).lower()
                    
                    # Detect Quota/Rate Limit
                    is_rate_limit = "429" in err_str or "quota" in err_str or "limit" in err_str
                    
                    if retries > max_retries:
                        logger.error(f"[FAILURE] All {max_retries} retries exhausted for {func.__name__}. Error: {e}")
                        raise e
                    
                    if is_rate_limit:
                        # Gemini Free Tier resets after 60s. We wait 65s for safety.
                        delay = 65
                        logger.warning(f"🚦 [RATE LIMIT] {func.__name__} hit Google Quota. Entering 65s Cool Down...")
                    else:
                        # Exponential Backoff for general errors
                        delay = base_delay * (2 ** (retries - 1))
                        logger.warning(f"[RETRY] Attempt {retries} for {func.__name__} failed. Retrying in {delay}s....")
                    
                    time.sleep(delay)
        return wrapper
    return decorator
