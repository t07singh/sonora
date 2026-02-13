#!/bin/bash
echo "🚢 SHIPPING SONORA: AI DUBBING STUDIO"
echo "======================================"

# 1. Build and Run
docker-compose up --build -d

# 2. Health Wait
echo "⏳ Waiting for Swarm Handshake..."
until $(curl --output /dev/null --silent --head --fail http://localhost:8501); do
    printf '.'
    sleep 2
done

echo ""
echo "✅ SONORA READY FOR STUDIO DEMO"
echo "📍 Access UI at http://localhost:8501"
echo "📍 API Documentation at http://localhost:8001/docs"
