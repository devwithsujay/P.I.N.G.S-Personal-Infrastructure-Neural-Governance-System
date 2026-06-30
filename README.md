# P.I.N.G.S — Personal Infrastructure & Neural Governance System

A self-hosted AI assistant platform that runs entirely on your own hardware —
Telegram bot, FastAPI brain, vector memory, private web search, and a React
dashboard, all orchestrated with Docker. No SaaS subscriptions, no third-party
data harvesting, no cloud dependency beyond an optional API key for vision.

```
───────────────────────────────────────────────
   P.I.N.G.S — your homelab, with a brain
───────────────────────────────────────────────
```

---

## Why this exists

Most AI assistants either run entirely in someone else's cloud or require you
to babysit a local model server. P.I.N.G.S takes a third path: an agent that
knows your infrastructure, speaks in your voice, and runs free models by
default — with a clear, optional upgrade path to a stronger model when a task
actually needs it.

It's not a chatbot wrapper. It's a digital twin that can SSH into your
homelab, debug a downed container, write a structured research report,
scaffold a project, track your tasks, and check in on you proactively — all
while respecting a hard-coded safety layer that gates destructive actions
behind explicit confirmation.

---

## Features

- **Telegram bot** — chat, upload photos/documents, switch AI models mid-
  conversation, kick off research from your phone
- **FastAPI brain** — intent classification, agent dispatch, persistent
  conversation memory
- **5 free AI models, one switch** — MiMo V2.5, DeepSeek V4 Flash, Nemotron 3
  Ultra, Big Pickle, and North Mini Code, all via opencode, swappable from the
  dashboard or `/model` in Telegram — no API key required for any of them
- **Vision support** — NVIDIA NIM for image and document analysis when you
  need a stronger multimodal model
- **Vector memory** — ChromaDB with local ONNX embeddings (fastembed) for
  semantic recall over past conversations — fully offline, no embedding API
- **Private web search** — SearXNG, self-hosted, with DuckDuckGo fallback —
  no search queries ever leave your network
- **Multi-mode deep research** — product, compare, how-to, and fact-check
  research templates, each producing a structured report with sources;
  fact-check mode includes confidence/agreement scoring
- **Mission Control dashboard** — live status cards per agent, a real-time
  journal feed of everything the system has done, and a memory-recall panel
- **Proactive monitoring** — scheduled homelab health checks and task
  reminders, pushed via Telegram and ntfy
- **Persona system** — your identity, current context, and operational
  safety rules live in plain markdown files the agent reads on every request
  and hot-reloads on edit — no redeploy needed to update what it knows
- **Safety-gated automation** — a `RULES.md`-driven confirmation layer that
  blocks destructive shell/Docker/git actions until you explicitly approve
  them, enforced in code, not just prompted for
- **SSH remote access** — execute and reason over commands on remote
  machines via the bot, with the same safety gate applied
- **PWA dashboard** — installable on mobile, 5 selectable color themes
- **Reverse proxy** — nginx with TLS (mkcert-friendly for LAN/Tailscale),
  WebSocket support, rate limiting

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
                            Zen models      NIM vision
                          (free, default)   (optional)
```

Every container is self-hosted. The only outbound API call in the default
configuration is to opencode's free Zen model tier; NVIDIA NIM is opt-in,
used only for vision and any task you explicitly route to it.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full diagram and
data flow.

---

## Quick start

### Prerequisites
- Docker 24+
- Docker Compose v2
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- An NVIDIA API key — optional, only needed for vision/image analysis

### 1. Clone and configure
```bash
git clone https://github.com/<your-username>/pings-core.git
cd pings-core
cp .env.example .env
# Edit .env with your Telegram bot token and (optionally) your NVIDIA API key
```

### 2. Run setup
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The script checks for Docker, generates a secret key if missing, builds all
containers, and runs a health check on first boot.

### 3. Access

| Service | URL |
|---|---|
| Web dashboard | `http://localhost` |
| API health check | `http://localhost:8000/api/status` |
| SearXNG | `http://localhost:8080` |
| ChromaDB | `http://localhost:8100` |
| ntfy | `http://localhost:8090` |

