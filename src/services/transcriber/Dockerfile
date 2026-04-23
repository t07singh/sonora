FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    git \
    build-essential \
    execstack \
    && rm -rf /var/lib/apt/lists/*

# Symlink python3 to python so scripts work
RUN ln -s /usr/bin/python3 /usr/bin/python

COPY requirements_core.txt .
# Add service-specific requirements if they exist, or just use core
COPY src/services/transcriber/requirements.txt ./requirements_transcriber.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_core.txt
RUN pip install --no-cache-dir -r requirements_transcriber.txt

# Remove executable stack flag from CTranslate2 to prevent Docker/WSL crashes
RUN find $(python3 -c "import site; print(site.getsitepackages()[0])")/ctranslate2 -name "*.so*" -exec execstack -c {} \;

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["python", "src/services/transcriber/main.py"]
