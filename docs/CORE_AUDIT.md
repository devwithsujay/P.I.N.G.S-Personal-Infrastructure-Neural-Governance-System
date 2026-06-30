# P.I.N.G.S Core v2 — Audit Report

**Date:** 2026-06-23  
**Auditor:** opencode  
**Version:** 2.0.0

---

## Overall Health

P.I.N.G.S Core v2 is **structurally sound** — all 8 containers run, the FastAPI core boots, opencode sidecar responds, and the web dashboard loads. However, **ChromaDB vector memory is completely broken** (embedding model name mismatch), the **Tasks agent lies about creating tasks** (no SQLite write), and the **CodeGen agent doesn't actually write files**. These are functional failures masked by successful HTTP responses. The system appears to work but doesn't persist data where it matters.

---

## Pre-Flight

### Container Status

All 8 containers UP and healthy:

| Container | Status | Health |
|-----------|--------|--------|
| pings-core | Up 5min | healthy |
| pings-opencode | Up 5min | healthy |
| pings-bot | Up 5min | running (no healthcheck) |
| pings-web | Up 5min | running (no healthcheck) |
| pings-nginx | Up 5min | healthy |
| pings-chroma | Up 5min | healthy |
| pings-searxng | Up 5min | healthy |
| pings-ntfy | Up 5min | healthy |

### opencode Model IDs

Exact model IDs as listed by `opencode models`:

```
opencode/big-pickle
opencode/deepseek-v4-flash-free
opencode/mimo-v2.5-free
opencode/nemotron-3-ultra-free
opencode/north-mini-code-free
```

**All 5 match** what's hardcoded in `bot/main.py:19-25` and `main.py` `/models` endpoint. ✅

### .env Completeness

Missing from `.env` vs `.env.example`:
- `SEARXNG_URL` — set in .env as `http://pings-searxng:8081` (port 8081 on host, but config.py default is `:8080` internal). Container-to-container uses `:8080` ✅
- `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_AUTH_TYPE`, `SSH_KEY_PATH`, `SSH_PASSWORD` — all configured via UI, stored in SQLite. `.env` has no SSH vars (correct — UI-driven). ✅

---

## Section 1 — FastAPI Core

### 1.1 Startup

- Container starts without Python exceptions. ✅
- `GET /health` returns 200 with `{"status":"ok","services":{"api":"healthy","chroma":"healthy","scheduler":"running"}}`. ✅
- **Startup logs show repeated ChromaDB errors:** `Model all-MiniLM-L6-v2 is not supported in TextEmbedding` — this is the embedding model name mismatch. Non-fatal for boot (caught in try/except) but **fatal for all vector operations**.

### 1.2 Persona Loading

- All 4 files exist in `/app/persona/`: IDENTITY.md, CONTEXT.md, RULES.md, JOURNAL.md. ✅
- `build_system_prompt()` at `loader.py:62-83` correctly concatenates identity + context + rules. ✅
- Hot-reload: `watch_persona_files()` at `loader.py:86-117` is defined but **never started in lifespan** (`main.py:63-81`). The watcher thread is dead code — `startup_event()` calls `load_persona()` once and caches it, but never calls `watch_persona_files()`.

### 1.3 Auth

- `verify_api_key()` at `main.py:100-109` — **always returns True** (line 109: `return True`). Auth is completely disabled. Every endpoint is open.
- `/health` at `main.py:112` has no auth dependency. ✅
- `/models` at `main.py` — no auth dependency (public). Acceptable for model listing.

### 1.4 opencode Integration

