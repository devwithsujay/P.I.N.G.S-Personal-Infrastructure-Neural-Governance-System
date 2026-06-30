import re
import logging
from typing import List, Tuple

from core.config import settings

logger = logging.getLogger("pings.tools.security")

CONFIRM_BEFORE: List[str] = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r"docker\s+stop\s+",
    r"docker\s+rm\s+",
    r"docker\s+kill\s+",
    r"systemctl\s+stop\s+",
    r"systemctl\s+disable\s+",
    r"shutdown\s+",
    r"reboot",
    r"halt",
    r"init\s+[06]",
    r"mkfs\.",
    r"dd\s+if=",
    r">\s*/dev/sd",
    r"chmod\s+-R\s+777\s+/",
    r"chown\s+-R.*\s+/",
    r"apt\s+(remove|purge)\s+",
    r"yum\s+(remove|erase)\s+",
    r"kill\s+-9\s+1",
    r"killall",
    r"pkill",
    r"service\s+\w+\s+stop",
]


def get_dangerous_patterns() -> List[str]:
    return settings.DANGER_PATTERNS


def is_action_safe(message: str) -> Tuple[bool, str]:
    msg_lower = message.lower().strip()

    for pattern in settings.DANGER_PATTERNS:
        if pattern.lower() in msg_lower:
            reason = f"Blocked: matches danger pattern '{pattern}'"
            logger.warning(f"Unsafe action detected: {reason} | message={message[:100]}")
            return False, reason

    for pattern in CONFIRM_BEFORE:
        if re.search(pattern, msg_lower):
            reason = f"Requires confirmation: matches pattern '{pattern}'"
            logger.info(f"Confirmation required: {reason} | message={message[:100]}")
            return False, reason

    return True, "safe"


def get_confirm_patterns() -> List[str]:
    return CONFIRM_BEFORE
