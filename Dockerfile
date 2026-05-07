# Sonora Studio Unified Container - Cloud Edition
# Optimized for Hugging Face Spaces and Monetization
FROM python:3.10-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install core dependencies first for caching
COPY requirements_core.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements_core.txt

# Pre-install Gradio Client for cloud offloading
RUN pip install --no-cache-dir gradio_client

# Create non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/home/user/app

WORKDIR $HOME/app

# Copy application code
COPY --chown=user . $HOME/app

# Fix line endings and permissions
USER root
RUN sed -i 's/\r$//' entrypoint_unified.sh && \
    chmod +x entrypoint_unified.sh
USER user

# Health check for orchestration stability
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

EXPOSE 7860

CMD ["./entrypoint_unified.sh"]
