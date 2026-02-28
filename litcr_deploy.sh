#!/usr/bin/env bash
set -e

# Configuration
LIGHTNING_API_KEY="b5efb1b0-95be-43f4-b10e-5263141672c0"
USERNAME="roshnis0238"
REGISTRY="litcr.io"
PROJECT_PATH="lit-container/roshnis0238/sonora-external-testing-project"
IMAGE_NAME="sonora"
LOCAL_IMAGE="sonora-unified:latest"

echo "🚀 Starting Sonora Deployment to Lightning Container Registry (LitCR)..."

# Step 1: Login
echo "📂 Logging in to LitCR..."
echo $LIGHTNING_API_KEY | docker login $REGISTRY --username=$USERNAME --password-stdin

# Step 2: Build
echo "🏗️ Building Sonora Unified image..."
docker build -f Dockerfile.unified -t $LOCAL_IMAGE .

# Step 3: Tag
echo "🏷️ Tagging image..."
REMOTE_IMAGE="$REGISTRY/$PROJECT_PATH/$IMAGE_NAME"
docker tag $LOCAL_IMAGE $REMOTE_IMAGE

# Step 4: Push
echo "📤 Pushing image to LitCR..."
docker push $REMOTE_IMAGE

echo "✨ Deployment complete! Image pushed to: $REMOTE_IMAGE"
