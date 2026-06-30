# P.I.N.G.S Core v2 — Application Flow

## Request Lifecycle

### 1. Telegram Message Received

```
Telegram Bot API
  │
  ▼
pings-bot (aiogram dispatcher)
  │
  ├─ Is it a command? (/start, /clear, /model, etc.)
  │   ├─ YES → Handle command locally
  │   │         Return response immediately
  │   │
  │   └─ NO → Continue to processing
  │
  ├─ Is it a photo or document?
  │   ├─ YES → Upload flow (see §2)
  │   │
  │   └─ NO → Continue to processing
  │
  ├─ Is it free text?
  │   └─ YES → Chat flow (see §3)
  │
  └─ Check user authorization
      ├─ ALLOWED → Process
      └─ DENIED → "Access denied."
```

### 2. Upload Flow (Photo/Document)

```
User sends photo/document
  │
  ▼
pings-bot
  │
  ├─ Download file from Telegram
  │   (bot.get_file → bot.download_file)
  │
  ├─ POST /api/chat/upload
  │   Body: multipart/form-data
  │     - session_id: str(user.id)
  │     - caption: message.caption or ""
  │     - file: binary data
  │
  ▼
pings-core (/api/chat/upload)
  │
  ├─ Determine file type
  │   ├─ Image → Vision agent (NVIDIA NIM)
  │   └─ Document → Document parser
  │
  ├─ Process file content
  │
  ├─ Store in conversation history
  │
  └─ Return response text
      │
      ▼
pings-bot → Send reply to user
```

### 3. Chat Flow (Free Text)

```
User sends text message
  │
  ▼
pings-bot
  │
  ├─ POST /api/chat/message
  │   Body: JSON
  │     - session_id: str(user.id)
  │     - content: message text
  │
  ▼
pings-core (/api/chat/message)
  │
  ├─ Intent Classifier
  │   │
  │   │  Analyze message content:
  │   │  - Keywords (code, debug, fix, deploy, research, etc.)
  │   │  - Context from conversation history
  │   │  - Current model capabilities
  │   │
  │   ├─ "chat" → Chat Agent
  │   │           General conversation, Q&A
  │   │
  │   ├─ "code" → Code Agent
  │   │           Write, debug, review code
  │   │
  │   ├─ "research" → Research Agent
  │   │               Search web, compile findings
  │   │
  │   ├─ "devops" → DevOps Agent
  │   │             Docker, nginx, systemd, SSH
  │   │
  │   └─ "vision" → Vision Agent
  │                 Image analysis via NIM
  │
  ├─ Agent executes task
  │   │
  │   ├─ May call tools:
  │   │   - SearXNG (search)
  │   │   - ChromaDB (memory lookup)
  │   │   - SSH (remote execution)
  │   │   - File system (workspace)
  │   │
  │   └─ Generate response
  │
  ├─ Store in SQLite (conversation history)
  │
  ├─ Store in ChromaDB (vector embeddings)
  │
  └─ Return response JSON
      │
      ▼
pings-bot → Send reply to user
```

## Model Switching Flow

```
User: /model
  │
  ▼
pings-bot
  │
  ├─ GET /api/model/current
  │   Returns: { model: "opencode/mimo-v2.5-free" }
  │
  ├─ Show inline keyboard with 5 models:
  │   ✅ MiMo V2.5 Free (current)
  │   ⭐ DeepSeek V4 Flash Free
  │     Nemotron 3 Ultra Free
  │     Big Pickle
  │     North Mini Code Free
  │
  └─ Wait for callback
      │
      ▼
User taps a model button
  │
  ├─ callback_data: "model:opencode/deepseek-v4-flash-free"
  │
  ▼
pings-bot
  │
  ├─ POST /api/model/set
  │   Body: { session_id, model: "opencode/deepseek-v4-flash-free" }
  │
  ▼
pings-core
  │
  ├─ Update session model in memory
  │
  └─ Return success
      │
      ▼
pings-bot → Edit message: "Switched to DeepSeek V4 Flash Free."
```

## Research Flow

```
User: /research quantum computing
  │
  ▼
pings-bot
  │
  ├─ State: waiting_topic
  │
  ├─ User sends topic
  │
  ├─ POST /api/research/start
  │   Body: { session_id, topic: "quantum computing" }
  │
  ▼
pings-core (/api/research/start)
  │
  ├─ Create research run (SQLite)
  │   run_id: uuid
  │   status: "running"
  │   topic: "quantum computing"
  │   created_at: now()
  │
  ├─ Research Agent:
  │   │
  │   ├─ Step 1: Generate search queries
  │   │   "quantum computing basics"
  │   │   "quantum computing applications 2026"
  │   │   "quantum computing vs classical"
  │   │
  │   ├─ Step 2: Search via SearXNG
  │   │   POST http://pings-searxng:8080/search
  │   │   Format: JSON
  │   │
  │   ├─ Step 3: Fetch and summarize top results
  │   │   Extract key points from each result
  │   │
  │   ├─ Step 4: Store in ChromaDB
  │   │   Collection: research_runs
  │   │   Document: compiled findings
  │   │
  │   ├─ Step 5: Compile report
  │   │   Structure: summary, key points, sources
  │   │
  │   └─ Step 6: Notify via ntfy
  │       POST http://pings-ntfy:80/pings-alerts
  │       Message: "Research complete: quantum computing"
  │
  ├─ Update run status to "completed"
  │
  └─ Return { run_id, status }
      │
      ▼
pings-bot → "Research run created: {run_id}"
            "Results will be sent when complete."
```

## Agent Dispatch Table

| Intent | Agent | Tools Used | Response Type |
|--------|-------|-----------|---------------|
| chat | Chat Agent | ChromaDB (memory) | Text |
| code | Code Agent | File system, SSH | Code + explanation |
| research | Research Agent | SearXNG, ChromaDB | Report |
| devops | DevOps Agent | SSH, Docker API | Command + output |
| vision | Vision Agent | NVIDIA NIM | Image description |

## Error Handling

```
Any Request
  │
  ├─ Success (2xx)
  │   └─ Return response to user
  │
  ├─ Client Error (4xx)
  │   ├─ 401 → "Authentication failed"
  │   ├─ 404 → "Resource not found"
  │   └─ 422 → "Invalid request"
  │
  ├─ Server Error (5xx)
  │   ├─ 500 → "Internal error. Check logs."
  │   ├─ 502 → "Core API unavailable"
  │   └─ 503 → "Service overloaded"
  │
  └─ Timeout
      └─ "Request timed out. Try again."
```
