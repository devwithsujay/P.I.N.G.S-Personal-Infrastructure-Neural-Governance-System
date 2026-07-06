import os
import uuid
import logging
import base64
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import settings
from core.schemas import (
    HealthResponse, ChatRequest, ChatResponse, HistoryEntry, SessionInfo,
    HomelabStatus, ContainerInfo, TaskCreate, TaskUpdate, TaskOut,
    UploadResponse, ExportRequest, SettingsUpdate, AgentCreate, AgentUpdate,
    AgentOut, ModelsResponse, ModelInfo,
)
from core.memory.db import (
    init_db, save_message, get_session_messages, get_all_sessions, delete_session, delete_all_sessions,
    create_task, get_tasks, get_task, update_task, delete_task, get_overdue_tasks,
    get_setting, set_setting, get_all_settings, create_agent, get_agents, get_agent,
    update_agent, delete_agent, save_agent_run, get_agent_runs, get_last_agent_run,
    update_research_run, get_research_runs, get_research_run,
    delete_research_run,
    create_calendar_task, get_calendar_tasks, update_calendar_task, delete_calendar_task,
)
from core.memory.persistent import add_knowledge, search_knowledge, get_memory_stats
from core.memory.seed import seed_chroma_on_startup
from core.persona.loader import load_persona, build_system_prompt, watch_persona_files

from core.agents.router import dispatch, classify_intent
from core.agents.opencode_engine import run_opencode_task
from core.tools.ssh import test_ssh_connection, run_ssh_command, get_ssh_config_from_db
from core.tools.system import list_containers, control_container, get_container_stats
from core.tools.browser import web_search, fetch_url
from core.tools.file_tool import read_file, write_file, list_files
from core.tools.security import is_action_safe, get_dangerous_patterns

logger = logging.getLogger("pings.main")

