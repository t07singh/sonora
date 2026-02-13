#!/bin/bash
# onboard_customer.sh - Sonora B2B Onboarding Utility
# v1.1.0 (Production)

set -e

echo "------------------------------------------------"
echo "🎨 SONORA B2B: CUSTOMER ONBOARDING"
echo "------------------------------------------------"

if [ -z "$1" ]; then
    echo "Usage: ./onboard_customer.sh <customer_name>"
    exit 1
fi

CUSTOMER_NAME=$1
CUSTOMER_ID=$(echo $CUSTOMER_NAME | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
INSTANCE_DIR="deployments/$CUSTOMER_ID"
DATA_DIR="/var/lib/sonora/$CUSTOMER_ID"

echo "➡️  Onboarding: $CUSTOMER_NAME (ID: $CUSTOMER_ID)"

# 1. Hardware Pre-Flight Check
echo "🔍 Checking hardware readiness..."

HAS_GPU=true
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  NVIDIA GPU not detected via nvidia-smi."
    HAS_GPU=false
fi

if ! docker info 2>/dev/null | grep -i nvidia &> /dev/null; then
    echo "⚠️  NVIDIA Docker Toolkit not detected in Docker runtime."
    HAS_GPU=false
fi

if [ "$HAS_GPU" = false ]; then
    echo "❌ WARNING: This instance will run in CPU-Legacy mode (Slow)."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "🚪 Aborting onboarding."
        exit 1
    fi
else
    echo "✅ Hardware Ready: NVIDIA GPU & Toolkit detected."
fi

# 2. Create Deployment and Data isolation
mkdir -p "$INSTANCE_DIR"
sudo mkdir -p "$DATA_DIR"
sudo chown $USER:$USER "$DATA_DIR"

# 2. Generate Secure API Key
SONORA_KEY=$(openssl rand -hex 24)
echo "✅ Generated secure API key: $SONORA_KEY"

# 3. Create .env from template
cat > "$INSTANCE_DIR/.env" << EOL
# SONORA PRODUCTION CONFIG - $CUSTOMER_NAME
SONORA_API_KEY=$SONORA_KEY
SONORA_CUSTOMER_ID=$CUSTOMER_ID
SONORA_DATA_DIR=/app/sonora/data
LOG_LEVEL=INFO
EOL

# Collect existing keys if any, otherwise prompt
if [ -f .env ]; then
    source .env
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$INSTANCE_DIR/.env"
    echo "ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY" >> "$INSTANCE_DIR/.env"
    echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> "$INSTANCE_DIR/.env"
else
    echo "⚠️  Global .env not found. Please add provider keys to $INSTANCE_DIR/.env manualy later."
fi

# 4. Copy Docker Compose but adjust for isolation
cp docker-compose.prod.yml "$INSTANCE_DIR/"

# 5. Launch the Appliance
echo "🚀 Launching instance for $CUSTOMER_NAME..."
cd "$INSTANCE_DIR"
docker compose -p "sonora-$CUSTOMER_ID" up -d

# 6. Verify Service Health
echo "📡 Verifying API connectivity (waiting 10s)..."
sleep 10
HEALTH_CHECK=$(curl -s -X GET "http://localhost:8000/health" -H "X-Sonora-Key: $SONORA_KEY")

if echo "$HEALTH_CHECK" | grep -q '"status":"ok"'; then
    echo "✅ System Healthy: Orchestrator is online."
else
    echo "❌ Health check failed or returned unexpected status."
    echo "   Response: $HEALTH_CHECK"
    echo "   Check logs with: docker compose -p sonora-$CUSTOMER_ID logs sonora-api"
fi

echo ""
echo "------------------------------------------------"
echo "✨ ONBOARDING COMPLETE!"
echo "Customer:    $CUSTOMER_NAME"
echo "Service URL: http://localhost:8501 (Port may need mapping)"
echo "API Key:     $SONORA_KEY"
echo "Deploy Dir:  $INSTANCE_DIR"
echo "Data Dir:    $DATA_DIR"
echo "------------------------------------------------"
