#!/bin/bash
# Startup script for Sonora Unified (API + UI)

echo "🎬 Starting Sonora Swarm Unified Services..."

# 0. Check and download neural weights (Cloud-side download/Volume Persistence)
echo "📥 Checking for model weights in /app/models..."
# bundle_weights.py will populate /app/models which is shared across services
python scripts/bundle_weights.py

# 1. Start the FastAPI backend in the background
echo "🚀 Launching FastAPI Backend on port 8000..."
# We keep the backend process attached so we can see logs in the terminal
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