app = FastAPI(
    title="P.I.N.G.S Core v2",
    description="Personal Intelligent Neural Gateway System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

persona_cache: Dict[str, Any] = {}


DEFAULT_AGENTS = [
    {"name": "pings", "description": "Default general-purpose agent for conversation and QA", "system_prompt": "You are the primary P.I.N.G.S agent. Handle all general conversation, questions, and fallback tasks.", "model": "opencode/mimo-v2.5-free"},
    {"name": "coder", "description": "Code generation, scaffolding, and technical development", "system_prompt": "You are a senior backend engineer who writes clean, production-ready code with proper error handling, type hints, and documentation.", "model": "opencode/deepseek-v4-flash-free"},
    {"name": "researcher", "description": "Research and analysis with web search", "system_prompt": "You are an analytical researcher. Investigate topics deeply, compare alternatives, and provide data-driven insights.", "model": "opencode/mimo-v2.5-free"},
    {"name": "planner", "description": "Task planning, scheduling, and time management", "system_prompt": "You are a planning assistant. Help organize tasks, set priorities, and manage schedules.", "model": "opencode/north-mini-code-free"},
    {"name": "homelab-monitor", "description": "Infrastructure monitoring and SSH operations", "system_prompt": "You are an infrastructure monitoring agent. Check server health, Docker containers, and system resources.", "model": "opencode/north-mini-code-free"},
    {"name": "creative", "description": "Creative writing, brainstorming, and ideation", "system_prompt": "You are a creative writing assistant. Be imaginative, expressive, and use vivid language with original ideas.", "model": "opencode/mimo-v2.5-free"},
]


async def seed_default_agents() -> None:
    existing = await get_agents()
    existing_names = {a["name"] for a in existing}
    for agent in DEFAULT_AGENTS:
        if agent["name"] not in existing_names:
            await create_agent(
                name=agent["name"],
                description=agent["description"],
                system_prompt=agent["system_prompt"],
                model=agent["model"],
            )
            logger.info(f"Seeded agent: {agent['name']}")
        else:
            logger.debug(f"Agent already exists: {agent['name']}")


@app.on_event("startup")
async def startup_event() -> None:
    global persona_cache
    logger.info("Starting P.I.N.G.S Core v2...")
    await init_db()
    logger.info("Database initialized")

    try:
        await seed_default_agents()
        logger.info("Default agents seeded")
    except Exception as e:
        logger.warning(f"Agent seeding failed (non-fatal): {e}")

    try:
        await seed_chroma_on_startup()
    except Exception as e:
        logger.warning(f"ChromaDB seed failed (non-fatal): {e}")

    persona_cache = load_persona()
    logger.info("Persona loaded")

    def _reload_persona():
        global persona_cache
        persona_cache = load_persona()
        logger.info("Persona reloaded from disk")

    watch_persona_files(_reload_persona)
    logger.info("Persona file watcher started")




@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("P.I.N.G.S Core v2 stopped")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


async def verify_api_key(request: Request) -> bool:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        if token == settings.BRAIN_SECRET_KEY:
            return True
    api_key = request.headers.get("X-API-Key", "")
    if api_key == settings.BRAIN_SECRET_KEY:
        return True
    api_key_query = request.query_params.get("api_key", "")
    if api_key_query == settings.BRAIN_SECRET_KEY:
        return True
    return False


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    services: Dict[str, str] = {"api": "healthy"}
    try:
        from core.memory.chroma import chroma_memory
        chroma_health = await chroma_memory.health_check()
        services["chroma"] = chroma_health.get("status", "unknown")
    except Exception:
        services["chroma"] = "unavailable"
    return HealthResponse(status="ok", services=services)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, authorized: bool = Depends(verify_api_key)) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    model = request.model or settings.DEFAULT_ZEN_MODEL

    await save_message(session_id, "user", request.message)

    global persona_cache
    if not persona_cache:
        persona_cache = load_persona()
    system_prompt = build_system_prompt(persona_cache)

    response_text, intent = await dispatch(
        request.message, session_id, system_prompt, persona_cache, model=model
    )

    await save_message(session_id, "assistant", response_text, intent=intent, model=model)

    return ChatResponse(
        reply=response_text,
        session_id=session_id,
        intent=intent,
        model_used=model,
    )


@app.post("/chat/upload", response_model=ChatResponse)
async def chat_upload(
    message: str = Form(""),
    session_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    authorized: bool = Depends(verify_api_key),
) -> ChatResponse:
    global persona_cache
    sid = session_id or str(uuid.uuid4())
    content = await file.read()
    filename = file.filename or ""

    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    is_image = any(filename.lower().endswith(ext) for ext in image_extensions)
    is_pdf = filename.lower().endswith(".pdf")

    if is_image:
        image_b64 = base64.b64encode(content).decode("utf-8")
        ext = filename.rsplit('.', 1)[-1].lower()
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        extra_parts = [{"type": "file", "mime": f"image/{mime}", "url": f"data:image/{mime};base64,{image_b64}", "filename": filename}]
        user_log = f"[Image: {filename}] {message}"
    elif is_pdf:
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            doc.close()
            extra_parts = [{"type": "file", "mime": "image/png", "url": f"data:image/png;base64,{img_b64}", "filename": f"{filename}.png"}]
            if text.strip():
                message = f"{message}\n\n--- OCR text from PDF: {filename} ---\n{text[:3000]}"
            user_log = f"[PDF: {filename}] {message}"
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            text_content = content.decode("utf-8", errors="replace")
            message = f"{message}\n\n--- Uploaded PDF (raw): {filename} ---\n{text_content[:5000]}"
            extra_parts = None
            user_log = f"[PDF: {filename}] {message}"
    else:
        text_content = content.decode("utf-8", errors="replace")
        combined_message = f"{message}\n\n--- Uploaded file: {filename} ---\n{text_content[:5000]}"

        if not persona_cache:
            persona_cache = load_persona()
        system_prompt = build_system_prompt(persona_cache)
        response_text, intent = await dispatch(combined_message, sid, system_prompt, persona_cache)
        await save_message(sid, "user", f"[Upload: {filename}] {message}")
        await save_message(sid, "assistant", response_text, intent=intent)
        return ChatResponse(reply=response_text, session_id=sid, intent=intent)

    if not persona_cache:
        persona_cache = load_persona()
    system_prompt = build_system_prompt(persona_cache)
    prompt_text = message or "Describe this image in detail."
    response_text, intent = await dispatch(prompt_text, sid, system_prompt, persona_cache, extra_parts=extra_parts)

    await save_message(sid, "user", user_log)
    await save_message(sid, "assistant", response_text, intent=intent)

    return ChatResponse(reply=response_text, session_id=sid, intent=intent)


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form(""),
    authorized: bool = Depends(verify_api_key),
) -> UploadResponse:
    content = await file.read()
    text_content = content.decode("utf-8", errors="replace")

    target_path = path if path else file.filename or "uploaded_file"
    result = await write_file(target_path, text_content)

    return UploadResponse(
        filename=file.filename or "unknown",
        path=target_path,
        size=len(content),
    )


