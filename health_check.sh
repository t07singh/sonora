#!/usr/bin/env bash
set -e
HOST=${1:-http://localhost:80}
HEALTH=$(curl -s $HOST/health | jq -r '.status')
if [ "$HEALTH" != "ok" ]; then
  echo "Unhealthy: restarting api"
  docker restart sonora_api
fi



































