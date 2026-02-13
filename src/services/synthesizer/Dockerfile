FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_core.txt .
COPY src/services/synthesizer/requirements.txt ./requirements_synthesizer.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_core.txt
RUN pip install --no-cache-dir -r requirements_synthesizer.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["python", "src/services/synthesizer/main.py"]
