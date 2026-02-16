FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_core.txt .
COPY src/services/lipsync_service/requirements.txt ./requirements_lipsync.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_core.txt
RUN pip install --no-cache-dir -r requirements_lipsync.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8004

CMD ["python", "src/services/lipsync_service/app.py"]
