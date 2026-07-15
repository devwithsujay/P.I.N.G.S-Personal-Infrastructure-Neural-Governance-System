import logging
import re
from typing import Optional

from core.tools.ssh import run_ssh_command

logger = logging.getLogger("pings.tools.host")


async def exec_command(command: str) -> str:
    result = await run_ssh_command(command)
    if result.startswith("[SSH Error]") or result.startswith("[exit"):
        return f"Command failed: {result}"
    return result


async def get_ip() -> str:
    return await exec_command("hostname -I | awk '{print $1}'")


async def create_folder(path: str) -> str:
    safe_path = path.replace("'", "'\\''")
    return await exec_command(f"mkdir -p '{safe_path}' && echo 'Created {path}'")


async def delete_path(path: str) -> str:
    safe_path = path.replace("'", "'\\''")
    return await exec_command(f"rm -rf '{safe_path}' && echo 'Deleted {path}'")


async def list_directory(path: str = "~") -> str:
    safe_path = path.replace("'", "'\\''")
    return await exec_command(f"ls -la '{safe_path}'")


def parse_host_action(message: str) -> Optional[str]:
    msg = message.lower().strip()

    if re.search(r"\b(what'?s?\s+)?my\s+(ip|ip\s+address|ip\s+addr)", msg):
        return "get_ip"

    m = re.search(r"(create|make)\s+(?:a\s+)?(?:folder|directory|dir)\s+(?:at|in|under|called|named)?\s*(.+)", msg)
    if m:
        return f"create_folder:{m.group(2).strip().rstrip('.')}"

    m = re.search(r"(delete|remove|rm)\s+(?:the\s+)?(?:folder|directory|dir|file|path)\s+(.+)", msg)
    if m:
        return f"delete_path:{m.group(2).strip().rstrip('.')}"

    m = re.search(r"(list|show|ls)\s+(?:the\s+)?(?:contents?\s+of\s+)?(?:folder|directory|dir|path)?\s*(.+)", msg)
    if m:
        return f"list_directory:{m.group(2).strip().rstrip('.')}"

    if re.search(r"\b(run|execute)\s+(?:the\s+)?command\s+(.+)", msg):
        m = re.search(r"\b(?:run|execute)\s+(?:the\s+)?command\s+(.+)", msg)
        if m:
            return f"exec:{m.group(1).strip().rstrip('.')}"

    return None
