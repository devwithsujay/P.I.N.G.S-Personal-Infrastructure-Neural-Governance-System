#!/usr/bin/env bash
# P.I.N.G.S Core v2 — Setup Script
# Run this on first deploy to initialize the environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== P.I.N.G.S Core v2 Setup ==="
echo ""

# ── 1. Check prerequisites ──────────────────────────────────────────────────
echo "[1/6] Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found. Install Docker first."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "ERROR: docker compose not found."; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "WARNING: openssl not found. TLS certs must be provided manually."; }

echo "  ✓ Docker: $(docker --version)"
echo "  ✓ Docker Compose: $(docker compose version)"

# ── 2. Generate .env if missing ─────────────────────────────────────────────
echo ""
echo "[2/6] Checking .env file..."

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "  .env not found. Copying from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"

    # Generate a random BRAIN_SECRET_KEY
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | od -An -tx1 | tr -d ' \n')
    sed -i "s/BRAIN_SECRET_KEY=.*/BRAIN_SECRET_KEY=$SECRET_KEY/" "$PROJECT_ROOT/.env"

    echo "  ✓ .env created with generated BRAIN_SECRET_KEY"
    echo "  ⚠ Edit .env to add your TELEGRAM_BOT_TOKEN and NVIDIA_API_KEY"
else
    echo "  ✓ .env already exists"
fi

# ── 3. Check SSH key ────────────────────────────────────────────────────────
echo ""
echo "[3/6] Checking SSH configuration..."

SSH_KEY_PATH=$(grep "^SSH_KEY_PATH=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "")
SSH_AUTH_TYPE=$(grep "^SSH_AUTH_TYPE=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "key")

if [ "$SSH_AUTH_TYPE" = "key" ] && [ -n "$SSH_KEY_PATH" ]; then
    if [ -f "$SSH_KEY_PATH" ]; then
        echo "  ✓ SSH key found at $SSH_KEY_PATH"
    else
        echo "  ⚠ SSH key not found at $SSH_KEY_PATH"
        echo "    Generate one with: ssh-keygen -t ed25519 -f $SSH_KEY_PATH"
    fi
else
    echo "  ℹ SSH auth type: $SSH_AUTH_TYPE"
fi

# ── 4. Generate self-signed TLS certs if missing ────────────────────────────
echo ""
echo "[4/6] Checking TLS certificates..."

CERTS_DIR="$PROJECT_ROOT/nginx/certs"
mkdir -p "$CERTS_DIR"

if [ ! -f "$CERTS_DIR/fullchain.pem" ] || [ ! -f "$CERTS_DIR/privkey.pem" ]; then
    echo "  TLS certs not found. Generating self-signed certs..."
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout "$CERTS_DIR/privkey.pem" \
        -out "$CERTS_DIR/fullchain.pem" \
        -subj "/CN=localhost/O=PINGS/C=US" \
        2>/dev/null || echo "  ⚠ Could not generate certs. Provide them manually in nginx/certs/"
    echo "  ✓ Self-signed certs generated"
else
    echo "  ✓ TLS certs found"
fi

# ── 5. Create workspace directory ───────────────────────────────────────────
echo ""
echo "[5/6] Setting up workspace..."

WORKSPACE="$PROJECT_ROOT/workspace"
mkdir -p "$WORKSPACE"
echo "  ✓ Workspace directory ready at $WORKSPACE"

# ── 6. Build and start ──────────────────────────────────────────────────────
echo ""
echo "[6/6] Building and starting containers..."

cd "$PROJECT_ROOT"
docker compose build --no-cache
docker compose up -d

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services:"
echo "  • P.I.N.G.S Core API:  http://localhost:8000"
echo "  • P.I.N.G.S Web:       http://localhost:80"
echo "  • P.I.N.G.S Bot:       (running, connect via Telegram)"
echo "  • SearXNG:             http://localhost:8080"
echo "  • ChromaDB:            http://localhost:8100"
echo "  • ntfy:                http://localhost:8090"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. docker compose restart pings-core pings-bot"
echo "  3. Test: curl http://localhost:8000/api/status"
