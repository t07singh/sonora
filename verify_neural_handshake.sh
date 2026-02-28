#!/bin/bash
# Neural Handshake Verification Script
# To be run INSIDE the Docker container

echo "📡 Starting Sonora Neural Handshake Verification..."

# 1. Check GPU availability
echo -n "Checking CUDA Hardware... "
python3 -c "import torch; print('✅ OK' if torch.cuda.is_available() else '⚠️ CPU ONLY')"

# 2. Check Model Weights
echo "Checking Neural Weights Disk Presence:"
models=(
    "models/qwen7b:Qwen-2.5-7B"
    "models/whisper:Whisper-Large"
    "models/qwen3:Qwen3-TTS"
    "models/wav2lip:Wav2Lip-HQ"
)

for m in "${models[@]}"; do
    path="${m%%:*}"
    name="${m#*:}"
    if [ -d "$path" ]; then
        size=$(du -sh "$path" | cut -f1)
        echo "  - $name: ✅ FOUND ($size)"
    else
        echo "  - $name: ❌ MISSING"
    fi
done

# 3. Check Service Endpoints
echo "Checking Local Microservice Handshakes:"
services=(
    "8501:Streamlit UI"
    "8000:FastAPI Core"
    "8002:Synthesizer"
)

for s in "${services[@]}"; do
    port="${s%%:*}"
    name="${s#*:}"
    if curl -s "http://localhost:$port/health" > /dev/null || curl -s "http://localhost:$port" > /dev/null; then
        echo "  - $name: ✅ ONLINE"
    else
        echo "  - $name: ⚠️ UNREACHABLE (Check logs)"
    fi
done

echo "🚀 Neural Swarm Verification Complete!"
