import os
import time
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml

logger = logging.getLogger("pings.persona.loader")


def load_persona(path: str = "/app/persona") -> Dict[str, Any]:
    persona_dir = Path(path)
    result: Dict[str, Any] = {
        "identity": "",
        "context": "",
        "rules": "",
        "config": {},
    }

    config_file = persona_dir / "persona.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                result["config"] = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load persona.yaml: {e}")

    identity_file = persona_dir / "IDENTITY.md"
    if identity_file.exists():
        try:
            result["identity"] = identity_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load IDENTITY.md: {e}")

    context_file = persona_dir / "CONTEXT.md"
    if context_file.exists():
        try:
            result["context"] = context_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load CONTEXT.md: {e}")

    rules_file = persona_dir / "RULES.md"
    if rules_file.exists():
        try:
            result["rules"] = rules_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load RULES.md: {e}")

    journal_path = Path(os.environ.get("JOURNAL_PATH", "/app/persona/JOURNAL.md"))
    if journal_path.exists():
        try:
            result["journal"] = journal_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load journal: {e}")
    else:
        result["journal"] = ""

    return result


def build_system_prompt(persona: Dict[str, Any]) -> str:
    parts = []

    if persona.get("identity"):
        parts.append(persona["identity"])

    if persona.get("context"):
        parts.append("\n## Context\n" + persona["context"])

    if persona.get("rules"):
        parts.append("\n## Rules\n" + persona["rules"])

    config = persona.get("config", {})
    if config:
        name = config.get("name", "PINGS")
        parts.append(f"\nYou are {name}, a personal AI assistant.")
        if config.get("capabilities"):
            caps = config["capabilities"]
            if isinstance(caps, list):
                parts.append("Capabilities: " + ", ".join(caps))

    return "\n".join(parts) if parts else "You are PINGS, a helpful AI assistant."


def watch_persona_files(callback: Callable[[], None], interval: float = 5.0, path: str = "/app/persona") -> None:
    import threading

    persona_dir = Path(path)
    mtimes: Dict[str, float] = {}

    def _check() -> None:
        changed = False
        for file in persona_dir.glob("*"):
            if file.is_file():
                try:
                    mtime = file.stat().st_mtime
                    key = str(file)
                    if key not in mtimes or mtimes[key] != mtime:
                        mtimes[key] = mtime
                        changed = True
                except OSError:
                    pass
        if changed:
            try:
                callback()
            except Exception as e:
                logger.error(f"Persona watch callback error: {e}")

    def _loop() -> None:
        while True:
            time.sleep(interval)
            _check()

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    logger.info(f"Persona file watcher started (interval={interval}s, path={path})")
