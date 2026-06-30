import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from core.config import settings

logger = logging.getLogger("pings.proactive.notifier")


async def send_telegram(message: str, title: str = "PINGS Notification") -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    user_id = settings.TELEGRAM_ALLOWED_USER_ID
    if not token or not user_id:
        logger.debug("Telegram not configured, skipping")
        return False

    text = f"*{title}*\n\n{message}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": user_id, "text": text, "parse_mode": "Markdown"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"Telegram notification sent: {title}")
            return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def send_ntfy(message: str, title: str = "PINGS", priority: str = "default") -> bool:
    ntfy_url = settings.NTFY_URL
    topic = settings.NTFY_TOPIC
    if not ntfy_url:
        logger.debug("ntfy not configured, skipping")
        return False

    url = f"{ntfy_url}/{topic}"
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": "pings,notification",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, content=message.encode("utf-8"), headers=headers)
            resp.raise_for_status()
            logger.info(f"ntfy notification sent: {title}")
            return True
    except Exception as e:
        logger.error(f"ntfy send failed: {e}")
        return False


async def notify_all(message: str, title: str = "PINGS Notification", priority: str = "default") -> None:
    await send_telegram(message, title)
    await send_ntfy(message, title, priority)


async def append_journal(entry: str) -> bool:
    journal_path = Path(settings.JOURNAL_PATH)
    try:
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"\n[{timestamp}] {entry}\n"

        import asyncio
        def _write():
            with open(journal_path, "a", encoding="utf-8") as f:
                f.write(line)

        await asyncio.get_event_loop().run_in_executor(None, _write)
        return True
    except Exception as e:
        logger.error(f"Journal append failed: {e}")
        return False
