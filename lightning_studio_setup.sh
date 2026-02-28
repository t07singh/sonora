#!/bin/bash
# 🛰️ Sonora Heavyweight Swarm - Lightning AI Setup Script
# This version uses Docker Compose to manage the 18GB high-res AI stack.

echo "🎬 Initializing Sonora Swarm Persistence Sequence..."

# 1. Ensure shared volumes exist
mkdir -p shared_data models scripts stems

# 2. Cleanup old container naming conflicts
echo "🧹 Cleaning up legacy container naming conflicts..."
docker stop sonora-main-app >/dev/null 2>&1
docker rm sonora-main-app >/dev/null 2>&1

# 3. Launch the High-Res Neural Stack via Docker Compose
# This handles:
# - sonora-api (8000)
# - sonora-transcriber (8001) [Whisper Large-v3]
# - sonora-synthesizer (8002) [Qwen3-TTS]
# - sonora-separator (8003) [Demucs v4]
# - sonora-ui (8501) [Cockpit Frontend]
# - sonora-model-downloader (Background Weight Pulling)

echo "🚀 Launching Sonora Swarm Stack..."
docker compose up -d

echo ""
echo "✅ Swarm is launching in the background."
echo "🎙️ Access via Port Viewer Plugin (Port 8501 for UI, 8000 for API)"
echo "📡 Neural Separator available on port 8003."
echo ""
echo "📥 To monitor the 18GB model download, run:"
echo "   docker logs -f sonora-model-downloader"
