import re
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from core.memory.db import create_task, get_tasks, get_task, update_task

logger = logging.getLogger("pings.agents.tasks")

DUE_DATE_PATTERNS = [
    (r"due\s+(tomorrow)", 1),
    (r"due\s+(today)", 0),
    (r"due\s+(next\s+week)", 7),
    (r"due\s+(\d{1,2}(?:st|nd|rd|th)?)", 0),
    (r"by\s+(tomorrow)", 1),
    (r"by\s+(today)", 0),
    (r"by\s+(next\s+week)", 7),
    (r"(?:on|by)\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)", 0),
]

PRIORITY_KEYWORDS = {
    "urgent": ["urgent", "asap", "critical", "emergency"],
    "high": ["high", "important", "priority"],
    "medium": ["medium", "normal"],
    "low": ["low", "minor", "whenever"],
}


def _extract_task_details(message: str) -> Dict[str, Any]:
    msg_lower = message.lower()
    result = {"title": "", "description": "", "priority": "medium", "due_date": None}

    title = message
    for prefix in ["add task", "create task", "new task", "task:", "todo:"]:
        if msg_lower.startswith(prefix):
            title = message[len(prefix):].strip()
            break

    title = re.sub(r"\s+due\s+.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+priority\s+\w+", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+by\s+\w+\s+\d{1,2}.*$", "", title, flags=re.IGNORECASE)
    title = title.strip(" .,;:!?")
    if not title:
        title = message[:100]

    result["title"] = title

    today = datetime.utcnow().date()
    for pattern, days_offset in DUE_DATE_PATTERNS:
        match = re.search(pattern, msg_lower)
        if match:
            if days_offset > 0:
                result["due_date"] = (today + timedelta(days=days_offset)).isoformat()
            else:
                captured = match.group(1)
                if "tomorrow" in captured:
                    result["due_date"] = (today + timedelta(days=1)).isoformat()
                elif "today" in captured:
                    result["due_date"] = today.isoformat()
                elif "next week" in captured:
                    result["due_date"] = (today + timedelta(days=7)).isoformat()
                else:
                    day_match = re.search(r"(\d{1,2})", captured)
                    if day_match:
                        day = int(day_match.group(1))
                        month_match = re.search(r"(\w+)\s+\d", captured)
                        if month_match:
                            month_name = month_match.group(1)
                            try:
                                month = datetime.strptime(month_name, "%B").month
                            except ValueError:
                                try:
                                    month = datetime.strptime(month_name, "%b").month
                                except ValueError:
                                    month = today.month
                            year = today.year if month >= today.month else today.year + 1
                            try:
                                due = datetime(year, month, day).date()
                                result["due_date"] = due.isoformat()
                            except ValueError:
                                pass
            break

    for priority, keywords in PRIORITY_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                result["priority"] = priority
                break
        if result["priority"] != "medium":
            break

    return result


async def handle_tasks(message: str, system_prompt: str = "") -> str:
    msg_lower = message.lower()
    logger.info(f"Tasks agent processing: {message[:100]}")

    if "list" in msg_lower or "show" in msg_lower or "what" in msg_lower or "pending" in msg_lower or "my tasks" in msg_lower:
        tasks = await get_tasks()
        if not tasks:
            return "No tasks found. Use 'add task <title>' to create one."
        lines = ["Your tasks:\n"]
        for t in tasks:
            status_icon = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}.get(t["status"], "[ ]")
            due = f" (due: {t['due_date']})" if t.get("due_date") else ""
            lines.append(f"{status_icon} #{t['id']} {t['title']}{due} [{t['priority']}]")
        return "\n".join(lines)

    if msg_lower.startswith("done ") or msg_lower.startswith("complete ") or msg_lower.startswith("finish "):
        id_match = re.search(r"#?(\d+)", message)
        if id_match:
            task_id = int(id_match.group(1))
            task = await get_task(task_id)
            if task:
                await update_task(task_id, status="done")
                return f"Task #{task_id} marked as done."
            return f"Task #{task_id} not found."
        return "Please specify a task number. Example: done #1"

    if "delete" in msg_lower or "remove" in msg_lower:
        id_match = re.search(r"#?(\d+)", message)
        if id_match:
            from core.memory.db import delete_task
            task_id = int(id_match.group(1))
            success = await delete_task(task_id)
            if success:
                return f"Task #{task_id} deleted."
            return f"Task #{task_id} not found."
        return "Please specify a task number. Example: delete #1"

    details = _extract_task_details(message)
    task_id = await create_task(
        title=details["title"],
        description=details["description"],
        priority=details["priority"],
        due_date=details["due_date"],
    )
    task = await get_task(task_id)

    due_str = f" due {task['due_date']}" if task and task.get("due_date") else ""
    priority_str = f" [{details['priority']}]" if details["priority"] != "medium" else ""
    return f"Task #{task_id} created: {details['title']}{due_str}{priority_str}"
