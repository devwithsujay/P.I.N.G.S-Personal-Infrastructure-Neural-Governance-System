# P.I.N.G.S Core v2 — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                     │
│                                                                             │
│   ┌──────────────┐          ┌──────────────┐                               │
│   │   Telegram    │          │   Browser    │                               │
│   │   (Bot API)   │          │   (React)    │                               │
│   └──────┬───────┘          └──────┬───────┘                               │
└──────────┼─────────────────────────┼────────────────────────────────────────┘
           │                         │
           ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EDGE LAYER                                        │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                  pings-nginx (nginx:alpine)               │             │
│   │               Ports: 80 (HTTP) → 443 (HTTPS)             │             │
│   │                                                           │             │
│   │   /api/*  ──────→  pings-core:8000                       │             │
│   │   /ws/*   ──────→  pings-core:8000  (WebSocket)          │             │
│   │   /*      ──────→  pings-web:80     (React SPA)          │             │
│   └──────────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
           │                                           │
           ▼                                           ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│     pings-bot            │          │      pings-web           │
│   (Python 3.11)          │          │    (nginx:alpine)        │
│   aiogram 3 + httpx      │          │    React + Vite dist     │
│                          │          │                          │
│   • /start /clear        │          │   • Dashboard UI         │
│   • /model (5 models)    │          │   • Status page          │
│   • /research            │          │   • Chat interface        │
│   • photo/doc upload     │          │   • Settings             │
│   • free text → classify │          │                          │
│                          │          │                          │
│   Session: user_id str   │          │                          │
└──────────┬───────────────┘          └──────────────────────────┘
           │
           │ http://pings-core:8000
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CORE LAYER                                        │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │               pings-core (FastAPI)                        │             │
│   │               Port: 8000                                  │             │
│   │                                                           │             │
│   │   /api/status          GET  — health + uptime            │             │
│   │   /api/chat/message    POST — free text → classify       │             │
│   │   /api/chat/upload     POST — photo/document → process   │             │
│   │   /api/chat/clear      POST — clear session history      │             │
│   │   /api/chat/history    GET  — retrieve conversation      │             │
│   │   /api/model/current   GET  — current model              │             │
│   │   /api/model/set       POST — switch model               │             │
│   │   /api/research/start  POST — create research run        │             │
│   │   /api/tasks/list      GET  — active tasks               │             │
│   │                                                           │             │
│   │   ┌─────────────────────────────────────────────────┐    │             │
│   │   │              Intent Classifier                   │    │             │
│   │   │  message → classify → route to agent             │    │             │
│   │   │                                                  │    │             │
│   │   │  Agents:                                        │    │             │
│   │   │  • chat_agent     — conversation                │    │             │
│   │   │  • code_agent     — coding tasks                │    │             │
│   │   │  • research_agent — web research                │    │             │
│   │   │  • devops_agent   — infrastructure              │    │             │
│   │   │  • vision_agent   — image analysis              │    │             │
│   │   └─────────────────────────────────────────────────┘    │             │
│   └───────────────────────────┬──────────────────────────────┘             │
│                               │                                             │
└───────────────────────────────┼─────────────────────────────────────────────┘
                                │
              ┌─────────────────┼──────────────────────┐
              ▼                 ▼                       ▼
┌─────────────────────┐ ┌────────────────┐  ┌────────────────────┐
│    pings-chroma      │ │  pings-searxng │  │    pings-ntfy      │
│  (ChromaDB 0.5.23)   │ │  (SearXNG)     │  │  (binwiederhier/   │
│  Port: 8100→8000     │ │  Port: 8080     │  │   ntfy:v2)         │
│                      │ │                │  │  Port: 8090→80     │
│  • Vector storage    │ │  • Web search  │  │                    │
│  • Semantic search   │ │  • JSON API    │  │  • Push notifs     │
│  • Embeddings        │ │  • No rate lim │  │  • Research alerts │
│                      │ │                │  │                    │
│  Volume:             │ │  Config:       │  │  Volume:           │
│   pings-chroma-data  │ │   settings.yml │  │   pings-data       │
└─────────────────────┘ └────────────────┘  └────────────────────┘
                                │
                                ▼
              ┌─────────────────────────────────┐
              │         opencode (AI)            │
              │                                  │
              │  ┌──────────────────────────┐   │
              │  │     Zen AI Models         │   │
              │  │                           │   │
              │  │  • MiMo V2.5 Free ★       │   │
              │  │  • DeepSeek V4 Flash Free │   │
              │  │  • Nemotron 3 Ultra Free  │   │
              │  │  • Big Pickle             │   │
              │  │  • North Mini Code Free   │   │
              │  └──────────────────────────┘   │
              │                                  │
              │  ┌──────────────────────────┐   │
              │  │    NVIDIA NIM (Vision)    │   │
              │  │    Model: nvidia/vila     │   │
              │  └──────────────────────────┘   │
              └─────────────────────────────────┘
```

## Data Flow

### 1. Telegram Message Flow
```
User sends message
  → Telegram Bot API receives it
  → pings-bot (aiogram) processes it
    → Session ID = str(user.id)
    → Free text: POST /api/chat/message
    → Photo/Document: POST /api/chat/upload
    → Commands handled locally (/start, /clear, /model, etc.)
  → pings-core receives request
    → Intent classifier determines agent
    → Agent executes task (chat, code, research, devops, vision)
    → Response generated using current model
    → History stored in SQLite
    → Vectors stored in ChromaDB
  → Response returned to bot
  → Bot sends reply to user
```

### 2. Web Dashboard Flow
```
User opens browser
  → Request hits pings-nginx:80
  → Redirects to HTTPS (443)
  → /api/* → proxied to pings-core:8000
  → /* → served from pings-web:80 (React SPA)
  → React app makes API calls to /api/*
```

### 3. Research Flow
```
User: /research <topic>
  → Bot sends POST /api/research/start
  → pings-core creates research run
  → Research agent:
    1. Generates search queries from topic
    2. Searches via SearXNG API
    3. Fetches and summarizes results
    4. Stores findings in ChromaDB
    5. Compiles report
    6. Sends notification via ntfy
  → Bot notifies user of completion
```

## Network Topology

All services communicate over the `pings-net` Docker bridge network:

| Service | Internal URL | External Port |
|---------|-------------|---------------|
| pings-core | http://pings-core:8000 | 8000 |
| pings-bot | (no HTTP server) | — |
| pings-web | http://pings-web:80 | — |
| pings-nginx | — | 80, 443 |
| pings-chroma | http://pings-chroma:8000 | 8100 |
| pings-searxng | http://pings-searxng:8080 | 8080 |
| pings-ntfy | http://pings-ntfy:80 | 8090 |

## Volumes

| Volume | Purpose |
|--------|---------|
| pings-data | Core data, ntfy cache, SQLite DB |
| pings-chroma-data | ChromaDB vector storage |
| pings-workspace | Shared workspace for file operations |
