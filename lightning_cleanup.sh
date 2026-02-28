#!/bin/bash
# The "Nuclear Clean" script for Lightning AI
# Run this to clear up 18GB of ghost directory storage and prune credit-eating cache layers

echo "🧹 Stopping all stalled containers..."
docker stop $(docker ps -aq) 2>/dev/null

echo "🗑️ Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null

echo "🔥 Pruning the 'Credit Eaters' (unused images, networks, and anonymous volumes)..."
docker system prune -a --volumes -f

echo "✅ Cleanup complete. Checking available disk space:"
df -h