@app.get("/sessions", response_model=List[SessionInfo])
async def get_sessions() -> List[SessionInfo]:
    sessions = await get_all_sessions()
    return [
        SessionInfo(
            session_id=s["session_id"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=s["message_count"],
            title=s.get("title"),
        )
        for s in sessions
    ]


@app.get("/sessions/{session_id}", response_model=List[HistoryEntry])
async def get_session(session_id: str) -> List[HistoryEntry]:
    messages = await get_session_messages(session_id)
    return [
        HistoryEntry(
            id=m["id"],
            session_id=m["session_id"],
            role=m["role"],
            content=m["content"],
            timestamp=m["timestamp"],
            intent=m.get("intent"),
        )
        for m in messages
    ]


@app.get("/history/{session_id}", response_model=List[HistoryEntry])
async def get_history(session_id: str) -> List[HistoryEntry]:
    return await get_session(session_id)


@app.delete("/history")
async def clear_all_history() -> Dict[str, str]:
    success = await delete_all_sessions()
    return {"status": "cleared"}


@app.delete("/history/{session_id}")
async def delete_history(session_id: str) -> Dict[str, str]:
    success = await delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


@app.get("/tasks", response_model=List[TaskOut])
async def list_tasks(status: Optional[str] = Query(None)) -> List[TaskOut]:
    tasks = await get_tasks(status)
    return [TaskOut(**t) for t in tasks]


@app.post("/tasks", response_model=TaskOut)
async def create_new_task(task: TaskCreate) -> TaskOut:
    task_id = await create_task(task.title, task.description, task.priority, task.due_date)
    created = await get_task(task_id)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create task")
    return TaskOut(**created)


@app.put("/tasks/{task_id}", response_model=TaskOut)
async def update_existing_task(task_id: int, update: TaskUpdate) -> TaskOut:
    kwargs = update.model_dump(exclude_none=True)
    success = await update_task(task_id, **kwargs)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(**task)


@app.delete("/tasks/{task_id}")
async def delete_existing_task(task_id: int) -> Dict[str, str]:
    success = await delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "task_id": str(task_id)}


@app.get("/schedule")
async def list_schedule() -> List[Dict[str, Any]]:
    from core.memory.db import get_scheduled_tasks
    return await get_scheduled_tasks()


@app.post("/schedule")
async def create_schedule(task_id: int = Form(...), cron_expr: str = Form(...)) -> Dict[str, Any]:
    from core.memory.db import create_scheduled_task
    sched_id = await create_scheduled_task(task_id, cron_expr)
    return {"id": sched_id, "task_id": task_id, "cron_expr": cron_expr}


