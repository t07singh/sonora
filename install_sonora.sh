#!/bin/bash
set -e

# INSTALL SONORA B2B APPLIANCE
# v1.0.0

echo "🚀 INITIALIZING SONORA INSTALLER..."
echo "==================================="

# 1. System Checks
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker found."

# 1.5 Hardware Pre-Flight Check (GPU)
echo "Checking GPU capabilities..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  NVIDIA GPU not detected."
    echo "   Visual Sync (Wav2Lip-HQ) will run in CPU-Legacy mode (Slow)."
else
    echo "✅ NVIDIA GPU detected."
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi
echo ""

# 2. Configuration Challenge
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Configuring Production Secrets."
    echo ""
    read -p "Enter your SONORA_API_KEY (Admin Access): " SONORA_KEY
    read -p "Enter OPENAI_API_KEY: " OPENAI_KEY
    read -p "Enter ELEVENLABS_API_KEY: " ELEVEN_KEY
    
    cat > .env << EOL
SONORA_API_KEY=$SONORA_KEY
OPENAI_API_KEY=$OPENAI_KEY
ELEVENLABS_API_KEY=$ELEVEN_KEY
SONORA_DATA_DIR=/app/sonora/data
LOG_LEVEL=INFO
EOL
    echo "✅ Configuration saved to .env"
fi

# 3. Launch
echo ""
echo "🚢 Deploying Production Stack..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "🎉 SONORA IS LIVE!"
echo "   Dashboard: http://localhost:8501"
echo "   API:       http://localhost:8000"
echo ""
echo "   Admin Key: $(grep SONORA_API_KEY .env | cut -d '=' -f2)"
