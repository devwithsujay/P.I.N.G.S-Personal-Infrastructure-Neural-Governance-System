import logging
import asyncio
from typing import Any, Dict, Optional

from core.tools.ssh import run_ssh_command, get_ssh_config_from_db
from core.tools.security import is_action_safe

logger = logging.getLogger("pings.tools.system")


async def list_containers() -> str:
    result = await run_ssh_command("docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}'")
    if result.startswith("[SSH Error]") or result.startswith("[exit"):
        return f"Failed to list containers: {result}"

    lines = ["Docker Containers:\n"]
    for line in result.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            name = parts[0]
            status = parts[1]
            image = parts[2]
            ports = parts[3] if len(parts) > 3 else ""
            emoji = "🟢" if "Up" in status else "🔴"
            lines.append(f"{emoji} {name} | {status} | {image} | {ports}")
    return "\n".join(lines) if len(lines) > 1 else "No containers found."


async def control_container(action: str, name: str) -> str:
    safe, reason = is_action_safe(f"docker {action} {name}")
    if not safe:
        return f"Action blocked: {reason}"

    if action == "start":
        cmd = f"docker start {name}"
    elif action == "stop":
        cmd = f"docker stop {name}"
    elif action == "restart":
        cmd = f"docker restart {name}"
    elif action == "pause":
        cmd = f"docker pause {name}"
    elif action == "unpause":
        cmd = f"docker unpause {name}"
    elif action == "logs":
        cmd = f"docker logs --tail 50 {name}"
    elif action == "status":
        cmd = f"docker inspect --format '{{{{.State.Status}}}}' {name}"
    else:
        return f"Unknown action: {action}"

    result = await run_ssh_command(cmd)
    return result


async def get_container_stats() -> str:
    result = await run_ssh_command(
        "docker stats --no-stream --format '{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}' 2>/dev/null || echo 'docker stats unavailable'"
    )
    if result.startswith("[SSH Error]") or result.startswith("[exit"):
        return f"Failed to get stats: {result}"

    lines = ["Container Resource Usage:\n"]
    for line in result.strip().split("\n"):
        if not line.strip() or line == "docker stats unavailable":
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            lines.append(f"📦 {parts[0]} | CPU: {parts[1]} | MEM: {parts[2]} | NET: {parts[3]}")
    return "\n".join(lines) if len(lines) > 1 else "No stats available."