@app.delete("/schedule/{sched_id}")
async def delete_schedule(sched_id: int) -> Dict[str, str]:
    from core.memory.db import delete_scheduled_task
    success = await delete_scheduled_task(sched_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted", "schedule_id": str(sched_id)}


class CalendarTaskIn(BaseModel):
    title: str
    description: str = ""
    due_date: str
    due_time: Optional[str] = None
    priority: str = "medium"
    recurrence: str = "none"


@app.get("/calendar")
async def list_calendar_tasks() -> List[Dict[str, Any]]:
    return await get_calendar_tasks()


@app.post("/calendar")
async def create_calendar_task_endpoint(task: CalendarTaskIn) -> Dict[str, Any]:
    task_id = await create_calendar_task(
        title=task.title,
        due_date=task.due_date,
        description=task.description,
        due_time=task.due_time,
        priority=task.priority,
        recurrence=task.recurrence,
    )
    return {"id": task_id, "title": task.title, "due_date": task.due_date}


@app.put("/calendar/{task_id}")
async def update_calendar_task_endpoint(task_id: int, task: CalendarTaskIn) -> Dict[str, Any]:
    success = await update_calendar_task(
        task_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        due_time=task.due_time,
        priority=task.priority,
        recurrence=task.recurrence,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": task_id, "status": "updated"}


@app.delete("/calendar/{task_id}")
async def delete_calendar_task_endpoint(task_id: int) -> Dict[str, str]:
    success = await delete_calendar_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "task_id": str(task_id)}


@app.get("/homelab/status", response_model=HomelabStatus)
async def homelab_status() -> HomelabStatus:
    ssh_cfg = await get_ssh_config_from_db()
    conn = await test_ssh_connection()
    containers: List[ContainerInfo] = []
    if conn["success"]:
        output = await list_containers()
        for line in output.split("\n"):
            if line.strip() and ("🟢" in line or "🔴" in line):
                parts = line.split("|")
                if len(parts) >= 3:
                    name = parts[0].replace("🟢", "").replace("🔴", "").strip()
                    status_str = "running" if ("running" in line.lower() or "🟢" in line) else "stopped"
                    containers.append(ContainerInfo(
                        name=name,
                        status=status_str,
                        image=parts[2].strip(),
                    ))

    return HomelabStatus(
        host_reachable=conn["success"],
        containers=containers,
        ssh_user=ssh_cfg.get("user", ""),
        ssh_host=ssh_cfg.get("host", ""),
    )


@app.post("/homelab/ssh/test")
async def ssh_test(config: Dict[str, Any] = {}) -> Dict[str, Any]:
    result = await test_ssh_connection(config if config else None)
    return result


@app.put("/homelab/ssh")
async def save_ssh_config(config: Dict[str, Any]) -> Dict[str, str]:
    for key, value in config.items():
        setting_key = f"SSH_{key.upper()}"
        await set_setting(setting_key, str(value))
    return {"status": "saved"}


@app.post("/homelab/ssh/exec")
async def ssh_exec(command: str = Form(...)) -> Dict[str, str]:
    safe, reason = is_action_safe(command)
    if not safe:
        raise HTTPException(status_code=403, detail=reason)
    result = await run_ssh_command(command)
    return {"output": result}


@app.get("/homelab/containers")
async def homelab_containers() -> Dict[str, str]:
    output = await list_containers()
    return {"containers": output}


@app.post("/homelab/containers/{action}/{name}")
async def homelab_container_action(action: str, name: str) -> Dict[str, str]:
    if action not in ("start", "stop", "restart", "logs", "status"):
        raise HTTPException(status_code=400, detail="Invalid action")
    result = await control_container(action, name)
    return {"output": result}


@app.get("/homelab/stats")
async def homelab_stats() -> Dict[str, str]:
    output = await get_container_stats()
    return {"stats": output}


@app.get("/agents", response_model=List[AgentOut])
async def list_agents() -> List[AgentOut]:
    agents = await get_agents()
    return [AgentOut(**a) for a in agents]


@app.post("/agents", response_model=AgentOut)
async def create_new_agent(agent: AgentCreate) -> AgentOut:
    agent_id = await create_agent(agent.name, agent.description, agent.system_prompt, agent.model, agent.tools)
    created = await get_agent(agent_id)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create agent")
    return AgentOut(**created)


@app.put("/agents/{agent_id}", response_model=AgentOut)
async def update_existing_agent(agent_id: int, update: AgentUpdate) -> AgentOut:
    kwargs = update.model_dump(exclude_none=True)
    success = await update_agent(agent_id, **kwargs)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = await get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentOut(**agent)


@app.delete("/agents/{agent_id}")
async def delete_existing_agent(agent_id: int) -> Dict[str, str]:
    success = await delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "deleted", "agent_id": str(agent_id)}


