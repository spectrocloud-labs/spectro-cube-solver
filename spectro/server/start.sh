#!/bin/sh

# Start Mosquitto in the background
mosquitto -c /etc/mosquitto/conf.d/bus.conf &

# Start Python backend (REST API & WebSocket)
python /app/backend/main.py &

# Start Nginx in the foreground
nginx -g "daemon off;"
