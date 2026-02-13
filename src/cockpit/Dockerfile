FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_core.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_core.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8501

CMD ["streamlit", "run", "unified_demo.py", "--server.port=8501", "--server.address=0.0.0.0"]
