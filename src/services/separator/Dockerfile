FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_core.txt .
COPY src/services/separator/requirements.txt ./requirements_separator.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_core.txt
RUN pip install --no-cache-dir -r requirements_separator.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "src/services/separator/main.py"]
