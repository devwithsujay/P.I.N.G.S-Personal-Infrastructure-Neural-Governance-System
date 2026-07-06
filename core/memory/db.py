import aiosqlite
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.config import settings

logger = logging.getLogger("pings.memory.db")

_DB_PATH = settings.SQLITE_DB_PATH


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


@asynccontextmanager
async def get_db_ctx():
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    try:
        async with get_db_ctx() as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT DEFAULT NULL,
                    model TEXT DEFAULT NULL,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'medium',
                    due_date TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    cron_expr TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_run TEXT DEFAULT NULL,
                    next_run TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    system_prompt TEXT DEFAULT '',
                    model TEXT DEFAULT NULL,
                    tools TEXT DEFAULT '[]',
                    personality TEXT DEFAULT NULL,
                    memory TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    embedding_id TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    session_id TEXT,
                    intent TEXT,
                    model TEXT,
                    input_text TEXT,
                    output_text TEXT,
                    duration_ms INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                );
                CREATE TABLE IF NOT EXISTS research_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    mode TEXT DEFAULT 'balanced',
                    status TEXT DEFAULT 'queued',
                    sources_count INTEGER DEFAULT 0,
                    report_html TEXT DEFAULT NULL,
                    report_path TEXT DEFAULT NULL,
                    error TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    completed_at TEXT DEFAULT NULL
                );
                CREATE TABLE IF NOT EXISTS calendar_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    due_date TEXT NOT NULL,
                    due_time TEXT DEFAULT NULL,
                    priority TEXT DEFAULT 'medium',
                    recurrence TEXT DEFAULT 'none',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_entries(session_id);
                CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_id);
                CREATE INDEX IF NOT EXISTS idx_research_status ON research_runs(status);
            """)
            await db.commit()
            migrations = [
                "ALTER TABLE research_runs ADD COLUMN type TEXT DEFAULT 'standard'",
                "ALTER TABLE research_runs ADD COLUMN outline TEXT DEFAULT NULL",
                "ALTER TABLE research_runs ADD COLUMN progress INTEGER DEFAULT 0",
                "ALTER TABLE research_runs ADD COLUMN report_docx_path TEXT DEFAULT NULL",
            ]
            for migration in migrations:
                try:
                    await db.execute(migration)
                    await db.commit()
                except Exception:
                    pass
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def save_message(session_id: str, role: str, content: str, intent: Optional[str] = None, model: Optional[str] = None) -> int:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "INSERT INTO conversations (session_id, role, content, intent, model) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, intent, model),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_session_messages(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in reversed(rows)]


async def get_all_sessions() -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute("""
            SELECT c.session_id,
                   MIN(c.timestamp) as created_at,
                   MAX(c.timestamp) as updated_at,
                   COUNT(*) as message_count,
                   (SELECT content FROM conversations
                    WHERE session_id = c.session_id AND role = 'user'
                    ORDER BY timestamp ASC LIMIT 1) as title
            FROM conversations c
            GROUP BY c.session_id
            ORDER BY updated_at DESC
        """)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def delete_session(session_id: str) -> bool:
    try:
        async with get_db_ctx() as db:
            await db.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        return False


async def delete_all_sessions() -> bool:
    try:
        async with get_db_ctx() as db:
            await db.execute("DELETE FROM conversations")
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Delete all sessions error: {e}")
        return False


async def create_task(title: str, description: str = "", priority: str = "medium", due_date: Optional[str] = None) -> int:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "INSERT INTO tasks (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
            (title, description, priority, due_date),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        if status:
            cursor = await db.execute("SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor = await db.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_task(task_id: int, **kwargs: Any) -> bool:
    async with get_db_ctx() as db:
        allowed = {"title", "description", "status", "priority", "due_date"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        await db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return True


async def delete_task(task_id: int) -> bool:
    async with get_db_ctx() as db:
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        return True


async def get_overdue_tasks() -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        now = datetime.utcnow().isoformat()
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE status != 'done' AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date ASC",
            (now,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def create_scheduled_task(task_id: int, cron_expr: str, next_run: Optional[str] = None) -> int:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "INSERT INTO scheduled_tasks (task_id, cron_expr, next_run) VALUES (?, ?, ?)",
            (task_id, cron_expr, next_run),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_scheduled_tasks() -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute("""
            SELECT st.*, t.title, t.description
            FROM scheduled_tasks st
            JOIN tasks t ON st.task_id = t.id
            WHERE st.enabled = 1
        """)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_scheduled_task(sched_id: int, **kwargs: Any) -> bool:
    async with get_db_ctx() as db:
        allowed = {"enabled", "last_run", "next_run", "cron_expr"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [sched_id]
        await db.execute(f"UPDATE scheduled_tasks SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return True


async def delete_scheduled_task(sched_id: int) -> bool:
    async with get_db_ctx() as db:
        await db.execute("DELETE FROM scheduled_tasks WHERE id = ?", (sched_id,))
        await db.commit()
        return True


async def create_calendar_task(title: str, due_date: str, description: str = "", due_time: Optional[str] = None, priority: str = "medium", recurrence: str = "none") -> int:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "INSERT INTO calendar_tasks (title, description, due_date, due_time, priority, recurrence) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, due_date, due_time, priority, recurrence),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_calendar_tasks() -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "SELECT * FROM calendar_tasks ORDER BY due_date ASC, due_time ASC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_calendar_task(task_id: int, **kwargs: Any) -> bool:
    async with get_db_ctx() as db:
        allowed = {"title", "description", "due_date", "due_time", "priority", "recurrence", "status"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]
        await db.execute(f"UPDATE calendar_tasks SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return True


async def delete_calendar_task(task_id: int) -> bool:
    async with get_db_ctx() as db:
        await db.execute("DELETE FROM calendar_tasks WHERE id = ?", (task_id,))
        await db.commit()
        return True


async def get_setting(key: str) -> Optional[str]:
    async with get_db_ctx() as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else None


async def set_setting(key: str, value: str) -> None:
    async with get_db_ctx() as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_all_settings() -> Dict[str, str]:
    async with get_db_ctx() as db:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {r["key"]: r["value"] for r in rows}


async def create_agent(name: str, description: str = "", system_prompt: str = "", model: Optional[str] = None, tools: Optional[List[str]] = None) -> int:
    import json
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "INSERT INTO agents (name, description, system_prompt, model, tools) VALUES (?, ?, ?, ?, ?)",
            (name, description, system_prompt, model, json.dumps(tools or [])),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_agents() -> List[Dict[str, Any]]:
    import json
    async with get_db_ctx() as db:
        cursor = await db.execute("SELECT * FROM agents ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tools"] = json.loads(d.get("tools", "[]"))
            result.append(d)
        return result


async def get_agent(agent_id: int) -> Optional[Dict[str, Any]]:
    import json
    async with get_db_ctx() as db:
        cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = await cursor.fetchone()
        if row:
            d = dict(row)
            d["tools"] = json.loads(d.get("tools", "[]"))
            return d
        return None


async def update_agent(agent_id: int, **kwargs: Any) -> bool:
    import json
    async with get_db_ctx() as db:
        allowed = {"name", "description", "system_prompt", "model", "tools", "personality", "memory"}
        updates: Dict[str, Any] = {}
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                if k == "tools" and isinstance(v, list):
                    updates[k] = json.dumps(v)
                else:
                    updates[k] = v
        if not updates:
            return False
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [agent_id]
        await db.execute(f"UPDATE agents SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return True


async def delete_agent(agent_id: int) -> bool:
    async with get_db_ctx() as db:
        await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        await db.commit()
        return True


async def save_memory_entry(content: str, session_id: Optional[str] = None, category: str = "general", embedding_id: Optional[str] = None) -> int:
    async with get_db_ctx() as db:
        eid = embedding_id or str(uuid.uuid4())
        cursor = await db.execute(
            "INSERT INTO memory_entries (session_id, content, category, embedding_id) VALUES (?, ?, ?, ?)",
            (session_id, content, category, eid),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_memory_entries(session_id: Optional[str] = None, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        conditions: List[str] = []
        params: List[Any] = []
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if category:
            conditions.append("category = ?")
            params.append(category)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        cursor = await db.execute(f"SELECT * FROM memory_entries{where} ORDER BY created_at DESC LIMIT ?", params + [limit])
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def save_agent_run(agent_id: int, session_id: str, intent: str, model: str, input_text: str, output_text: str, duration_ms: int = 0, status: str = "success") -> int:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "INSERT INTO agent_runs (agent_id, session_id, intent, model, input_text, output_text, duration_ms, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (agent_id, session_id, intent, model, input_text, output_text, duration_ms, status),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_agent_runs(limit: int = 20) -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "SELECT ar.*, a.name as agent_name FROM agent_runs ar LEFT JOIN agents a ON ar.agent_id = a.id ORDER BY ar.created_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_last_agent_run() -> Optional[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "SELECT ar.*, a.name as agent_name FROM agent_runs ar LEFT JOIN agents a ON ar.agent_id = a.id ORDER BY ar.created_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_research_run(topic: str, mode: str = "balanced") -> int:
    async with get_db_ctx() as db:
        await db.execute(
            "DELETE FROM research_runs WHERE topic = ? AND status = 'running'",
            (topic,),
        )
        research_type = "deep" if mode == "deep" else "standard"
        cursor = await db.execute(
            "INSERT INTO research_runs (topic, mode, type) VALUES (?, ?, ?)",
            (topic, mode, research_type),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def update_research_run(run_id: int, **kwargs: Any) -> bool:
    async with get_db_ctx() as db:
        allowed = {"status", "sources_count", "report_html", "report_path", "error", "completed_at", "type", "outline", "progress", "report_docx_path"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [run_id]
        await db.execute(f"UPDATE research_runs SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return True


async def get_research_runs(status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        if status:
            cursor = await db.execute(
                "SELECT * FROM research_runs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM research_runs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_research_run(run_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute("SELECT * FROM research_runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_next_queued_run() -> Optional[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            "SELECT * FROM research_runs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_research_run(run_id: int) -> bool:
    async with get_db_ctx() as db:
        await db.execute("DELETE FROM research_runs WHERE id = ?", (run_id,))
        await db.commit()
        return True