@app.put("/agents/{agent_id}/personality")
async def update_agent_personality(agent_id: int, personality: str = Form(...)) -> Dict[str, str]:
    success = await update_agent(agent_id, personality=personality)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "updated"}


@app.put("/agents/{agent_id}/memory")
async def update_agent_memory(agent_id: int, memory: str = Form(...)) -> Dict[str, str]:
    success = await update_agent(agent_id, memory=memory)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "updated"}


@app.get("/memory/search")
async def memory_search(q: str = Query(...), n: int = Query(5)) -> List[Dict[str, Any]]:
    results = await search_knowledge(q, n_results=n)
    return results


@app.get("/knowledge")
async def get_knowledge_entries() -> Dict[str, Any]:
    stats = await get_memory_stats()
    return {
        "total_entries": stats.get("total_entries", 0),
        "categories": stats.get("categories", {}),
        "chroma_status": stats.get("chroma_status", "unknown"),
        "sqlite_status": stats.get("sqlite_status", "healthy"),
    }


@app.post("/knowledge")
async def add_knowledge_entry(content: str = Form(...), category: str = Form("general")) -> Dict[str, str]:
    entry_id = await add_knowledge(content, category)
    return {"id": entry_id, "status": "added"}


@app.get("/agent-runs")
async def list_agent_runs(limit: int = Query(20)) -> List[Dict[str, Any]]:
    return await get_agent_runs(limit)


