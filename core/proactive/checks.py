import logging
from core.tools.ssh import test_ssh_connection, run_ssh_command
from core.tools.system import list_containers
from core.memory.db import get_overdue_tasks
from core.proactive.notifier import notify_all, append_journal

logger = logging.getLogger("pings.proactive.checks")


async def homelab_check() -> None:
    logger.info("Running homelab health check")
    try:
        result = test_ssh_connection()
        if result["success"]:
            containers_output = await list_containers()
            down_containers = []
            for line in containers_output.split("\n"):
                if line.strip().startswith("🔴"):
                    down_containers.append(line.strip())

            if down_containers:
                msg = f"Homelab Alert: {len(down_containers)} container(s) are down:\n" + "\n".join(down_containers)
                await notify_all(msg, title="Homelab Alert", priority="high")
                await append_journal(f"[HOMELAB] Down containers detected: {len(down_containers)}")
            else:
                logger.info("Homelab check: all containers running")
                await append_journal("[HOMELAB] Health check passed - all containers running")
        else:
            msg = f"Homelab Alert: Cannot reach server - {result.get('error', 'unknown')}"
            await notify_all(msg, title="Homelab Alert", priority="urgent")
            await append_journal(f"[HOMELAB] Server unreachable: {result.get('error')}")
    except Exception as e:
        logger.error(f"Homelab check failed: {e}")
        await append_journal(f"[HOMELAB] Check failed: {e}")


async def overdue_tasks_check() -> None:
    logger.info("Running overdue tasks check")
    try:
        tasks = await get_overdue_tasks()
        if tasks:
            task_list = "\n".join(
                f"- {t['title']} (due: {t['due_date']})" for t in tasks[:5]
            )
            msg = f"You have {len(tasks)} overdue task(s):\n{task_list}"
            await notify_all(msg, title="Overdue Tasks", priority="normal")
            await append_journal(f"[TASKS] {len(tasks)} overdue tasks notified")
        else:
            logger.info("No overdue tasks")
    except Exception as e:
        logger.error(f"Overdue tasks check failed: {e}")
