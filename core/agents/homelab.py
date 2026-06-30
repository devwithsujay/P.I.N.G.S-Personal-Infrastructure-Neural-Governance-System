import logging
import re
from typing import Any, Dict, Optional

from core.tools.ssh import run_ssh_command, test_ssh_connection
from core.tools.system import list_containers, control_container, get_container_stats

logger = logging.getLogger("pings.agents.homelab")


async def handle_homelab(message: str, system_prompt: str = "") -> str:
    msg_lower = message.lower()
    logger.info(f"HomeLab agent processing: {message[:100]}")

    if "status" in msg_lower and ("server" in msg_lower or "host" in msg_lower or "system" in msg_lower):
        return await _get_system_status()

    if "stats" in msg_lower or "resource" in msg_lower or "usage" in msg_lower:
        return await get_container_stats()

    if "list" in msg_lower or "all containers" in msg_lower or "docker ps" in msg_lower:
        return await list_containers()

    for action in ["restart", "stop", "start", "logs"]:
        if action in msg_lower:
            container_name = _extract_container_name(msg_lower, action)
            if container_name:
                return await control_container(action, container_name)
            return f"Please specify a container name. Example: {action} <container_name>"

    if "connect" in msg_lower or "test" in msg_lower or "ssh" in msg_lower:
        result = test_ssh_connection()
        if result["success"]:
            return f"SSH connection successful!\nServer info: {result.get('info', '')}"
        return f"SSH connection failed: {result.get('error', 'unknown')}"

    if "disk" in msg_lower or "space" in msg_lower:
        output = await run_ssh_command("df -h / && echo '---' && du -sh /var/* 2>/dev/null | sort -rh | head -5")
        return f"Disk Usage:\n{output}"

    if "memory" in msg_lower or "ram" in msg_lower:
        output = await run_ssh_command("free -h && echo '---' && top -bn1 | head -15")
        return f"Memory Usage:\n{output}"

    if "process" in msg_lower or "top" in msg_lower:
        output = await run_ssh_command("ps aux --sort=-%cpu | head -15")
        return f"Top Processes:\n{output}"

    if "network" in msg_lower or "connection" in msg_lower:
        output = await run_ssh_command("ss -tuln | head -20 && echo '---' && ip -br addr")
        return f"Network Status:\n{output}"

    if "service" in msg_lower:
        output = await run_ssh_command("systemctl list-units --type=service --state=running | head -20")
        return f"Running Services:\n{output}"

    return await _get_system_status()


async def _get_system_status() -> str:
    parts = []

    conn = test_ssh_connection()
    if conn["success"]:
        parts.append(f"Server: {conn.get('info', 'reachable')}")
    else:
        return f"Server unreachable: {conn.get('error', 'unknown')}"

    uptime = await run_ssh_command("uptime -p")
    parts.append(f"Uptime: {uptime}")

    mem = await run_ssh_command("free -h | grep Mem | awk '{print $3\"/\"$2}'")
    parts.append(f"Memory: {mem}")

    disk = await run_ssh_command("df -h / | tail -1 | awk '{print $3\"/\"$2\" (\"$5\" used)\"}'")
    parts.append(f"Disk: {disk}")

    containers = await list_containers()
    parts.append(f"\n{containers}")

    return "\n".join(parts)


def _extract_container_name(message: str, action: str) -> Optional[str]:
    patterns = [
        rf"{action}\s+(\S+)",
        rf"container\s+(\S+)",
        rf"docker\s+{action}\s+(\S+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            name = match.group(1)
            skip_words = {"container", "docker", "the", "a", "all", "on", "server", "remote"}
            if name.lower() not in skip_words:
                return name
    return None
