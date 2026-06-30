#!/bin/bash
set -e

echo "[opencode-sidecar] Starting OpenCode server..."

ZEN_API_KEY="${ZEN_API_KEY:-}"
SERVER_PORT="${OPENCODE_SERVER_PORT:-4096}"

if [ -z "$ZEN_API_KEY" ]; then
    echo "[opencode-sidecar] WARNING: ZEN_API_KEY not set. Zen models will not be available."
    echo "[opencode-sidecar] Set ZEN_API_KEY in .env to enable Zen models."
fi

opencode serve --hostname 0.0.0.0 --port "$SERVER_PORT" &
SERVER_PID=$!

sleep 3

if [ -n "$ZEN_API_KEY" ]; then
    echo "[opencode-sidecar] Configuring Zen API key..."
    curl -s -X PUT "http://localhost:${SERVER_PORT}/auth/opencode" \
        -H "Content-Type: application/json" \
        -d "{\"type\": \"api\", \"key\": \"${ZEN_API_KEY}\"}" \
        && echo "[opencode-sidecar] Zen API key configured." \
        || echo "[opencode-sidecar] WARNING: Failed to configure Zen API key."
fi

echo "[opencode-sidecar] OpenCode server ready on port ${SERVER_PORT}"

wait $SERVER_PID
