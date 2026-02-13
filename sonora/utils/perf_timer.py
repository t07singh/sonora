import time
import logging
import functools
from contextlib import contextmanager

logger = logging.getLogger("perf_timer")

class PerfTimer:
    def __init__(self, name, logger=None):
        self.name = name
        self.logger = logger or globals()['logger']
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        self.logger.info(f"⏱️ {self.name} completed in {elapsed:.4f}s")

class PerfProfiler:
    def __init__(self, name, logger=None):
        self.name = name
        self.logger = logger or globals()['logger']
        self.stages = []

    @contextmanager
    def stage(self, stage_name):
        start = time.perf_counter()
        yield
        elapsed = time.perf_counter() - start
        self.stages.append((stage_name, elapsed))
        self.logger.info(f"   └─ Stage '{stage_name}': {elapsed:.4f}s")

    def report(self):
        total = sum(s[1] for s in self.stages)
        self.logger.info(f"📊 Performance Report: {self.name}")
        for stage_name, elapsed in self.stages:
            self.logger.info(f"   - {stage_name}: {elapsed:.4f}s ({(elapsed/total)*100:.1f}%)")
        self.logger.info(f"   TOTAL: {total:.4f}s")

def time_function(name=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timer_name = name or func.__name__
            with PerfTimer(timer_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator