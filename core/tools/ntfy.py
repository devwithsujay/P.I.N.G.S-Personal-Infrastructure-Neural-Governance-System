import httpx
import logging
from core.config import settings

logger = logging.getLogger("pings.ntfy")


async def send_ntfy(title: str, message: str, priority: str = "default", tags: str = "") -> bool:
    if not settings.NTFY_URL or not settings.NTFY_TOPIC:
        return False

    headers = {"Title": title, "Priority": priority}
    if tags:
        headers["Tags"] = tags

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.NTFY_URL}/{settings.NTFY_TOPIC}",
                headers=headers,
                content=message,
            )
            return resp.status_code == 200
    except Exception as e:
        logger.warning(f"ntfy send failed: {e}")
        return False
