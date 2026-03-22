#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# CyberShield — Cloudflare Tunnel Deployment Script
# Exposes the local/VPS Streamlit app via Cloudflare Tunnel
# Prerequisites: cloudflared CLI, Docker (optional)
# ─────────────────────────────────────────────────────────────

set -euo pipefail

APP_PORT="${APP_PORT:-8501}"
TUNNEL_NAME="${TUNNEL_NAME:-cybershield}"

echo "============================================"
echo "  CyberShield — Cloudflare Deployment"
echo "  App Port: ${APP_PORT}"
echo "  Tunnel:   ${TUNNEL_NAME}"
echo "============================================"

# ── Check Prerequisites ─────────────────────────────────────
if ! command -v cloudflared &> /dev/null; then
    echo "ERROR: cloudflared CLI not found."
    echo "Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    exit 1
fi

# ── Step 1: Build & Start App (Docker) ──────────────────────
echo ""
echo "[1/3] Building and starting CyberShield..."
if command -v docker &> /dev/null; then
    docker compose up --build -d
    echo "  Docker container started on port ${APP_PORT}"
else
    echo "  Docker not found — assuming app is already running on port ${APP_PORT}"
    echo "  Start manually: streamlit run app.py --server.port=${APP_PORT}"
fi

# ── Step 2: Authenticate Cloudflare (first time only) ───────
echo "[2/3] Checking Cloudflare authentication..."
if [ ! -f "$HOME/.cloudflared/cert.pem" ]; then
    echo "  First-time setup — opening browser for Cloudflare login..."
    cloudflared tunnel login
fi

# ── Step 3: Create & Run Tunnel ─────────────────────────────
echo "[3/3] Starting Cloudflare Tunnel..."

# Create tunnel if it doesn't exist
if ! cloudflared tunnel list | grep -q "${TUNNEL_NAME}"; then
    echo "  Creating tunnel '${TUNNEL_NAME}'..."
    cloudflared tunnel create "${TUNNEL_NAME}"
fi

echo ""
echo "  Starting tunnel → http://localhost:${APP_PORT}"
echo "  Configure DNS: cloudflared tunnel route dns ${TUNNEL_NAME} your-subdomain.yourdomain.com"
echo ""
echo "============================================"
echo "  To run the tunnel:"
echo "    cloudflared tunnel --url http://localhost:${APP_PORT} run ${TUNNEL_NAME}"
echo ""
echo "  For a quick public URL (no DNS config):"
echo "    cloudflared tunnel --url http://localhost:${APP_PORT}"
echo "============================================"

# Run tunnel (foreground — Ctrl+C to stop)
cloudflared tunnel --url "http://localhost:${APP_PORT}" run "${TUNNEL_NAME}"
