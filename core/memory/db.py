import aiosqlite
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

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


async def _execute(sql: str, params: tuple = ()) -> aiosqlite.Cursor:
    async with get_db_ctx() as db:
        cursor = await db.execute(sql, params)
        await db.commit()
        return cursor


async def _fetch(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(sql, params)
        return [dict(r) for r in await cursor.fetchall()]


async def _fetch_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(sql, params)
        row = await cursor.fetchone()
        return dict(row) if row else None


async def _insert(table: str, **values: Any) -> int:
    cols = ", ".join(values.keys())
    placeholders = ", ".join("?" for _ in values)
    cursor = await _execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", tuple(values.values()))
    return cursor.lastrowid or 0


async def _update(table: str, id: int, allowed: set, **kwargs: Any) -> bool:
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    await _execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", tuple(updates.values()) + (id,))
    return True


async def _delete(table: str, id: int) -> bool:
    await _execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    return True


async def init_db() -> None:
    try:
        async with get_db_ctx() as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, role TEXT NOT NULL,
                    content TEXT NOT NULL, intent TEXT DEFAULT NULL, model TEXT DEFAULT NULL,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending', priority TEXT DEFAULT 'medium', due_date TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, cron_expr TEXT,
                    enabled INTEGER DEFAULT 1, last_run TEXT DEFAULT NULL, next_run TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')), FOREIGN KEY (task_id) REFERENCES tasks(id)
                );
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT (datetime('now')));
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT DEFAULT '',
                    system_prompt TEXT DEFAULT '', model TEXT DEFAULT NULL, tools TEXT DEFAULT '[]',
                    personality TEXT DEFAULT NULL, memory TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, content TEXT NOT NULL,
                    category TEXT DEFAULT 'general', embedding_id TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id INTEGER, session_id TEXT, intent TEXT,
                    model TEXT, input_text TEXT, output_text TEXT, duration_ms INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success', created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                );
                CREATE TABLE IF NOT EXISTS research_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL, mode TEXT DEFAULT 'balanced',
                    status TEXT DEFAULT 'queued', sources_count INTEGER DEFAULT 0, report_html TEXT DEFAULT NULL,
                    report_path TEXT DEFAULT NULL, error TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')), completed_at TEXT DEFAULT NULL
                );
                CREATE TABLE IF NOT EXISTS calendar_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT DEFAULT '',
                    due_date TEXT NOT NULL, due_time TEXT DEFAULT NULL, priority TEXT DEFAULT 'medium',
                    recurrence TEXT DEFAULT 'none', status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_entries(session_id);
                CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_id);
                CREATE INDEX IF NOT EXISTS idx_research_status ON research_runs(status);
                CREATE TABLE IF NOT EXISTS automations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    schedule_time TEXT NOT NULL,
                    timezone TEXT DEFAULT 'UTC',
                    active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    last_run_at TEXT DEFAULT NULL
                );
                CREATE TABLE IF NOT EXISTS briefing_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    automation_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    started_at TEXT DEFAULT NULL,
                    completed_at TEXT DEFAULT NULL,
                    pdf_path TEXT DEFAULT NULL,
                    error_message TEXT DEFAULT NULL,
                    FOREIGN KEY (automation_id) REFERENCES automations(id) ON DELETE CASCADE
                );
            """)
            await db.commit()
            for migration in [
                "ALTER TABLE research_runs ADD COLUMN type TEXT DEFAULT 'standard'",
                "ALTER TABLE research_runs ADD COLUMN outline TEXT DEFAULT NULL",
                "ALTER TABLE research_runs ADD COLUMN progress INTEGER DEFAULT 0",
                "ALTER TABLE research_runs ADD COLUMN report_docx_path TEXT DEFAULT NULL",
                "ALTER TABLE research_runs ADD COLUMN report TEXT DEFAULT NULL",
            ]:
                try:
                    await db.execute(migration)
                    await db.commit()
                except Exception:
                    pass
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


# ── Conversations ────────────────────────────────────────────────────────────
async def save_message(session_id: str, role: str, content: str, intent: Optional[str] = None, model: Optional[str] = None) -> int:
    if intent is not None and model is not None:
        return await _insert("conversations", session_id=session_id, role=role, content=content, intent=intent, model=model)
    return await _insert("conversations", session_id=session_id, role=role, content=content)


async def get_session_messages(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    rows = await _fetch("SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?", (session_id, limit))
    return list(reversed(rows))


async def get_all_sessions() -> List[Dict[str, Any]]:
    return await _fetch("""
        SELECT c.session_id, MIN(c.timestamp) as created_at, MAX(c.timestamp) as updated_at,
               COUNT(*) as message_count,
               (SELECT content FROM conversations WHERE session_id = c.session_id AND role = 'user' ORDER BY timestamp ASC LIMIT 1) as title
        FROM conversations c GROUP BY c.session_id ORDER BY updated_at DESC""")


async def delete_session(session_id: str) -> bool:
    await _execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    return True


async def delete_all_sessions() -> bool:
    await _execute("DELETE FROM conversations")
    return True


# ── Tasks ────────────────────────────────────────────────────────────────────
async def create_task(title: str, description: str = "", priority: str = "medium", due_date: Optional[str] = None) -> int:
    return await _insert("tasks", title=title, description=description, priority=priority)


async def get_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    if status:
        return await _fetch("SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status,))
    return await _fetch("SELECT * FROM tasks ORDER BY created_at DESC")


async def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    return await _fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))


async def update_task(task_id: int, **kwargs: Any) -> bool:
    kwargs.setdefault("updated_at", datetime.utcnow().isoformat())
    return await _update("tasks", task_id, {"title", "description", "status", "priority", "due_date"}, **kwargs)


async def delete_task(task_id: int) -> bool:
    return await _delete("tasks", task_id)


async def get_overdue_tasks() -> List[Dict[str, Any]]:
    return await _fetch(
        "SELECT * FROM tasks WHERE status != 'done' AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date ASC",
        (datetime.utcnow().isoformat(),),
    )


# ── Scheduled Tasks ──────────────────────────────────────────────────────────
async def create_scheduled_task(task_id: int, cron_expr: str) -> int:
    return await _insert("scheduled_tasks", task_id=task_id, cron_expr=cron_expr)


async def get_scheduled_tasks() -> List[Dict[str, Any]]:
    return await _fetch(
        "SELECT st.*, t.title, t.description FROM scheduled_tasks st JOIN tasks t ON st.task_id = t.id WHERE st.enabled = 1")


async def update_scheduled_task(sched_id: int, **kwargs: Any) -> bool:
    return await _update("scheduled_tasks", sched_id, {"enabled", "last_run", "next_run", "cron_expr"}, **kwargs)


async def delete_scheduled_task(sched_id: int) -> bool:
    return await _delete("scheduled_tasks", sched_id)


# ── Calendar Tasks ───────────────────────────────────────────────────────────
async def create_calendar_task(title: str, due_date: str, description: str = "", due_time: Optional[str] = None, priority: str = "medium", recurrence: str = "none") -> int:
    return await _insert("calendar_tasks", title=title, due_date=due_date, description=description, due_time=due_time, priority=priority, recurrence=recurrence)


async def get_calendar_tasks() -> List[Dict[str, Any]]:
    return await _fetch("SELECT * FROM calendar_tasks ORDER BY due_date ASC, due_time ASC")


async def update_calendar_task(task_id: int, **kwargs: Any) -> bool:
    kwargs.setdefault("updated_at", datetime.utcnow().isoformat())
    return await _update("calendar_tasks", task_id, {"title", "description", "due_date", "due_time", "priority", "recurrence", "status"}, **kwargs)


async def delete_calendar_task(task_id: int) -> bool:
    return await _delete("calendar_tasks", task_id)


# ── Settings ─────────────────────────────────────────────────────────────────
async def get_setting(key: str) -> Optional[str]:
    row = await _fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else None


async def set_setting(key: str, value: str) -> None:
    await _execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)", (key, value, datetime.utcnow().isoformat()))


async def get_all_settings() -> Dict[str, str]:
    rows = await _fetch("SELECT key, value FROM settings")
    return {r["key"]: r["value"] for r in rows}


# ── Agents ───────────────────────────────────────────────────────────────────
async def create_agent(name: str, description: str = "", system_prompt: str = "", model: Optional[str] = None, tools: Optional[List[str]] = None) -> int:
    return await _insert("agents", name=name, description=description, system_prompt=system_prompt, model=model, tools=json.dumps(tools or []))


async def get_agents() -> List[Dict[str, Any]]:
    rows = await _fetch("SELECT * FROM agents ORDER BY created_at DESC")
    for r in rows:
        r["tools"] = json.loads(r.get("tools", "[]"))
    return rows


async def get_agent(agent_id: int) -> Optional[Dict[str, Any]]:
    row = await _fetch_one("SELECT * FROM agents WHERE id = ?", (agent_id,))
    if row:
        row["tools"] = json.loads(row.get("tools", "[]"))
    return row


async def update_agent(agent_id: int, **kwargs: Any) -> bool:
    allowed = {"name", "description", "system_prompt", "model", "tools", "personality", "memory"}
    updates: Dict[str, Any] = {}
    for k, v in kwargs.items():
        if k in allowed and v is not None:
            updates[k] = json.dumps(v) if k == "tools" and isinstance(v, list) else v
    if not updates:
        return False
    updates["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    await _execute(f"UPDATE agents SET {set_clause} WHERE id = ?", tuple(updates.values()) + (agent_id,))
    return True


async def delete_agent(agent_id: int) -> bool:
    return await _delete("agents", agent_id)


# ── Memory ───────────────────────────────────────────────────────────────────
async def save_memory_entry(content: str, session_id: Optional[str] = None, category: str = "general", embedding_id: Optional[str] = None) -> int:
    eid = embedding_id or str(uuid.uuid4())
    return await _insert("memory_entries", session_id=session_id, content=content, category=category, embedding_id=eid)


async def get_memory_entries(session_id: Optional[str] = None, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conditions: List[str] = []
    params: List[Any] = []
    if session_id:
        conditions.append("session_id = ?")
        params.append(session_id)
    if category:
        conditions.append("category = ?")
        params.append(category)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    return await _fetch(f"SELECT * FROM memory_entries{where} ORDER BY created_at DESC LIMIT ?", params + [limit])


# ── Agent Runs ───────────────────────────────────────────────────────────────
async def save_agent_run(agent_id: int, session_id: str, intent: str, model: str, input_text: str, output_text: str, duration_ms: int = 0, status: str = "success") -> int:
    return await _insert("agent_runs", agent_id=agent_id, session_id=session_id, intent=intent, model=model, input_text=input_text, output_text=output_text, duration_ms=duration_ms, status=status)


async def get_agent_runs(limit: int = 20) -> List[Dict[str, Any]]:
    return await _fetch(
        "SELECT ar.*, a.name as agent_name FROM agent_runs ar LEFT JOIN agents a ON ar.agent_id = a.id ORDER BY ar.created_at DESC LIMIT ?", (limit,))


async def get_last_agent_run() -> Optional[Dict[str, Any]]:
    return await _fetch_one(
        "SELECT ar.*, a.name as agent_name FROM agent_runs ar LEFT JOIN agents a ON ar.agent_id = a.id ORDER BY ar.created_at DESC LIMIT 1")


# ── Research ─────────────────────────────────────────────────────────────────
async def create_research_run(topic: str, mode: str = "balanced") -> int:
    await _execute("DELETE FROM research_runs WHERE topic = ? AND status = 'running'", (topic,))
    research_type = "deep" if mode == "deep" else "standard"
    return await _insert("research_runs", topic=topic, mode=mode, type=research_type)


async def update_research_run(run_id: int, **kwargs: Any) -> bool:
    return await _update("research_runs", run_id, {"status", "sources_count", "report_html", "report", "report_path", "error", "completed_at", "type", "outline", "progress", "report_docx_path"}, **kwargs)


async def get_research_runs(status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    if status:
        return await _fetch("SELECT * FROM research_runs WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
    return await _fetch("SELECT * FROM research_runs ORDER BY created_at DESC LIMIT ?", (limit,))


async def get_research_run(run_id: int) -> Optional[Dict[str, Any]]:
    return await _fetch_one("SELECT * FROM research_runs WHERE id = ?", (run_id,))


async def get_next_queued_run() -> Optional[Dict[str, Any]]:
    return await _fetch_one("SELECT * FROM research_runs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1")


async def delete_research_run(run_id: int) -> bool:
    return await _delete("research_runs", run_id)


# ── Automations ────────────────────────────────────────────────────────────
async def create_automation(name: str, instructions: str, schedule_time: str, timezone: str = "UTC") -> int:
    return await _insert("automations", name=name, instructions=instructions, schedule_time=schedule_time, timezone=timezone)


async def get_automations(active_only: bool = False) -> List[Dict[str, Any]]:
    if active_only:
        return await _fetch("SELECT * FROM automations WHERE active = 1 ORDER BY created_at DESC")
    return await _fetch("SELECT * FROM automations ORDER BY created_at DESC")


async def get_automation(automation_id: int) -> Optional[Dict[str, Any]]:
    return await _fetch_one("SELECT * FROM automations WHERE id = ?", (automation_id,))


async def update_automation(automation_id: int, **kwargs: Any) -> bool:
    return await _update("automations", automation_id, {"name", "instructions", "schedule_time", "timezone", "active", "last_run_at"}, **kwargs)


async def delete_automation(automation_id: int) -> bool:
    await _delete("briefing_runs", automation_id)
    return await _delete("automations", automation_id)


# ── Briefing Runs ──────────────────────────────────────────────────────────
async def create_briefing_run(automation_id: int) -> int:
    return await _insert("briefing_runs", automation_id=automation_id, status="pending", started_at=datetime.utcnow().isoformat())


async def update_briefing_run(run_id: int, **kwargs: Any) -> bool:
    return await _update("briefing_runs", run_id, {"status", "completed_at", "pdf_path", "error_message"}, **kwargs)


async def get_briefing_runs(automation_id: int) -> List[Dict[str, Any]]:
    return await _fetch("SELECT * FROM briefing_runs WHERE automation_id = ? ORDER BY started_at DESC", (automation_id,))


async def get_briefing_run(run_id: int) -> Optional[Dict[str, Any]]:
    return await _fetch_one("SELECT * FROM briefing_runs WHERE id = ?", (run_id,))
