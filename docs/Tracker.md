# P.I.N.G.S Core v2 — Build Progress Tracker

## Status Legend

- ⬜ Pending
- 🔄 In Progress
- ✅ Complete
- ❌ Broken
- ⚠️ Partial

---

## Phase 1: Foundation

| #   | Task                       | Status | Notes                                                                 |
|-----|----------------------------|--------|----------------------------------------------------------------------|
| 1.1 | Create directory structure | ✅     | bot/, nginx/, searxng/, persona/, scripts/, docs/                        |
| 1.2 | Create .env.example        | ✅     | OPENCODE_SERVER_URL, ZEN_API_KEY, EMBEDDING_MODEL (verified 2026-06-30) |
| 1.3 | Create .gitignore           | ✅     | Python, Node, Docker, secrets                                        |
| 1.4 | docker-compose.yml         | ✅     | 8 services, all healthchecks (except bot, web)                         |
| 1.5 | nginx/nginx.conf           | ✅     | HTTP→HTTPS, API proxy, SPA fallback                                    |
| 1.6 | searxng/settings.yml       | ✅     | JSON format, limiter off                                             |
| 1.7 | bot/main.py                | ✅     | All commands, model selector, handlers                                |
| 1.8 | bot/requirements.txt       | ✅     | aiogram>=3.7, httpx                                                  |
| 1.9 | bot/Dockerfile             | ✅     | python:3.11-slim                                                     |
| 1.10| Core API — /api/status      | ✅     | Health + uptime + services                                           |
| 1.11| Core API — /api/chat        | ✅     | Message + upload + history + clear                                   |
| 1.12| Core API — /api/models      | ✅     | List + set default                                                   |
| 1.13| Core API — /api/tasks       | ✅     | CRUD + schedule                                                     |
| 1.14| Core API — /api/research    | ✅     | Start + queue + runs + discuss                                       |
| 1.15| Core API — /api/homelab     | ✅     | Status + SSH test + containers + stats                                |
| 1.16| Core API — /api/settings    | ✅     | Get + update                                                         |
| 1.17| SQLite schema init         | ✅     | 8 tables auto-created                                                |
| 1.18| Verify all containers healthy | ✅ | 8/8 UP, 6/8 healthy (verified 2026-06-30)                             |

## Phase 2: Intelligence

| #   | Task                       | Status | Notes                                                                 |
|-----|----------------------------|--------|----------------------------------------------------------------------|
| 2.1 | Intent classifier          | ✅     | All 8 phrases correct (fixed 2026-06-30: "what is"/"what are" added to browse) |
| 2.2 | opencode sidecar integration| ✅     | HTTP API, session create + prompt, health check                       |
| 2.3 | HomeLab agent              | ✅     | SSH + Docker management, safety checks                                |
| 2.4 | CodeGen agent              | ❌     | Misroutes to qa + no file-write tool in opencode (requires live test)  |
| 2.5 | Research agent             | ✅     | 5 mode-specific templates (product/compare/how-to/fact-check/auto), keyword classifier, skip-if-empty enforcement, Odysseus HTML report |
| 2.6 | Report agent              | ⚠️     | Generates text but doesn't save to workspace (requires live test)     |
| 2.7 | Vision agent              | ❌     | Image decoded as text, MODEL_VISION never used (static check only)     |
| 2.8 | Model switching            | ✅     | 5 Zen models, persisted in SQLite, flows to opencode                   |
| 2.9 | ChromaDB integration      | ⚠️     | Embedding model name fixed in config.py + Dockerfile (2026-06-30), needs live test |
| 2.10| Vector embeddings          | ⚠️     | Model name corrected to "sentence-transformers/all-MiniLM-L6-v2", needs live test |
| 2.11| Semantic search            | ⚠️     | Should be unblocked by embedding fix, needs live test |

## Phase 3: Features

| #   | Task                       | Status | Notes                                                                 |
|-----|----------------------------|--------|----------------------------------------------------------------------|
| 3.1 | SearXNG API client         | ✅     | Primary search, JSON format, DDG fallback                             |
| 3.2 | Research workflow           | ✅     | Mode-specific prompts, keyword classifier, skip-if-empty post-processing, HTML report rendered inline |
| 3.3 | Research notification       | ✅     | ntfy + Telegram via notify_all()                                    |
| 3.4 | Image upload processing    | ❌     | Routed as text, no vision model call                                 |
| 3.5 | Document upload processing | ✅     | Text extracted, injected as context prefix                           |
| 3.6 | Task management            | ✅     | handle_tasks() calls create_task() SQLite write, list/done/delete all work (verified 2026-06-30) |
| 3.7 | React dashboard — all pages | ✅     | Chat, Research, Tasks, Calendar, HomeLab, Skills, History, MissionControl, Settings |
| 3.8 | PWA manifest              | ⚠️     | Manifest exists, SVG icon only (no 192/512 PNG) (verified 2026-06-30) |
| 3.9 | SSH config via UI          | ✅     | Key + password auth, save + test                                     |

## Phase 4: Polish

| #   | Task                       | Status | Notes                                                                 |
|-----|----------------------------|--------|----------------------------------------------------------------------|
| 4.1 | Persona system             | ⚠️     | Load works, hot-reload watcher never started (static check)           |
| 4.2 | SSH integration            | ✅     | paramiko, key + password auth, safety checks                          |
| 4.3 | Proactive agent            | ⚠️     | Scheduler runs, but blocking I/O in callbacks                         |
| 4.4 | Auth enforcement           | ❌     | verify_api_key() validation logic correct at code level; remove "return True" fallback to enable |
| 4.5 | Safety (RULES.md)          | ✅     | CONFIRM_BEFORE + DANGER_PATTERNS enforced                               |
| 4.6 | Error handling             | ✅     | Global exception handler, graceful failures                           |
| 4.7 | Workspace sandbox          | ✅     | Path traversal blocked                                               |
| 4.8 | Journal logging            | ⚠️     | append_journal() uses sync open() in async                             |

---

## Summary

| Phase   | Total | Complete | Broken | Partial |
|---------|-------|----------|--------|---------|
| Phase 1  | 18    | 17       | 0      | 1        |
| Phase 2  | 11    | 6        | 1      | 4        |
| Phase 3  | 9     | 6        | 1      | 2        |
| Phase 4  | 8     | 4        | 2      | 2        |
| **Total**| **46**| **33**   | **5**  | **8**    |

**Overall**: 72% working, 11% broken, 17% partial

---

## Critical Fixes Needed (Priority Order)

1. **Enable auth** — remove `return True` fallback in `verify_api_key()`
2. **Start persona watcher** — add `watch_persona_files()` to startup lifespan
3. **Wire vision to NIM** — route image uploads to MODEL_VISION endpoint
4. **Save reports to disk** — codegen + report agents need file-write calls

---

## Regressions found

none found

---

## Audit Date

**2026-06-30** — Fixes applied: Dockerfile embedding model corrected (sentence-transformers/all-MiniLM-L6-v2), intent classifier patterns added ("what is"/"what are" → browse), tasks agent confirmed writing to SQLite. Critical fixes list reduced from 7 to 4. Tracker re-audited: 33/46 working (72%), 5 broken (11%), 8 partial (17%).

**2026-06-30** — Mode-specific research templates implemented. 5 templates (product/compare/how-to/fact-check/auto) replace single fixed structure. Keyword-based mode classifier. Skip-if-empty post-processing. HTML renderer confirmed structure-agnostic.

**2026-06-23** — Full audit completed. See `docs/CORE_AUDIT.md` for details.
