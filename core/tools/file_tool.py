import os
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import settings
from core.tools.base import BaseTool

logger = logging.getLogger("pings.tools.file_tool")

WORKSPACE = Path(settings.WORKSPACE_PATH)


def _validate_path(path: str) -> Path:
    resolved = (WORKSPACE / path).resolve()
    if not str(resolved).startswith(str(WORKSPACE.resolve())):
        raise ValueError(f"Path escapes workspace: {path}")
    return resolved


async def read_file(path: str) -> str:
    try:
        full_path = _validate_path(path)
        if not full_path.exists():
            return f"File not found: {path}"
        if full_path.stat().st_size > 1_000_000:
            return "File too large (>1MB). Please be more specific."
        content = await asyncio.get_event_loop().run_in_executor(
            None, full_path.read_text, "utf-8"
        )
        return content
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error(f"read_file error: {e}")
        return f"Error reading file: {e}"


async def write_file(path: str, content: str) -> str:
    try:
        full_path = _validate_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.get_event_loop().run_in_executor(
            None, full_path.write_text, content, "utf-8"
        )
        return f"Written {len(content)} bytes to {path}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error(f"write_file error: {e}")
        return f"Error writing file: {e}"


async def list_files(path: str = ".") -> str:
    try:
        full_path = _validate_path(path)
        if not full_path.exists():
            return f"Directory not found: {path}"
        if not full_path.is_dir():
            return f"Not a directory: {path}"

        entries: List[str] = []
        for entry in sorted(full_path.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                entries.append(f"📁 {entry.name}/")
            else:
                size = entry.stat().st_size
                entries.append(f"📄 {entry.name} ({size} bytes)")

        if not entries:
            return f"Directory {path} is empty."
        return f"Contents of {path}:\n" + "\n".join(entries)
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error(f"list_files error: {e}")
        return f"Error listing files: {e}"


class FileTool(BaseTool):
    name = "files"
    description = "Read, write, and list files in the workspace"
    trigger_patterns = ["file", "read file", "write file", "list files", "show file", "workspace"]
    priority = 20

    async def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        msg_lower = message.lower()
        parts = message.split(maxsplit=2)

        if msg_lower.startswith("read file ") or msg_lower.startswith("show file "):
            path = message.split(maxsplit=1)[1] if len(parts) > 1 else ""
            return await read_file(path)

        if msg_lower.startswith("write file "):
            if len(parts) < 3:
                return "Usage: write file <path> <content>"
            path = parts[1]
            content = parts[2] if len(parts) > 2 else ""
            return await write_file(path, content)

        if msg_lower.startswith("list files") or msg_lower.startswith("show files"):
            path = parts[2] if len(parts) > 2 else "."
            return await list_files(path)

        if "workspace" in msg_lower:
            return await list_files(".")

        return await list_files(".")
