import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("pings.agents.router")

INTENT_PATTERNS: Dict[str, List[str]] = {
    "homelab": [
        r"container", r"docker", r"server", r"homelab", r"ssh",
        r"restart\s+\w+", r"stop\s+\w+", r"start\s+\w+", r"status\s+of",
        r"list\s+containers", r"docker\s+ps", r"system\s+check",
        r"n8n", r"running", r"up\s+on",
    ],
    "tasks": [
        r"task", r"todo", r"reminder", r"deadline", r"schedule",
        r"create\s+task", r"add\s+task", r"my\s+tasks", r"overdue",
        r"due\s+date", r"priority", r"pending",
    ],
    "codegen": [
        r"code", r"generate", r"write\s+code", r"script", r"function",
        r"python", r"javascript", r"bash\s+script", r"program",
        r"implement", r"class", r"api\s+endpoint",
        r"scaffold", r"project", r"file", r"create\s+a",
        r"build\s+a", r"make\s+a", r"setup\s+a",
    ],
    "report": [
        r"report", r"document", r"pdf", r"format", r"write\s+up",
        r"summary", r"vtu", r"assignment", r"essay",
    ],
    "research": [
        r"research", r"investigate", r"deep\s+dive", r"analyze",
        r"compare", r"evaluate", r"study", r"report\s+on",
    ],
    "browse": [
        r"search", r"look\s+up", r"find\s+online", r"google",
        r"who\s+is", r"how\s+to", r"browse",
        r"what\s+is", r"what\s+are", r"what's",
    ],
    "host": [
        r"my\s+ip", r"ip\s+address", r"create\s+(a\s+)?folder",
        r"make\s+(a\s+)?folder", r"create\s+(a\s+)?directory",
        r"delete\s+(the\s+)?(folder|file|directory|path)",
        r"remove\s+(the\s+)?(folder|file|directory|path)",
        r"list\s+(the\s+)?(contents?\s+of|folder|directory)",
        r"run\s+command", r"execute\s+command",
        r"what\s+is\s+my", r"whats\s+my",
    ],
}

AGENT_ROLES: Dict[str, Dict[str, Any]] = {
    "pings": {
        "role": "general-purpose digital twin",
        "model": "opencode/mimo-v2.5-free",
        "description": "Default agent for general conversation and QA",
    },
    "coder": {
        "role": "technical-dev",
        "model": "opencode/deepseek-v4-flash-free",
        "description": "Code generation, scaffolding, and technical development",
    },
    "researcher": {
        "role": "analytical",
        "model": "opencode/mimo-v2.5-free",
        "description": "Research, analysis, and deep investigation",
    },
    "planner": {
        "role": "tasks-scheduling",
        "model": "opencode/north-mini-code-free",
        "description": "Task planning, scheduling, and time management",
    },
    "homelab-monitor": {
        "role": "infrastructure",
        "model": "opencode/north-mini-code-free",
        "description": "Infrastructure monitoring and SSH operations",
    },
    "creative": {
        "role": "writing-brainstorming",
        "model": "opencode/mimo-v2.5-free",
        "description": "Creative writing, brainstorming, and ideation",
    },
}

AGENT_ALIASES: Dict[str, str] = {
    "@pings": "pings",
    "@coder": "coder",
    "@researcher": "researcher",
    "@planner": "planner",
    "@homelab": "homelab-monitor",
    "@homelab-monitor": "homelab-monitor",
    "@creative": "creative",
}


def classify_intent(message: str) -> str:
    msg_lower = message.lower()
    scores: Dict[str, int] = {}

    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                score += 1
        if score > 0:
            scores[intent] = score

    if not scores:
        return "qa"

    best_intent = max(scores, key=scores.get or 0)
    return best_intent


def extract_agent_mention(message: str) -> Tuple[Optional[str], str]:
    for alias, agent_id in sorted(AGENT_ALIASES.items(), key=lambda x: -len(x[0])):
        if message.lower().startswith(alias):
            stripped = message[len(alias):].strip()
            return agent_id, stripped
    return None, message


def is_explicit_model(model: Optional[str]) -> bool:
    return model is not None and model != ""


