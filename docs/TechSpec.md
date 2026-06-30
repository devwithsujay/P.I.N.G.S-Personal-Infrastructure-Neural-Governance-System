# P.I.N.G.S Core v2 — Technical Specification

## System Requirements

- **OS**: Debian 13 (Trixie) or compatible Linux
- **Docker**: 24.0+
- **Docker Compose**: v2.20+
- **RAM**: Minimum 4GB, recommended 8GB
- **Disk**: 20GB minimum for containers and data
- **Network**: Tailscale for remote access

## Service Specifications

### pings-core (FastAPI Brain)
| Property | Value |
|----------|-------|
| Image | Custom (Dockerfile.core) |
| Base | python:3.11-slim |
| Port | 8000 |
| Framework | FastAPI 0.115+ |
| Database | SQLite 3 (pings-data volume) |
| Vector DB | ChromaDB client |
| HTTP Client | httpx |
| Health | GET /api/status |

### pings-bot (Telegram Bot)
| Property | Value |
|----------|-------|
| Image | Custom (bot/Dockerfile) |
| Base | python:3.11-slim |
| Framework | aiogram 3.15+ |
| HTTP Client | httpx |
| Session | str(telegram_user.id) |
| Health | Process check |

### pings-web (React Dashboard)
| Property | Value |
|----------|-------|
| Image | nginx:alpine |
| Port | 80 (internal) |
| Build | Vite + React 18 |
| SPA | Yes (fallback to index.html) |

### pings-nginx (Reverse Proxy)
| Property | Value |
|----------|-------|
| Image | nginx:alpine |
| Ports | 80 (HTTP), 443 (HTTPS) |
| TLS | Self-signed or Let's Encrypt |
| Timeout | 300s (API), 10s (connect) |
| Rate Limit | 30 req/s per IP on /api/ |
| Max Upload | 50MB |

### pings-chroma (Vector Database)
| Property | Value |
|----------|-------|
| Image | chromadb/chroma:0.5.23 |
| Port | 8100 → 8000 |
| Volume | pings-chroma-data |
| Heartbeat | GET /api/v1/heartbeat |

### pings-searxng (Search Engine)
| Property | Value |
|----------|-------|
| Image | searxng/searxng:latest |
| Port | 8080 |
| Formats | HTML, JSON |
| Limiter | Disabled |
| Health | GET /healthz |

### pings-ntfy (Notifications)
| Property | Value |
|----------|-------|
| Image | binwiederhier/ntfy:v2 |
| Port | 8090 → 80 |
| Volume | pings-data |
| Health | GET /v1/health |

## AI Models

### Zen AI Models (via opencode)
| Model | ID | Context | Use Case |
|-------|----|---------|----------|
| MiMo V2.5 Free | opencode/mimo-v2.5-free | 128K | General (default) |
| DeepSeek V4 Flash Free | opencode/deepseek-v4-flash-free | 128K | Fast responses |
| Nemotron 3 Ultra Free | opencode/nemotron-3-ultra-free | 128K | Complex reasoning |
| Big Pickle | opencode/big-pickle | 128K | Creative tasks |
| North Mini Code Free | opencode/north-mini-code-free | 64K | Code generation |

### NVIDIA NIM (Vision)
| Property | Value |
|----------|-------|
| Model | nvidia/vila |
| Base URL | https://integrate.api.nvidia.com/v1 |
| Auth | Bearer token |
| Use | Image analysis only |

## Ports

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| pings-core | 8000 | 8000 |
| pings-nginx | 80 | 80 |
| pings-nginx | 443 | 443 |
| pings-chroma | 8100 | 8000 |
| pings-searxng | 8080 | 8080 |
| pings-ntfy | 8090 | 80 |

## Volumes

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| pings-data | /app/data | Core DB, ntfy cache |
| pings-chroma-data | /chroma/chroma | Vector embeddings |
| pings-workspace | /app/workspace | File operations |

## Network

| Network | Driver | Purpose |
|---------|--------|---------|
| pings-net | bridge | Inter-service communication |

## Environment Variables

See [`.env.example`](../.env.example) for the complete list. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| BRAIN_SECRET_KEY | Yes | — | API auth key |
| TELEGRAM_BOT_TOKEN | Yes | — | Bot token |
| NVIDIA_API_KEY | No | — | Vision API key |
| DEFAULT_ZEN_MODEL | No | opencode/mimo-v2.5-free | Starting model |
| SEARXNG_URL | No | http://pings-searxng:8080 | Search endpoint |
| NTFY_URL | No | http://pings-ntfy:80 | Notification endpoint |

## Build Commands

```bash
# Build all services
docker compose build

# Build specific service
docker compose build pings-core
docker compose build pings-bot

# Start all
docker compose up -d

# View logs
docker compose logs -f pings-core
docker compose logs -f pings-bot

# Restart specific service
docker compose restart pings-core

# Stop all
docker compose down

# Clean volumes (DESTROYS DATA)
docker compose down -v
```
