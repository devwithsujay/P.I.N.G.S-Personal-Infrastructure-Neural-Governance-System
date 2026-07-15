import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone as tz

from core.config import settings

logger = logging.getLogger("pings.scheduler")

_scheduler: Optional[AsyncIOScheduler] = None


def _job_id(automation_id: int) -> str:
    return f"briefing_{automation_id}"


async def start_scheduler() -> None:
    global _scheduler
    from core.memory.db import get_automations

    jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{settings.SQLITE_DB_PATH}")}
    _scheduler = AsyncIOScheduler(jobstores=jobstores)
    _scheduler.start()

    automations = await get_automations(active_only=True)
    for a in automations:
        _register_job(a)
    logger.info(f"Scheduler started, loaded {len(automations)} automations")


def _register_job(automation: dict) -> None:
    global _scheduler
    if not _scheduler:
        return

    job_id = _job_id(automation["id"])
    hour, minute = _parse_time(automation["schedule_time"])
    user_tz = tz(automation.get("timezone", "UTC"))

    trigger = CronTrigger(hour=hour, minute=minute, timezone=user_tz)

    try:
        _scheduler.add_job(
            _run_briefing,
            trigger,
            args=[automation["id"]],
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Registered job {job_id} at {automation['schedule_time']} {automation.get('timezone', 'UTC')}")
    except Exception as e:
        logger.error(f"Failed to register job {job_id}: {e}")


def _parse_time(time_str: str) -> tuple[int, int]:
    parts = time_str.strip().split(":")
    return int(parts[0]), int(parts[1])


async def _run_briefing(automation_id: int) -> None:
    from core.agents.briefing import generate_briefing
    try:
        await generate_briefing(automation_id)
    except Exception as e:
        logger.error(f"Briefing job {automation_id} failed: {e}")


def add_job(automation: dict) -> None:
    _register_job(automation)


def remove_job(automation_id: int) -> None:
    global _scheduler
    if not _scheduler:
        return
    job_id = _job_id(automation_id)
    try:
        _scheduler.remove_job(job_id)
        logger.info(f"Removed job {job_id}")
    except Exception:
        pass


def reschedule_job(automation: dict) -> None:
    remove_job(automation["id"])
    if automation.get("active"):
        _register_job(automation)


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
