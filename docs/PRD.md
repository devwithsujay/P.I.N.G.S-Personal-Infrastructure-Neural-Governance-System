# P.I.N.G.S Core v2 — Product Requirements Document

## Overview

P.I.N.G.S Core v2 is a self-hosted personal AI infrastructure that provides a unified interface for AI-assisted coding, research, system administration, and automation through Telegram and a web dashboard.

## Problem Statement

Managing a homelab and personal projects requires juggling multiple tools, contexts, and interfaces. There is no single system that:
- Provides AI assistance across all domains (coding, DevOps, research)
- Integrates with existing infrastructure (Docker, SSH, Tailscale)
- Offers persistent memory and context
- Is self-hosted and privacy-respecting
- Can be accessed from anywhere (Telegram + web)

## Goals

1. **Unified Interface** — One bot for chat, coding, research, DevOps, and system administration
2. **Model Flexibility** — Switch between AI models based on task requirements
3. **Persistent Memory** — Vector-based conversation history for context retention
4. **Self-Hosted** — All data stays on the owner's infrastructure
5. **Mobile-First** — Telegram as the primary mobile interface
6. **Web Dashboard** — Desktop interface for monitoring and configuration

## Target User

- **Primary**: Sujay (CS student, homelab operator, developer)
- **Secondary**: Future self — building infrastructure for long-term use

## Features

### P0 — Core (Must Have)

| Feature | Description |
|---------|-------------|
| Telegram Bot | aiogram 3 bot with command handling and free text |
| Intent Classification | Route messages to appropriate agents |
| AI Brain | FastAPI backend with agent dispatch |
| Model Selection | Switch between 5 Zen AI models via /model |
| Chat History | Persistent conversation history per session |
| File Upload | Accept photos and documents via Telegram |
| Docker Deployment | Full Docker Compose stack |

### P1 — Important (Should Have)

| Feature | Description |
|---------|-------------|
| Vector Memory | ChromaDB for semantic search over history |
| Web Search | SearXNG integration for research |
| Research Agent | Multi-step research with SearXNG + summarization |
| Notifications | ntfy alerts for research completion |
| Web Dashboard | React frontend for status and monitoring |
| TLS Termination | nginx with HTTPS |

### P2 — Nice to Have

| Feature | Description |
|---------|-------------|
| Vision Analysis | NVIDIA NIM for image understanding |
| SSH Remote Access | Execute commands on remote machines |
| Task Management | Track and manage ongoing tasks |
| Persona System | Configurable AI personality |
| Journal | Auto-maintained log of actions and decisions |
| Proactive Agent | Periodic background tasks |

## Model Selection

Users can switch between 5 Zen AI models:

| Model | ID | Best For |
|-------|----|----------|
| MiMo V2.5 Free ⭐ | opencode/mimo-v2.5-free | General purpose (default) |
| DeepSeek V4 Flash Free | opencode/deepseek-v4-flash-free | Fast responses |
| Nemotron 3 Ultra Free | opencode/nemotron-3-ultra-free | Complex reasoning |
| Big Pickle | opencode/big-pickle | Creative tasks |
| North Mini Code Free | opencode/north-mini-code-free | Code generation |

## Success Metrics

- Bot responds to all commands correctly
- Model switching works within 2 seconds
- Research runs complete within 60 seconds
- Web dashboard loads in under 3 seconds
- 99% uptime for core services
- Zero data loss for conversation history

## Constraints

- Self-hosted on Debian 13 homelab
- All services containerized with Docker
- Telegram as primary interface (must work on mobile)
- Budget: $0 for AI models (free tier only)
- Must work over Tailscale for remote access

## Out of Scope

- Multi-user support (single owner only)
- Voice messages / audio processing
- Video analysis
- Social media integration
- Mobile app (Telegram bot is sufficient)
