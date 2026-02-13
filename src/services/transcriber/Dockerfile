FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_core.txt .
# Add service-specific requirements if they exist, or just use core
COPY src/services/transcriber/requirements.txt ./requirements_transcriber.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_core.txt
RUN pip install --no-cache-dir -r requirements_transcriber.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["python", "src/services/transcriber/main.py"]
