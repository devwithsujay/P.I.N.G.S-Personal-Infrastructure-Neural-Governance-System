import logging
from datetime import datetime
from typing import Any, Dict

from core.memory.db import get_automation
from core.agents.daily_brief import run_daily_brief

logger = logging.getLogger("pings.agents.briefing")


async def generate_briefing(automation_id: int) -> Dict[str, Any]:
    """Delegate to the daily_brief pipeline."""
    return await run_daily_brief(automation_id)
