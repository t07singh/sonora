#!/usr/bin/env bash
set -euo pipefail

# Entrypoint for Sonora containers that ensures ports are free and starts supervisord.
# Usage: ./entrypoint.sh <preferred_port>
PREFERRED_PORT=${1:-8000}
MAX_TRIES=10
SLEEP_BETWEEN=0.5

find_free_port() {
  local port=$1
  for i in $(seq 0 $MAX_TRIES); do
    p=$((port + i))
    if ! ss -ltn "sport = :$p" >/dev/null 2>&1; then
      echo "$p"
      return 0
    fi
  done
  return 1
}

PORT=$(find_free_port $PREFERRED_PORT) || {
  echo "No free ports found near $PREFERRED_PORT"
  exit 1
}

export SONORA_PORT=$PORT
echo "Selected SONORA_PORT=$SONORA_PORT"

# write to env file for supervised processes to read
echo "SONORA_PORT=$SONORA_PORT" > /tmp/sonora_env.sh
chmod 600 /tmp/sonora_env.sh

# run supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

































