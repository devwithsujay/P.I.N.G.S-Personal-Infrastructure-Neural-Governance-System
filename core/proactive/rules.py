import re
import logging
from typing import List, Tuple

logger = logging.getLogger("pings.proactive.rules")


def load_rules(rules_md: str) -> List[str]:
    rules: List[str] = []
    for line in rules_md.split("\n"):
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            rule = line[2:].strip()
            if rule:
                rules.append(rule)
        elif line.startswith("#"):
            continue
        elif line:
            rules.append(line)
    return rules


def is_action_safe(message: str) -> Tuple[bool, str]:
    from core.tools.security import is_action_safe as _check
    return _check(message)


def matches_rule(message: str, rules: List[str]) -> List[str]:
    matched: List[str] = []
    msg_lower = message.lower()
    for rule in rules:
        keywords = rule.lower().split()
        if all(kw in msg_lower for kw in keywords):
            matched.append(rule)
    return matched
