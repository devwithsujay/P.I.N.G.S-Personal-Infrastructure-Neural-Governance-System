import logging
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from core.config import settings
from core.proactive.checks import homelab_check, overdue_tasks_check

logger = logging.getLogger("pings.proactive.scheduler")

_scheduler: Optional[AsyncIOScheduler] = None


def _run_homelab_check() -> None:
    import asyncio
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(homelab_check())
    else:
        loop.run_until_complete(homelab_check())


def _run_overdue_check() -> None:
    import asyncio
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(overdue_tasks_check())
    else:
        loop.run_until_complete(overdue_tasks_check())


def start_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.warning("Scheduler already running")
        return

    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        _run_homelab_check,
        IntervalTrigger(minutes=settings.PROACTIVE_INTERVAL_MINUTES),
        id="homelab_check",
        name="Homelab health check",
        replace_existing=True,
    )

    _scheduler.add_job(
        _run_overdue_check,
        IntervalTrigger(minutes=15),
        id="overdue_tasks",
        name="Overdue task notifications",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        f"Scheduler started: homelab_check every {settings.PROACTIVE_INTERVAL_MINUTES}m, overdue_tasks every 15m"
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None


def get_job_status() -> Dict[str, Any]:
    if not _scheduler:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return {"running": _scheduler.running, "jobs": jobs}


def add_scheduled_job(job_id: str, func: Any, cron_expr: str, name: str = "") -> bool:
    global _scheduler
    if not _scheduler or not _scheduler.running:
        return False
    try:
        parts = cron_expr.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4]
            )
        else:
            trigger = IntervalTrigger(minutes=30)

        _scheduler.add_job(func, trigger, id=job_id, name=name or job_id, replace_existing=True)
        return True
    except Exception as e:
        logger.error(f"Failed to add scheduled job: {e}")
        return False


def remove_scheduled_job(job_id: str) -> bool:
    global _scheduler
    if not _scheduler:
        return False
    try:
        _scheduler.remove_job(job_id)
        return True
    except Exception:
        return False
