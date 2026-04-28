FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_core.txt .
RUN pip install --upgrade pip

# Pre-install heavy AI dependencies for better layer caching
RUN pip install --no-cache-dir "torch>=2.0.0" "torchaudio>=2.0.0" "numpy<2.0.0" pandas transformers accelerate huggingface_hub

# Install remaining dependencies including demucs and faster-whisper
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements_core.txt

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

ENV PYTHONPATH=$HOME/app

# Fix Windows line endings and set permissions
USER root
RUN apt-get update && apt-get install -y sed && \
    sed -i 's/\r$//' entrypoint_unified.sh && \
    chmod +x entrypoint_unified.sh
USER user

EXPOSE 7860

CMD ["./entrypoint_unified.sh"]
