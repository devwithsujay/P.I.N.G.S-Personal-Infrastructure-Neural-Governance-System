# P.I.N.G.S Core v2 — Database Schema

## Overview

P.I.N.G.S Core v2 uses SQLite as its primary relational database and ChromaDB for vector storage. All tables are defined below.

---

## SQLite Tables

### sessions
Tracks active user sessions and their configuration.

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    user_id       INTEGER NOT NULL,
    username      TEXT,
    current_model TEXT NOT NULL DEFAULT 'opencode/mimo-v2.5-free',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT PK | Telegram user ID as string |
| user_id | INTEGER | Telegram numeric user ID |
| username | TEXT | Telegram username |
| current_model | TEXT | Active Zen model ID |
| created_at | DATETIME | First interaction |
| updated_at | DATETIME | Last interaction |

---

### messages
Conversation history for each session.

```sql
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    model       TEXT,
    metadata    TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_messages_session ON messages(session_id, created_at);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT FK | Reference to sessions |
| role | TEXT | "user", "assistant", or "system" |
| content | TEXT | Message content |
| model | TEXT | Model that generated this message |
| metadata | TEXT | JSON string with extra data (intent, tokens, etc.) |
| created_at | DATETIME | Timestamp |

---

### tasks
Tracks ongoing and completed tasks.

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'running', 'done', 'failed')),
    agent       TEXT,
    result      TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_tasks_session ON tasks(session_id, status);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT FK | Reference to sessions |
| title | TEXT | Task title |
| description | TEXT | Task description |
| status | TEXT | pending, running, done, or failed |
| agent | TEXT | Which agent is handling this task |
| result | TEXT | Task output or result |
| created_at | DATETIME | Creation time |
| updated_at | DATETIME | Last update time |

---

### research_runs
Tracks research execution.

```sql
CREATE TABLE IF NOT EXISTS research_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL UNIQUE,
    session_id  TEXT NOT NULL,
    topic       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    queries     TEXT,
    report      TEXT,
    sources     TEXT,
    error       TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_research_session ON research_runs(session_id);
CREATE UNIQUE INDEX idx_research_run_id ON research_runs(run_id);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| run_id | TEXT UNIQUE | UUID for the research run |
| session_id | TEXT FK | Reference to sessions |
| topic | TEXT | Research topic |
| status | TEXT | pending, running, completed, or failed |
| queries | TEXT | JSON array of search queries used |
| report | TEXT | Compiled research report |
| sources | TEXT | JSON array of source URLs |
| error | TEXT | Error message if failed |
| created_at | DATETIME | Creation time |
| completed_at | DATETIME | Completion time |

---

### uploads
Tracks uploaded files (photos, documents).

```sql
CREATE TABLE IF NOT EXISTS uploads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    file_type   TEXT NOT NULL CHECK (file_type IN ('photo', 'document')),
    file_name   TEXT,
    file_size   INTEGER,
    mime_type   TEXT,
    file_path   TEXT,
    processed   INTEGER NOT NULL DEFAULT 0,
    result      TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_uploads_session ON uploads(session_id);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT FK | Reference to sessions |
| file_type | TEXT | "photo" or "document" |
| file_name | TEXT | Original filename |
| file_size | INTEGER | File size in bytes |
| mime_type | TEXT | MIME type |
| file_path | TEXT | Storage path |
| processed | INTEGER | 0 = pending, 1 = processed |
| result | TEXT | Processing result |
| created_at | DATETIME | Upload time |

---

### model_switches
Logs model selection changes.

```sql
CREATE TABLE IF NOT EXISTS model_switches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    old_model   TEXT,
    new_model   TEXT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_model_switches_session ON model_switches(session_id);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT FK | Reference to sessions |
| old_model | TEXT | Previous model |
| new_model | TEXT | New model |
| created_at | DATETIME | Switch time |

---

## ChromaDB Collections

### conversation_history
Stores vector embeddings of conversation messages for semantic search.

| Property | Value |
|----------|-------|
| Collection | conversation_history |
| Document | Message content |
| Metadata | session_id, role, timestamp, model |
| Distance | cosine |

### research_findings
Stores research results for retrieval.

| Property | Value |
|----------|-------|
| Collection | research_findings |
| Document | Research summary text |
| Metadata | run_id, topic, source_url, timestamp |
| Distance | cosine |

### code_snippets
Stores code for context and reuse.

| Property | Value |
|----------|-------|
| Collection | code_snippets |
| Document | Code content |
| Metadata | session_id, language, filename, timestamp |
| Distance | cosine |

---

## Initialization

The database is auto-created on first startup. Schema migration is handled by the FastAPI application at boot.

```python
# Core initialization pattern
import sqlite3

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create all tables
    cursor.executescript(SCHEMA_SQL)
    
    conn.commit()
    conn.close()
```
