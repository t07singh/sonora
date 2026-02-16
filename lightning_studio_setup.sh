#!/usr/bin/env bash
set -e

echo "🚀 Starting Lightning AI Studio Kickstart for Sonora..."

# Step 1: Force-Start Docker and Set Permissions
echo "🔧 Configuring Docker daemon..."
sudo service docker start || echo "Docker already running"
sudo chmod 666 /var/run/docker.sock

# Step 2: Fix Windows Line Endings (if any)
echo "🧹 Fixing file formats..."
sudo apt-get update && sudo apt-get install -y dos2unix
find . -name "*.sh" -exec dos2unix {} +
find . -name "*.yml" -exec dos2unix {} +
find . -name "Dockerfile*" -exec dos2unix {} +

# Step 3: Diagnostic - Verify Dockerfile Locations
echo "🔍 Verifying Dockerfile paths..."
MISSING=0
for f in "src/cockpit/Dockerfile" "src/services/transcriber/Dockerfile" "src/services/synthesizer/Dockerfile" "src/services/separator/Dockerfile" "src/services/lipsync_service/Dockerfile"; do
    if [ ! -f "$f" ]; then
        echo "❌ MISSING: $f"
        MISSING=$((MISSING + 1))
    else
        echo "✅ FOUND: $f"
    fi
done

if [ $MISSING -gt 0 ]; then
    echo "⚠️ Warning: Some Dockerfiles are missing. Build may fail."
fi

# Step 4: Launch Swarm
echo "🎬 Launching Sonora Swarm..."
docker compose -f docker-compose-1.yml up --build -d

echo "✨ Deployment started in background."
echo "📜 Run 'docker compose -f docker-compose-1.yml logs -f' to see logs."
echo "🌐 Remember to expose port 8501 via the Port Viewer plugin!"
