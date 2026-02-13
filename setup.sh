#!/bin/bash

echo "🚀 Initializing Sonora AI Dubbing Studio Setup..."

# 1. Create Directory Structure
echo "📂 Creating data directories..."
mkdir -p sonora/data/audio_clips
mkdir -p sonora/data/input_videos
mkdir -p sonora/data/output_videos
mkdir -p sonora/data/temp

# 2. Check for FFmpeg
if ! command -v ffmpeg &> /dev/null
then
    echo "⚠️ FFmpeg not found. Attempting to install..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update && sudo apt install -y ffmpeg
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    else
        echo "❌ Automated FFmpeg install not supported for your OS."
        echo "Please install FFmpeg manually: https://ffmpeg.org/download.html"
    fi
else
    echo "✅ FFmpeg Engine: READY"
fi

# 3. Setup Python Virtual Environment (Optional, but recommended)
if [ ! -d "venv" ]; then
    echo "🐍 Setting up Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing Python libraries..."
source venv/bin/activate
pip install --upgrade pip
pip install streamlit openai elevenlabs ffmpeg-python pydub librosa numpy soundfile pydantic-settings

echo "-----------------------------------------------"
echo "✅ Setup Complete!"
echo "To start the studio, run:"
echo "source venv/bin/activate && python sonora/app.py"
echo "-----------------------------------------------"