async def dispatch_to_agent(agent_id: str, message: str, session_id: str, persona: Optional[Dict[str, str]] = None, model: Optional[str] = None, extra_parts: Optional[List[Dict[str, Any]]] = None) -> str:
    agent_config = AGENT_ROLES.get(agent_id)
    if not agent_config:
        from core.agents.opencode_engine import run_opencode_task
        return await run_opencode_task(message, "", model=model, extra_parts=extra_parts)

    agent_model = model if is_explicit_model(model) else agent_config["model"]
    role = agent_config["role"]
    identity = (persona or {}).get("identity", "")

    agent_prompt = f"You are the {agent_id} agent of P.I.N.G.S. Your role is: {role}.\n"
    if identity:
        agent_prompt += f"\n{identity}"

    if agent_id == "planner":
        from core.agents.tasks import handle_tasks
        return await handle_tasks(message, agent_prompt)
    elif agent_id == "homelab-monitor":
        from core.agents.homelab import handle_homelab
        return await handle_homelab(message, agent_prompt)
    elif agent_id == "creative":
        from core.agents.opencode_engine import run_opencode_task
        creative_prompt = f"{agent_prompt}\n\nBe creative, imaginative, and expressive. Use vivid language and original ideas."
        return await run_opencode_task(message, creative_prompt, model=agent_model, extra_parts=extra_parts)
    else:
        from core.agents.opencode_engine import run_opencode_task
        return await run_opencode_task(message, agent_prompt, model=agent_model, extra_parts=extra_parts)


async def dispatch(message: str, session_id: str, system_prompt: str, persona: Optional[Dict[str, str]] = None, model: Optional[str] = None, extra_parts: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, str]:
    agent_id, clean_message = extract_agent_mention(message)
    if agent_id:
        logger.info(f"Agent mention detected: @{agent_id}, message: {clean_message[:60]}")
        response = await dispatch_to_agent(agent_id, clean_message, session_id, persona, model=model, extra_parts=extra_parts)
        return response, f"agent:{agent_id}"

    intent = classify_intent(clean_message)
    logger.info(f"Intent classified: {intent} for message: {clean_message[:80]}")

    from core.agents.opencode_engine import run_opencode_task, _parse_model

    if intent == "host":
        from core.tools.host import parse_host_action, exec_command, get_ip, create_folder, delete_path, list_directory
        action = parse_host_action(clean_message)
        if action == "get_ip":
            response = await get_ip()
        elif action and action.startswith("create_folder:"):
            path = action.split(":", 1)[1]
            response = await create_folder(path)
        elif action and action.startswith("delete_path:"):
            path = action.split(":", 1)[1]
            response = await delete_path(path)
        elif action and action.startswith("list_directory:"):
            path = action.split(":", 1)[1]
            response = await list_directory(path)
        elif action and action.startswith("exec:"):
            cmd = action.split(":", 1)[1]
            response = await exec_command(cmd)
        else:
            response = await exec_command(clean_message)
        return response, intent

    if intent == "homelab":
        from core.agents.homelab import handle_homelab
        response = await handle_homelab(clean_message, system_prompt)
        return response, intent

    if intent == "research":
        import asyncio
        from core.memory.db import create_research_run
        from core.agents.research import run_research
        topic = clean_message
        for prefix in ["research on ", "research about ", "research ", "deep research on ", "deep research about ", "deep research ", "investigate ", "analyze ", "study "]:
            if clean_message.lower().startswith(prefix):
                topic = clean_message[len(prefix):]
                break
        run_id = await create_research_run(topic, "deep")
        asyncio.create_task(run_research(topic, "deep", run_id=run_id))
        response = f"Research started on: {topic}\nRun ID: {run_id}\nThis will take ~15-20 minutes. I'll send the report when it's done."
        return response, intent

    provider_id, model_id = _parse_model(model) if model else (None, None)
    using_ollama = provider_id == "ollama"

    if using_ollama:
        logger.info(f"Explicit Ollama model selected, bypassing intent routing")
        response = await run_opencode_task(clean_message, system_prompt, model=model, extra_parts=extra_parts)
        return response, "qa"

    if intent == "tasks":
        from core.agents.tasks import handle_tasks
        response = await handle_tasks(clean_message, system_prompt)
    elif intent == "browse":
        from core.tools.browser import web_search
        query = clean_message
        for prefix in ["search for ", "search ", "look up ", "google "]:
            if clean_message.lower().startswith(prefix):
                query = clean_message[len(prefix):]
                break
        response = await web_search(query)
    else:
        response = await run_opencode_task(clean_message, system_prompt, model=model, extra_parts=extra_parts)

    return response, intent