@app.get("/agent-runs/last")
async def last_agent_runs() -> List[Dict[str, Any]]:
    async with get_db_ctx() as db:
        cursor = await db.execute(
            """SELECT ar.*, a.name as agent_name FROM agent_runs ar
            LEFT JOIN agents a ON ar.agent_id = a.id
            WHERE ar.id IN (SELECT MAX(id) FROM agent_runs GROUP BY agent_id)
            ORDER BY ar.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@app.get("/research/queue")
async def research_queue() -> List[Dict[str, Any]]:
    return await get_research_runs(status="queued")


@app.get("/research/runs")
async def list_research_runs() -> List[Dict[str, Any]]:
    return await get_research_runs()


@app.get("/research/runs/{run_id}")
async def get_research(run_id: int) -> Dict[str, Any]:
    run = await get_research_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@app.delete("/research/runs/{run_id}")
async def delete_research(run_id: int) -> Dict[str, Any]:
    run = await get_research_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    await delete_research_run(run_id)
    return {"status": "deleted", "run_id": run_id}


@app.post("/research/discuss")
async def discuss_research(request: Dict[str, Any]) -> Dict[str, Any]:
    run_id = request.get("run_id")
    message = request.get("message", "")
    run = await get_research_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    topic = run.get("topic", "")
    system_prompt = f"You are a research assistant discussing the topic: {topic}"
    response = await run_opencode_task(
        prompt=f"Based on this research on '{topic}', answer: {message}",
        system_prompt=system_prompt,
        timeout=90,
    )
    return {"response": response}


@app.get("/research/{run_id}")
async def get_research_legacy(run_id: int) -> Dict[str, Any]:
    run = await get_research_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@app.get("/research/{run_id}/report.html", response_class=HTMLResponse)
async def get_research_report(run_id: int) -> HTMLResponse:
    run = await get_research_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    html = run.get("report_html", "<html><body><p>No report available</p></body></html>")
    return HTMLResponse(content=html)


@app.get("/settings")
async def get_settings() -> Dict[str, str]:
    settings_data = await get_all_settings()
    sensitive_keys = {"SSH_PASSWORD", "TELEGRAM_BOT_TOKEN", "BRAIN_SECRET_KEY", "NVIDIA_API_KEY", "SERPAPI_KEY"}
    masked = {}
    for k, v in settings_data.items():
        if k in sensitive_keys and v:
            masked[k] = v[:4] + "****" if len(v) > 4 else "****"
        else:
            masked[k] = v
    return masked


@app.put("/settings")
async def update_settings(update: SettingsUpdate) -> Dict[str, str]:
    await set_setting(update.key, update.value)
    return {"status": "updated", "key": update.key}


@app.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    models = [
        ModelInfo(id="opencode/mimo-v2.5-free", name="MiMo V2.5 Free", provider="zen", context_window=32768, is_default=True),
        ModelInfo(id="opencode/deepseek-v4-flash-free", name="DeepSeek V4 Flash Free", provider="zen", context_window=32768),
        ModelInfo(id="opencode/nemotron-3-ultra-free", name="Nemotron 3 Ultra Free", provider="zen", context_window=32768),
        ModelInfo(id="opencode/big-pickle", name="Big Pickle", provider="zen", context_window=32768),
        ModelInfo(id="opencode/north-mini-code-free", name="North Mini Code Free", provider="zen", context_window=32768),
    ]
    return ModelsResponse(models=models, default=settings.DEFAULT_ZEN_MODEL)


@app.get("/models/default")
async def get_default_model() -> Dict[str, str]:
    return {"model": settings.DEFAULT_ZEN_MODEL}


@app.put("/models/default")
async def set_default_model(model: str = Form(...)) -> Dict[str, str]:
    settings.DEFAULT_ZEN_MODEL = model
    return {"status": "updated", "model": model}


@app.get("/skills")
async def list_skills() -> List[Dict[str, str]]:
    return [
        {"name": "ssh", "description": "Execute SSH commands on remote server"},
        {"name": "browser", "description": "Search the web and fetch content"},
        {"name": "system", "description": "Manage Docker containers"},
        {"name": "files", "description": "Read/write/list workspace files"},
    ]


@app.post("/export")
async def export_data(request: ExportRequest) -> Dict[str, Any]:
    if request.session_id:
        messages = await get_session_messages(request.session_id)
        return {"session_id": request.session_id, "messages": messages, "format": request.format}
    sessions = await get_all_sessions()
    return {"sessions": sessions, "format": request.format}


@app.get("/patterns")
async def get_patterns() -> Dict[str, List[str]]:
    return {"danger_patterns": get_dangerous_patterns()}


@app.get("/suggestions")
async def get_suggestions() -> List[Dict[str, Any]]:
    return [
        {"id": 1, "text": "What's the status of my homelab?"},
        {"id": 2, "text": "Create a task to update Docker containers"},
        {"id": 3, "text": "Search for best practices in Python async"},
        {"id": 4, "text": "Generate a backup script"},
        {"id": 5, "text": "Write a research report on quantum computing"},
    ]


@app.get("/persona/journal")
async def get_journal() -> Dict[str, str]:
    journal_path = Path(settings.JOURNAL_PATH)
    if journal_path.exists():
        content = journal_path.read_text(encoding="utf-8")
        return {"journal": content}
    return {"journal": ""}


@app.post("/persona/reload")
async def reload_persona() -> Dict[str, str]:
    global persona_cache
    persona_cache = load_persona()
    return {"status": "reloaded"}


@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "name": "P.I.N.G.S Core v2",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }
