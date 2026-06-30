# P.I.N.G.S — Personal Infrastructure & Neural Governance System

A self-hosted AI assistant platform combining a Telegram bot, FastAPI brain, vector memory, web search, and a React dashboard — all orchestrated with Docker.

---

## Features

- **Telegram Bot** — Chat, upload photos/documents, switch AI models, run research queries
- **AI Brain (FastAPI)** — Intent classification, agent dispatch, conversation memory
- **Zen AI Models** — 5 selectable models via opencode (MiMo V2.5, DeepSeek V4, Nemotron 3, Big Pickle, North Mini)
- **Vision Support** — NVIDIA NIM for image analysis
- **Vector Memory** — ChromaDB for semantic search over conversation history
- **Web Search** — SearXNG self-hosted search engine
- **Notifications** — ntfy for alerts and research completion
- **Web Dashboard** — React frontend served via nginx
- **Reverse Proxy** — nginx with TLS, rate limiting, WebSocket support
- **Persona System** — Configurable AI personality and safety rules
- **SSH Remote Access** — Execute commands on remote machines via the bot

---

## Architecture

```
User
  ├── Telegram ──→ pings-bot ──→ pings-core (FastAPI)
  └── Browser  ──→ pings-nginx ──→ pings-web (React)
                                    pings-core (API)
                                        │
                        ┌───────────────┼───────────────┐
                        ▼               ▼               ▼
                    ChromaDB        SearXNG          ntfy
                    (vectors)       (search)      (notifs)
                                        │
                                    opencode
                                        │
                                ┌───────┴───────┐
                                ▼               ▼
                            Zen Models      NIM Vision
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full diagram.

---

## Quick Start

### Prerequisites
- Docker 24+
- Docker Compose v2
- A Telegram bot token (from @BotFather)
- An NVIDIA API key (for vision features)

### 1. Clone and configure
```bash
git clone https://github.com/devwithsujay/P.I.N.G.S-Personal-Infrastructure-Neural-Governance-System.git
cd pings-core-v2
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run setup
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Access
| Service | URL |
|---------|-----|
| API | http://localhost:8000/api/status |
| Web Dashboard | http://localhost |
| SearXNG | http://localhost:8080 |
| ChromaDB | http://localhost:8100 |
| ntfy | http://localhost:8090 |

### 4. Start chatting
Open Telegram, find your bot, and send `/start`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Bot | Python 3.11, aiogram 3 |
| Backend | Python 3.11, FastAPI, SQLite |
| AI | Zen AI (opencode), NVIDIA NIM |
| Vector DB | ChromaDB 0.5.23 |
| Search | SearXNG |
| Notifications | ntfy v2 |
| Frontend | React, Vite |
| Proxy | nginx (Alpine) |
| Containers | Docker Compose |

---

## Project Structure

```
pings-core-v2/
├── bot/                    # Telegram bot (aiogram)
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/                  # Reverse proxy config
│   └── nginx.conf
├── searxng/                # Search engine config
│   └── settings.yml
├── persona/                # AI persona files
│   ├── IDENTITY.md
│   ├── CONTEXT.md
│   ├── RULES.md
│   └── JOURNAL.md
├── scripts/                # Setup and utility scripts
│   └── setup.sh
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── PRD.md
│   ├── TechSpec.md
│   ├── AppFlow.md
│   ├── Schema.md
│   ├── ImplementationPlan.md
│   ├── Tracker.md
│   └── Rules.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Configuration

All configuration is done via environment variables in `.env`. See [`.env.example`](.env.example) for the full list.

Key variables:
- `TELEGRAM_BOT_TOKEN` — Your bot token
- `NVIDIA_API_KEY` — For vision features
- `BRAIN_SECRET_KEY` — Auto-generated, do not change after first run
- `DEFAULT_ZEN_MODEL` — Starting AI model

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design and data flow
- [Product Requirements](docs/PRD.md) — What we're building and why
- [Technical Spec](docs/TechSpec.md) — Versions, ports, and specs
- [Application Flow](docs/AppFlow.md) — Request lifecycle and agent dispatch
- [Database Schema](docs/Schema.md) — SQLite table definitions
- [Implementation Plan](docs/ImplementationPlan.md) — Phase-by-phase build plan
- [Build Tracker](docs/Tracker.md) — Current progress
- [Operational Rules](docs/Rules.md) — Safety and operational guidelines

---

## License

Private — for personal use only.