- **Call site:** `opencode_engine.py:66-102` — `run_opencode_task()` creates HTTP sessions via `httpx.AsyncClient` to `OPENCODE_SERVER_URL` (http://pings-opencode:4096).
- **opencode NOT installed in pings-core** — it's a separate sidecar container. ✅ (correct architecture)
- **Non-interactive mode:** Creates session via `POST /session`, sends prompt via `POST /session/{id}/message`. Confirmed working — test returned `PING`. ✅
- **Health check:** `_check_health()` at `opencode_engine.py:12-18` verifies sidecar is up before each call. ✅

### 1.5 Model Switcher

- `GET /models` returns 5 models with correct IDs. ✅
- `POST /models/default` persists to SQLite settings table. ✅ (confirmed: setting survives container restart)
- Model flows through: `chat()` → `dispatch(model=)` → `run_opencode_task(model=)` → `_send_prompt(model=)`. ✅

### 1.6 Intent Classification

Regex-based scoring at `router.py:38-54`. Test results:

| Phrase | Got | Expected | Status |
|--------|-----|----------|--------|
| "is n8n running" | qa | homelab | ❌ FAIL |
| "create a VTU report for X" | report | report | ✅ |
| "scaffold a FastAPI project" | qa | codegen | ❌ FAIL |
| "research quantum computing" | research | research | ✅ |
| "add task submit ML by Friday" | tasks | tasks | ✅ |
| "what is a transformer model" | browse | qa | ❌ FAIL |
| "what containers are currently running" | homelab | homelab | ✅ |
| "docker stop pings-nginx" | homelab | homelab | ✅ |

**3/8 misroutes.** The `browse` intent's `what\s+is` pattern (router.py:33) overrides `qa` for question-style queries. `codegen` patterns are too weak — "scaffold" and "project" don't match any codegen regex. `homelab` needs "n8n" or "running" patterns.

---

## Section 2 — Agents

### 2.1 HomeLab Agent

- **Test:** "what containers are currently running" → homelab intent, SSH connection attempted.
- SSH fails: `[Errno -2] Name or service not known` — no real server configured. **Graceful failure** — error returned to user without crash. ✅
- `is_action_safe()` check at `system.py:33` properly blocks `docker stop`. ✅

### 2.2 Q&A Agent

- **Test:** "what is the difference between ChromaDB and SQLite" → classified as `browse` (not `qa`).
- SearXNG search fires, returns results. Response is raw search output — **no opencode synthesis step**. The `browse` intent in `router.py:78-85` just calls `web_search(query)` directly without LLM processing.
- **ChromaDB recall never fires** — `qa` intent not reached, so no memory injection.

### 2.3 Tasks Agent

- **Test:** "add task finish audit report due tomorrow college" → classified as `tasks`.
- Response: "Got it. Added high-priority task..." — but **no task was actually inserted into SQLite**. The tasks intent at `router.py:64-67` just calls `run_opencode_task()` which sends text to opencode. opencode generates a text response but has no tool to write to SQLite.
- **SQLite tasks table is empty** after the call. ❌ CRITICAL — task creation is a lie.

### 2.4 CodeGen Agent

- **Test:** "scaffold a minimal FastAPI hello world project" → classified as `qa` (not `codegen`).
- **Misroute** — codegen agent never invoked. Even if it were, `codegen.py:26-31` calls `run_opencode_task()` which doesn't have file-write tools. No files created in `/app/workspace/`.
- `/app/workspace/` is empty after the call. ❌

### 2.5 Report Agent

- **Test:** Not live-tested (would require NIM credits for full report generation).
- `report.py:26-30` calls `run_opencode_task()` with `tools=["files"]` hint — but opencode sidecar has no file-write tool. Report text generated but **not saved to disk**. ⚠️

### 2.6 Research Agent

- `research.py:120-151` decomposes topic, runs SearXNG searches, synthesizes report.
- HTML report generation at `research.py:71-109` uses xhtml2pdf. ✅
- Reports not saved to `/app/workspace/research/` — `run_research()` returns markdown but doesn't call `write_file()`. ⚠️

### 2.7 Vision Agent

- `chat_upload()` at `main.py:151-173` accepts multipart form with file. ✅
- Routes through `dispatch()` which goes to opencode — **no direct NIM call** for vision. Image content decoded as text (UTF-8 with replace), not sent to vision model. ❌ MODEL_VISION defined in config but never used.

---

## Section 3 — Safety

### 3.1 Layer 1 — RULES.md in System Prompt

- `build_system_prompt()` at `loader.py:71-72` includes rules section. ✅
- RULES.md content includes destructive operation confirmation, secrets handling, SSH safety, file sandbox. ✅

### 3.2 Layer 2 — Pre-execution Check

- `is_action_safe()` at `security.py:39-54` checks both `DANGER_PATTERNS` and `CONFIRM_BEFORE` regex. ✅
- Called at `system.py:33` before `control_container()`. ✅
- **Live test:** "docker stop pings-nginx" → "Action blocked: Requires confirmation: matches pattern 'docker\\s+stop\\s+'" — correctly blocked. ✅
- **However:** The homelab agent at `homelab.py:24-29` does NOT call `is_action_safe()` before passing to `control_container()`. Safety check only happens inside `control_container()` at `system.py:33`. This works but is fragile — any new caller could bypass it.

### 3.3 RULES.md Content

- CONFIRM_BEFORE items present: `rm -rf`, `docker stop/rm/kill`, `apt remove/purge`, `shutdown`, `reboot`. ✅
- **Missing from CONFIRM_BEFORE:** `git push --force` (mentioned in audit spec but not in RULES.md or security.py). ⚠️
- HONESTY rule: Not explicitly present (no "don't fabricate SSH output" rule). ⚠️
- ESCALATION rule: Not present (no "stop retrying after N failures"). ⚠️

---

## Section 4 — Memory

### 4.1 SQLite

- Tables confirmed: `conversations`, `tasks`, `agent_runs`, `settings`, `research_runs`, `memory_entries`, `scheduled_tasks`, `agents`. ✅
- `settings` table holds model default. ✅

### 4.2 ChromaDB

- Container healthy. ✅
- Client connects via HTTP (`chroma.py`). ✅
- **Embedding model BROKEN:** `config.py:61` sets `EMBEDDING_MODEL="all-MiniLM-L6-v2"` but fastembed requires `"sentence-transformers/all-MiniLM-L6-v2"`. Every `add_knowledge()` and `search_knowledge()` call fails with `400 Bad Request`.
- `seed_chroma_on_startup()` fails silently for all 12 seed documents. Logs show repeated `Chroma write failed` errors.
- **This means: zero vector memory works.** No conversation history search, no knowledge recall, no semantic context. ❌ CRITICAL

### 4.3 Journal

- `JOURNAL.md` exists in persona/. ✅
- `append_journal()` at `notifier.py:66-78` uses synchronous `open()` inside an `async def` — blocking I/O in async context. ⚠️
- Called at startup/shutdown and by proactive checks. ✅

### 4.4 Memory Recall in Q&A

- Q&A test never reached the `qa` intent (routed to `browse` instead). **ChromaDB query was never attempted.**
- Even if it were, ChromaDB is broken (see 4.2). Double failure.

---

## Section 5 — Interfaces

### 5.1 Telegram Bot

- Container UP, no healthcheck defined. ⚠️
- Handlers registered: `/start`, `/clear`, `/history`, `/tasks`, `/status`, `/model`, `/research`, photo, document, free text. ✅
- Bot sends to `CORE_API` (http://pings-core:8000). ✅
- **`/start` not testable** without real Telegram bot token + user.

### 5.2 Web Dashboard

- `GET /` returns 200 with HTML. ✅
- 9 routes registered in App.jsx: `/`, `/research`, `/tasks`, `/calendar`, `/homelab`, `/skills`, `/history`, `/mission-control`, `/settings`. ✅
- PWA manifest at `/manifest.json` references `/pings-icon.svg` — file exists in dist. ✅
- `manifest.json` has no 192px/512px PNG icons — only SVG. PWA install may fail on some browsers. ⚠️

### 5.3 Nginx

- Ports 80 and 443 listening. ✅
- HTTPS with self-signed certs. ✅
- `/api/*` → `pings-core:8000` proxied correctly. ✅
- `/*` → `pings-web:80` proxied correctly. ✅

---

## Section 6 — Supporting Services

### 6.1 SearXNG

- Container healthy. ✅
- JSON search works: `curl "http://pings-searxng:8080/search?q=test&format=json"` returns results. ✅
- `browser.py:14-33` — SearXNG is PRIMARY, DDG is fallback. SerpAPI not implemented (despite `.env` having `SERPAPI_KEY`). ⚠️

### 6.2 ntfy

- Container healthy. ✅
- `send_ntfy()` at `notifier.py:36-58` implemented. ✅
- `notify_all()` at `notifier.py:61-63` calls both `send_telegram()` and `send_ntfy()`. ✅

### 6.3 Proactive Scheduler

- APScheduler started in lifespan at `main.py:78`. ✅
- `homelab_check` and `overdue_tasks` jobs registered. ✅
- **`homelab_check()` at `checks.py:10-34` calls `test_ssh_connection()`** which is synchronous and blocking — not wrapped in `run_in_executor`. ⚠️
- **`_run_homelab_check()` at `scheduler.py:16-22`** uses `asyncio.get_event_loop()` from a sync context (APScheduler callback) — this may fail in production with `RuntimeError: no current event loop`. ⚠️

---

## Section 7 — Cross-Cutting

### 7.1 Naming Consistency

- All containers `pings-*` prefixed. ✅
- All on `pings-net`. ✅
- Missing healthchecks: `pings-bot`, `pings-web`. ⚠️

### 7.2 Blocking I/O

| Location | Issue | Severity |
|----------|-------|----------|
| `notifier.py:73` | `open()` sync in `async def append_journal()` | ⚠️ |
| `checks.py:13` | `test_ssh_connection()` sync in `async def homelab_check()` | ⚠️ |
| `ssh.py:58` | `test_ssh_connection()` is sync, called from sync context | OK (not in async) |
| `system.py:12-68` | `list_containers/control_container` async, delegates to `run_ssh_command` which wraps in executor | ✅ |
| `embedder.py:25-27` | `encode()` wraps sync in `run_in_executor` | ✅ |

### 7.3 Secrets

- `BRAIN_SECRET_KEY` not in settings table output. ✅
- `SSH_PASSWORD` exposed in `GET /settings` response as plaintext (not masked). ❌
- `.env` not committed to git (no `.gitignore` found — but this is a fresh repo). ⚠️

### 7.4 .env.example Completeness

- `OPENCODE_SERVER_URL` — in `.env` but NOT in `.env.example`. ⚠️
- `ZEN_API_KEY` — in `.env` but NOT in `.env.example`. ⚠️
- `EMBEDDING_MODEL` — in code (`config.py:61`) but NOT in `.env.example`. ⚠️

### 7.5 Workspace Sandbox

- `file_tool.py:15-18` — `_validate_path()` resolves path and checks it starts with WORKSPACE. ✅
- **Test:** `_validate_path("../../etc/passwd")` raises `ValueError: Path escapes workspace`. ✅

---

## Critical Issues

| # | File:Line | Description | Fix |
|---|-----------|-------------|-----|
| 1 | `config.py:61` | EMBEDDING_MODEL `"all-MiniLM-L6-v2"` — fastembed needs `"sentence-transformers/all-MiniLM-L6-v2"` | Change default to full model name |
| 2 | `router.py:64-67` | Tasks agent sends text to opencode — no SQLite task creation | Add `create_task()` call after opencode response parsing |
| 3 | `router.py:68-70` | CodeGen agent never invoked (misroute) + no file-write tool | Fix patterns + add actual file write |
| 4 | `main.py:109` | `verify_api_key()` always returns True — auth disabled | Enforce key check or document as dev-mode |
| 5 | `main.py:63-81` | Persona hot-reload watcher never started | Call `watch_persona_files()` in startup |
| 6 | `main.py:151-173` | Vision: image decoded as text, MODEL_VISION never used | Route image to NIM vision endpoint |
| 7 | `notifier.py:73` | Sync `open()` in async `append_journal()` | Use `aiofiles` or `run_in_executor` |

---

## Summary Table

| Section | Status | Issues |
|---------|--------|--------|
| 1. FastAPI core | PARTIAL | auth disabled, persona watcher dead, embedding model wrong |
| 2. Agents (7) | 2/7 | tasks lies, codegen misroutes, vision unused, report/research no file save |
| 3. Safety | PASS | confirmation works, rules present, minor gaps |
| 4. Memory | FAIL | ChromaDB completely broken (embedding model name) |
| 5. Interfaces | PASS | web loads, bot handlers registered, nginx proxies |
| 6. Services | PASS | SearXNG, ntfy, scheduler running |
| 7. Cross-cutting | PARTIAL | blocking I/O, secrets in settings, .env.example gaps |

---

## Next Steps

1. **Fix embedding model name** — change `config.py:61` to `"sentence-transformers/all-MiniLM-L6-v2"` (unblocks all vector memory)
2. **Fix tasks agent** — after opencode response, parse task details and call `create_task()` in SQLite
3. **Fix intent classification** — add `"n8n"` to homelab patterns, `"scaffold|project|file|script"` to codegen, remove `"what\s+is"` from browse
4. **Enable auth enforcement** — remove `return True` fallback in `verify_api_key()`
5. **Start persona watcher** — add `watch_persona_files(callback)` to startup lifespan
6. **Mask SSH_PASSWORD in /settings** — redact sensitive fields in API responses
7. **Fix async blocking** — wrap `append_journal()` file I/O and `homelab_check()` SSH call in `run_in_executor`
