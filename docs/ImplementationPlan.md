# P.I.N.G.S Core v2 — Implementation Plan

## Phase 1: Foundation (Week 1)

### 1.1 Project Structure
- [ ] Create directory structure
- [ ] Set up .env.example with all variables
- [ ] Create .gitignore
- [ ] Initialize Docker Compose with all 7 services
- [ ] Verify all containers start and pass healthchecks

### 1.2 Core API (FastAPI)
- [ ] Set up FastAPI project structure
- [ ] Create SQLite database initialization (Schema.md)
- [ ] Implement /api/status endpoint
- [ ] Implement /api/chat/message endpoint
- [ ] Implement /api/chat/clear endpoint
- [ ] Implement /api/chat/history endpoint
- [ ] Implement /api/model/current endpoint
- [ ] Implement /api/model/set endpoint
- [ ] Implement /api/chat/upload endpoint
- [ ] Implement /api/tasks/list endpoint
- [ ] Implement /api/research/start endpoint

### 1.3 Telegram Bot
- [ ] Set up aiogram 3 dispatcher
- [ ] Implement /start command
- [ ] Implement /clear command
- [ ] Implement /history command
- [ ] Implement /tasks command
- [ ] Implement /status command
- [ ] Implement /model command with inline keyboard
- [ ] Implement /research command with state machine
- [ ] Implement photo handler
- [ ] Implement document handler
- [ ] Implement free text handler with intent routing
- [ ] Add user authorization check

### 1.4 Infrastructure
- [ ] Configure nginx reverse proxy (nginx.conf)
- [ ] Set up TLS certificates (self-signed for dev)
- [ ] Configure SearXNG (settings.yml)
- [ ] Verify ChromaDB connectivity
- [ ] Verify ntfy connectivity

**Deliverable**: Working stack with bot commands and basic chat via API.

---

## Phase 2: Intelligence (Week 2)

### 2.1 Intent Classification
- [ ] Design intent categories (chat, code, research, devops, vision)
- [ ] Implement keyword-based classifier
- [ ] Add fallback to chat for ambiguous inputs
- [ ] Test with sample messages

### 2.2 Agent System
- [ ] Create base Agent class
- [ ] Implement ChatAgent
- [ ] Implement CodeAgent
- [ ] Implement ResearchAgent
- [ ] Implement DevOpsAgent
- [ ] Implement VisionAgent
- [ ] Wire agents to intent classifier

### 2.3 Model Integration
- [ ] Integrate opencode for Zen AI models
- [ ] Implement model switching in session
- [ ] Add NVIDIA NIM client for vision
- [ ] Test all 5 models respond correctly

### 2.4 Vector Memory
- [ ] Set up ChromaDB client
- [ ] Implement conversation embedding on message
- [ ] Implement semantic search for context retrieval
- [ ] Test retrieval accuracy

**Deliverable**: Bot classifies intent and routes to correct agent with working model switching.

---

## Phase 3: Features (Week 3)

### 3.1 Research System
- [ ] Design research workflow (query → search → summarize → report)
- [ ] Implement SearXNG API client
- [ ] Implement query generation from topic
- [ ] Implement result summarization
- [ ] Implement report compilation
- [ ] Store research in ChromaDB
- [ ] Send ntfy notification on completion
- [ ] Add research_runs table tracking

### 3.2 File Processing
- [ ] Implement image upload → vision analysis
- [ ] Implement document upload → text extraction
- [ ] Store upload metadata in SQLite
- [ ] Return analysis results to user

### 3.3 Task Management
- [ ] Implement task creation from agent actions
- [ ] Implement task status tracking
- [ ] Add /tasks list display

### 3.4 Web Dashboard
- [ ] Set up React project with Vite
- [ ] Build status page
- [ ] Build chat history viewer
- [ ] Build model selector
- [ ] Build task list view
- [ ] Connect to /api/* endpoints

**Deliverable**: Full feature set — research, file processing, tasks, web dashboard.

---

## Phase 4: Polish (Week 4)

### 4.1 Persona System
- [ ] Load IDENTITY.md at startup
- [ ] Load CONTEXT.md for session context
- [ ] Load RULES.md for safety checks
- [ ] Inject persona into system prompts
- [ ] Update JOURNAL.md on significant actions

### 4.2 SSH Integration
- [ ] Implement SSH client with key/password auth
- [ ] Add confirmation for destructive commands
- [ ] Implement read-only command execution
- [ ] Test remote command flow

### 4.3 Proactive Agent
- [ ] Implement periodic background task scheduler
- [ ] Add configurable interval (PROACTIVE_INTERVAL_MINUTES)
- [ ] Implement health monitoring checks
- [ ] Send proactive alerts via ntfy

### 4.4 Hardening
- [ ] Rate limiting on API endpoints
- [ ] Input validation on all endpoints
- [ ] Error handling and logging
- [ ] Security headers in nginx
- [ ] Container resource limits
- [ ] Backup script for volumes

### 4.5 Documentation
- [ ] Complete all docs/*
- [ ] Add API documentation (OpenAPI)
- [ ] Add setup guide
- [ ] Add troubleshooting guide

**Deliverable**: Production-ready system with full documentation.

---

## Success Criteria

| Phase | Criteria |
|-------|----------|
| Phase 1 | All containers healthy, bot responds to commands |
| Phase 2 | Intent classification works, model switching functional |
| Phase 3 | Research completes, files processed, dashboard loads |
| Phase 4 | SSH works, proactive agent runs, docs complete |

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Model API downtime | Graceful fallback with error message |
| ChromaDB data loss | Regular volume backups |
| Telegram API rate limits | Implement request throttling |
| SSH security | Confirmation required for destructive ops |
| Disk space | Monitor volume sizes, alert at 80% |
