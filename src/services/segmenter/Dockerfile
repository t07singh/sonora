# Sonora Segmenter Service — Dockerfile
# Handles: VAD, Whisper ASR, pyannote Diarization, Forced Alignment, Video Cutting

FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set Mecab dictionary path
ENV MECAB_DICDIR=/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-utf8

WORKDIR /app

# Copy requirements first for caching
COPY src/services/segmenter/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY src/core/ /app/src/core/
COPY sonora/audio_editing/ /app/sonora/audio_editing/
COPY sonora/core/reliability.py /app/sonora/core/reliability.py
COPY sonora/__init__.py /app/sonora/__init__.py

# Copy segmenter service
COPY src/services/segmenter/ /app/src/services/segmenter/

# Create data directories
RUN mkdir -p /tmp/sonora/uploads /tmp/sonora/segments /tmp/sonora/stems

# Environment
ENV SEGMENTER_PORT=8004
ENV SHARED_PATH=/tmp/sonora
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

CMD ["python", "-m", "uvicorn", "src.services.segmenter.main:app", \
     "--host", "0.0.0.0", "--port", "8004", "--log-level", "info"]
