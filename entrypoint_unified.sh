#!/bin/bash
# Startup script for Sonora Unified (API + UI)

echo "🎬 Starting Sonora Swarm Unified Services..."
export SHARED_PATH="/home/user/app/shared_data"
export SONORA_DATA_DIR=$SHARED_PATH
export MODELS_DIR="/home/user/app/models"
mkdir -p $SHARED_PATH $MODELS_DIR

# 0. Check and download neural weights (Cloud-side download/Volume Persistence)
echo "📥 Checking for model weights in /app/models..."
# bundle_weights.py will populate /app/models which is shared across services
python scripts/bundle_weights.py

# 1. Start the Segmenter service (on port 8004)
echo "🛰️ Launching Sonora Segmenter Service on port 8004..."
export SEGMENTER_URL="http://127.0.0.1:8004"
uvicorn src.services.segmenter.main:app --host 0.0.0.0 --port 8004 --log-level info &
SEGMENTER_PID=$!
sleep 2
echo "💓 Segmenter heartbeat check..."
curl -s http://127.0.0.1:8004/health || echo "⚠️ Segmenter health check failed!"

# 2. Start the FastAPI backend in the background (on port 8000)
echo "🚀 Launching FastAPI Backend on port 8000..."
python run_server.py &
BACKEND_PID=$!

# 2. Wait a few seconds for the backend to initialize
echo "⏳ Waiting for backend neural handshake..."
sleep 5

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ CRITICAL: Backend failed to start! Check logs above."
    exit 1
fi

# 3. Start the Streamlit frontend in the foreground
echo "🎙️ Launching Streamlit UI on port 7860 (Hugging Face Spaces requirement)..."
streamlit run unified_demo.py --server.port=7860 --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false --server.maxUploadSize=1024
