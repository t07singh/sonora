#!/usr/bin/env bash
set -e
source /tmp/sonora_env.sh
API_PORT=${SONORA_PORT}
UI_PORT=$((SONORA_PORT+1))
sed -e "s/{{API_PORT}}/${API_PORT}/g" -e "s/{{UI_PORT}}/${UI_PORT}/g" /deploy/nginx.template.conf > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'

































