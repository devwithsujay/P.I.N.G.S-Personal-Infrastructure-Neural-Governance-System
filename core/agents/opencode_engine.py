import logging
import httpx
from typing import Any, Dict, List, Optional

from core.config import settings

logger = logging.getLogger("pings.agents.opencode")

OPENCODE_BASE_URL = settings.OPENCODE_SERVER_URL
OLLAMA_BASE_URL = "http://pings-ollama:11434"


async def _check_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OPENCODE_BASE_URL}/global/health")
            return resp.status_code == 200
    except Exception:
        return False


async def _create_session(title: str = "PINGS Task") -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{OPENCODE_BASE_URL}/session",
            json={"title": title},
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def _send_prompt(
    session_id: str,
    text: str,
    model: Optional[str] = None,
    extra_parts: Optional[List[Dict[str, Any]]] = None,
) -> str:
    model = model or settings.DEFAULT_ZEN_MODEL

    provider_id, model_id = _parse_model(model)

    parts = list(extra_parts) if extra_parts else []
    parts.append({"type": "text", "text": text})
    body: Dict[str, Any] = {"parts": parts}
    if provider_id and model_id:
        body["model"] = {"providerID": provider_id, "modelID": model_id}

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{OPENCODE_BASE_URL}/session/{session_id}/message",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

    parts = data.get("parts", [])
    text_parts = [p.get("text", "") for p in parts if p.get("type") == "text"]
    return "\n".join(text_parts) if text_parts else "No response from agent."


async def _call_ollama(prompt: str, model: str, system: str = "") -> str:
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 2048}
    }
    if system:
        body["system"] = system

    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=body)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()


def _parse_model(model: str) -> tuple[Optional[str], Optional[str]]:
    if "/" in model:
        parts = model.split("/", 1)
        return parts[0], parts[1]
    return "opencode", model


async def run_opencode_task(
    task: str,
    system_context: str = "",
    model: Optional[str] = None,
    tools: Optional[List[str]] = None,
    timeout: int = 120,
    extra_parts: Optional[List[Dict[str, Any]]] = None,
) -> str:
    model = model or settings.DEFAULT_ZEN_MODEL

    provider_id, model_id = _parse_model(model)

    if provider_id == "ollama":
        logger.info(f"ollama direct: model={model_id}, task={task[:80]}")
        try:
            result = await _call_ollama(task, model_id, system=system_context)
            return result
        except httpx.TimeoutException:
            logger.error("ollama timed out")
            return "Agent timed out. Ollama model may be too slow for this request."
        except Exception as e:
            logger.error(f"ollama error: {e}")
            return f"Agent error (Ollama): {str(e)}"

    prompt_parts = []
    if system_context:
        prompt_parts.append(f"Context:\n{system_context}")
    prompt_parts.append(f"Task: {task}")
    full_prompt = "\n\n".join(prompt_parts)

    logger.info(f"opencode sidecar: model={model}, task={task[:80]}")

    try:
        if not await _check_health():
            logger.error("opencode sidecar not healthy")
            return "Agent error: opencode sidecar is not responding."

        session_id = await _create_session(title=task[:60])
        logger.info(f"Created opencode session: {session_id}")

        result = await _send_prompt(session_id, full_prompt, model=model, extra_parts=extra_parts)
        return result

    except httpx.TimeoutException:
        logger.error("opencode sidecar timed out")
        return "Agent timed out. Try a simpler request."
    except httpx.HTTPStatusError as e:
        logger.error(f"opencode sidecar HTTP error: {e.response.status_code} {e.response.text[:200]}")
        return f"Agent error: HTTP {e.response.status_code}"
    except Exception as e:
        logger.error(f"opencode sidecar error: {e}")
        return f"Agent error: {str(e)}"


async def run_opencode_with_tools(
    task: str,
    system_context: str,
    model: Optional[str] = None,
    available_tools: Optional[List[Dict[str, str]]] = None,
) -> str:
    model = model or settings.DEFAULT_ZEN_MODEL

    tool_descriptions = ""
    if available_tools:
        tool_descriptions = "\nAvailable tools:\n"
        for t in available_tools:
            tool_descriptions += f"- {t.get('name', 'unknown')}: {t.get('description', '')}\n"

    full_context = system_context + tool_descriptions
    return await run_opencode_task(task, full_context, model=model)