### 4. Start chatting

Open Telegram, find your bot, send `/start`. Or open the web dashboard and
start typing — both interfaces share the same conversation memory.

---

## Tech stack

| Layer | Technology |
|---|---|
| Bot | Python 3.11, aiogram 3 |
| Backend | Python 3.11, FastAPI, SQLite |
| Agent engine | opencode |
| AI models | Zen free tier (5 models) + NVIDIA NIM (vision, optional) |
| Vector DB | ChromaDB 0.5.x, fastembed (ONNX, local) |
| Search | SearXNG |
| Notifications | ntfy |
| Frontend | React, Vite, Tailwind |
| Proxy | nginx (Alpine) |
| Containers | Docker Compose |

---

## Project structure

```
pings-core/
├── bot/                    # Telegram bot (aiogram)
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── core/                   # FastAPI brain
│   ├── main.py
│   ├── agents/              # Per-intent agent logic
│   ├── tools/                # SSH, browser, file, n8n tools
│   ├── memory/                # SQLite + ChromaDB
│   └── persona/                 # Persona loader + hot-reload
├── web/                     # React dashboard
├── nginx/                   # Reverse proxy config
│   └── nginx.conf
├── searxng/                  # Search engine config
│   └── settings.yml
├── persona/                  # Your AI's identity, in plain markdown
│   ├── IDENTITY.md             # Static facts — who you are, your stack
│   ├── CONTEXT.md               # Living context — edit this as things change
│   ├── RULES.md                  # Operational safety rules
│   └── JOURNAL.md                 # Append-only log the agent writes to
├── scripts/                  # Setup and utility scripts
│   └── setup.sh
├── docs/                      # Documentation
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

All configuration is done via environment variables in `.env`. See
[`.env.example`](.env.example) for the full list with comments.

Key variables:

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Your bot token from BotFather |
| `TELEGRAM_ALLOWED_USER_ID` | Yes | Restricts the bot to your Telegram user ID |
| `NVIDIA_API_KEY` | No | Only needed for vision/image analysis |
| `BRAIN_SECRET_KEY` | Auto-generated | Used for internal API auth — do not change after first run |
| `DEFAULT_ZEN_MODEL` | No | Starting AI model, switchable at runtime |
| `SSH_HOST` / `SSH_USER` | For homelab features | Target server for the HomeLab agent |

---

## The persona system

Your assistant's identity isn't buried in code — it's four plain markdown
files you can read and edit directly:

- **IDENTITY.md** — who you are, your tone, your stack, rarely changes
- **CONTEXT.md** — what's true right now (current projects, priorities) —
  meant to be hand-edited often, re-read on every request
- **RULES.md** — hard safety constraints (what requires confirmation before
  the agent will act, what it should never do)
- **JOURNAL.md** — append-only, the agent writes here after significant
  actions, giving you a transparent audit trail

This is the core design philosophy: the agent's behavior should be legible
and editable by you, not a black box tuned by prompt engineering buried
three files deep.

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — system design and data flow
- [Product Requirements](docs/PRD.md) — what we're building and why
- [Technical Spec](docs/TechSpec.md) — versions, ports, and specs
- [Application Flow](docs/AppFlow.md) — request lifecycle and agent dispatch
- [Database Schema](docs/Schema.md) — SQLite table definitions
- [Implementation Plan](docs/ImplementationPlan.md) — phase-by-phase build plan
- [Build Tracker](docs/Tracker.md) — current progress
- [Operational Rules](docs/Rules.md) — safety and operational guidelines

---

## Status

Actively developed, personal-use project. See
[docs/Tracker.md](docs/Tracker.md) for the current build status — this
project tracks its own completion percentage and known issues openly rather
than presenting a polished facade.

---

## License

Private — for personal use only.
