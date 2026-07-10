import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.tools.browser import web_search
from core.agents.opencode_engine import run_opencode_task
from core.agents.html_renderer import markdown_to_odysseus_html
from core.memory.db import create_research_run, update_research_run

logger = logging.getLogger("pings.agents.research")

SEARCH_PRESETS: Dict[str, Dict[str, Any]] = {
    "quick": {"max_sources": 5, "depth": 1, "queries": 2},
    "balanced": {"max_sources": 10, "depth": 3, "queries": 4},
    "deep": {"max_sources": 20, "depth": 5, "queries": 8},
}

CONTENT_MODES = ("product", "compare", "how-to", "fact-check", "auto")


def _classify_mode(topic: str, subtopics: List[str]) -> str:
    t = topic.lower()
    all_text = t + " " + " ".join(subtopics)

    compare_signals = ["vs", "versus", "compared to", "comparison", "compare", "difference between", "which is better", "alternative to"]
    if any(s in all_text for s in compare_signals):
        return "compare"

    factcheck_signals = [
        "does", "is it true", "fact check", "fact-check", "myth", "really",
        "true that", "actually", "prove", "evidence", "confirmed",
    ]
    if any(s in all_text for s in factcheck_signals):
        return "fact-check"

    howto_signals = [
        "how to", "how do i", "setup", "install", "configure", "guide",
        "tutorial", "step by step", "getting started", "set up",
        "create a", "build a", "deploy", "migrate",
    ]
    if any(s in all_text for s in howto_signals):
        return "how-to"

    product_signals = [
        "pricing", "features", "review", "worth it", "subscription",
        "plan", "tier", "free vs paid", "license", "tool", "software",
        "app", "platform", "service", "product",
    ]
    if any(s in all_text for s in product_signals):
        return "product"

    return "auto"


_UNIVERSAL_RULES = """CRITICAL RULES:
1. NEVER include raw search strings like "SearXNG results for:", "search:query", or "Mode: balanced"
2. NEVER include placeholder text like "Analysis pending" or "Data pending"
3. NEVER list sources one by one as fragments -- synthesize them into flowing prose
4. Write as a domain expert, not a search engine
5. Use ONLY plain ASCII characters -- no emojis or special unicode
6. Clean up any garbled text, mojibake, or encoding artifacts
7. Sections marked [SKIP IF ...] MUST be omitted entirely from your output if the condition applies. Do NOT fill them with "no information found" or "N/A" -- just skip them completely.
"""

_SHELL_HEADER = """OUTPUT FORMAT (follow EXACTLY):

# {topic_title}
*{mode_label} research -- {source_count} sources -- generated {date}

## Summary
2-3 sentences, the direct answer or takeaway -- no preamble

---
"""

_SHELL_FOOTER = """
---

## Sources
1. [Title](url) -- one-line note on what this source contributed
2. [additional sources]
"""

SYNTHESIS_PROMPT_PRODUCT = _UNIVERSAL_RULES + _SHELL_HEADER + """
## What it is
1-2 sentences, plain description of the product/service

## Key features
- bullet list, only the features that actually matter for a decision

## Pricing [SKIP IF no pricing information found in sources]
table or short list of pricing tiers

## Strengths
- bullets of advantages

## Weaknesses / limitations [SKIP IF none found in sources]
- bullets of drawbacks

## Alternatives worth knowing [SKIP IF no alternatives mentioned in sources]
- 1-2 lines each for relevant alternatives
""" + _SHELL_FOOTER

SYNTHESIS_PROMPT_COMPARE = _UNIVERSAL_RULES + _SHELL_HEADER + """
## At a glance
| | [Option A] | [Option B] | [Option C if present] |
|---|---|---|---|
| [dimension] | | | |
(table dimensions = whatever the sources actually compared, not forced categories -- 3-6 rows typical)

## [Option A] -- strengths & tradeoffs
- bullets

## [Option B] -- strengths & tradeoffs
- bullets

## Bottom line
1-2 sentences: when you would pick which one, if sources support a recommendation
""" + _SHELL_FOOTER

SYNTHESIS_PROMPT_HOWTO = _UNIVERSAL_RULES + _SHELL_HEADER + """
## Before you start [SKIP IF no prerequisites found in sources]
- prerequisites or requirements as bullets

## Steps
1. **Step name** -- instruction
2. **Step name** -- instruction
(numbered, sequential, sourced from what was actually found)

## Common pitfalls [SKIP IF none found in sources]
- bullets

## Time / difficulty estimate [SKIP IF not stated in sources]
1 line
""" + _SHELL_FOOTER

SYNTHESIS_PROMPT_FACTCHECK = _UNIVERSAL_RULES + _SHELL_HEADER + """
## Claim
restate exactly what is being checked, 1 sentence

## Verdict
**[Confirmed / Disputed / Partially true / Unverifiable]**
1-2 sentence explanation of the verdict

## Confidence
**[High / Medium / Low]** -- based on source agreement, source quality, or recency, explained in 1 sentence.
Apply these rules exactly:
  - High: 3+ independent sources agree, at least one is a primary or authoritative source
  - Medium: 2+ sources agree but all secondary, or topic is fast-changing
  - Low: sources conflict, single source only, or sources are low-quality / unclear provenance

## Evidence for
- bullets with source attribution inline

## Evidence against [SKIP IF none found in sources]
- bullets with source attribution inline

## Caveats [SKIP IF none]
- anything that complicates a simple yes or no answer
""" + _SHELL_FOOTER

SYNTHESIS_PROMPT_AUTO = """You are an expert research analyst producing a research report. You have been given raw search data. Pick whichever report structure below best fits the topic, and state which mode you picked in the subtitle (e.g. "auto -- how-to research").

""" + _UNIVERSAL_RULES + """
OUTPUT FORMAT -- pick ONE of these structures based on what fits the topic:

--- IF THE TOPIC IS A PRODUCT/SERVICE, USE THIS STRUCTURE: ---

# {topic_title}
*auto -- product research -- {source_count} sources -- generated {date}

## Summary
2-3 sentences, direct takeaway

---

## What it is
## Key features
## Pricing [SKIP IF no pricing info]
## Strengths
## Weaknesses / limitations [SKIP IF none]
## Alternatives worth knowing [SKIP IF none]

---

## Sources

--- IF THE TOPIC COMPARES THINGS, USE THIS STRUCTURE: ---

# {topic_title}
*auto -- compare research -- {source_count} sources -- generated {date}

## Summary
## At a glance (comparison table)
## [Option A] -- strengths & tradeoffs
## [Option B] -- strengths & tradeoffs
## Bottom line
## Sources

--- IF THE TOPIC IS A HOW-TO / INSTRUCTIONS, USE THIS STRUCTURE: ---

# {topic_title}
*auto -- how-to research -- {source_count} sources -- generated {date}

## Summary
## Before you start [SKIP IF none]
## Steps (numbered)
## Common pitfalls [SKIP IF none]
## Time / difficulty estimate [SKIP IF not stated]
## Sources

--- IF THE TOPIC ASKS FOR FACT-CHECKING, USE THIS STRUCTURE: ---

# {topic_title}
*auto -- fact-check research -- {source_count} sources -- generated {date}

## Summary
## Claim
## Verdict
## Confidence
## Evidence for
## Evidence against [SKIP IF none]
## Caveats [SKIP IF none]
## Sources

--- IF NONE OF THE ABOVE FIT (OPEN-ENDED EXPLORATORY), USE THIS FALLBACK: ---

# {topic_title}
*auto -- exploratory research -- {source_count} sources -- generated {date}

## Summary

---

## [Sub-question 1 as header]
findings, 2-4 sentences or bullets

## [Sub-question 2 as header]
findings

## [repeat per sub-question, 3-5 typical]

---

## Sources

NOW synthesize the following raw search data into a report using the structure that best fits:

"""


_PROMPTS_BY_MODE: Dict[str, str] = {
    "product": SYNTHESIS_PROMPT_PRODUCT,
    "compare": SYNTHESIS_PROMPT_COMPARE,
    "how-to": SYNTHESIS_PROMPT_HOWTO,
    "fact-check": SYNTHESIS_PROMPT_FACTCHECK,
    "auto": SYNTHESIS_PROMPT_AUTO,
}


def _build_prompt(mode: str, topic: str, source_count: int, clean_sources: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    title = topic.title() if len(topic) < 80 else topic[:77] + "..."
    mode_label = mode if mode in CONTENT_MODES else "auto"
    prompt_template = _PROMPTS_BY_MODE.get(mode_label, SYNTHESIS_PROMPT_AUTO)

    header = prompt_template.split("---\n\n", 2)[-1] if "\n---\n\n" in prompt_template else prompt_template
    if "{topic_title}" in prompt_template:
        header = prompt_template.format(
            topic_title=title,
            mode_label=mode_label,
            source_count=source_count,
            date=timestamp,
        )

    return header + "\n" + clean_sources[:15000]


_FILLER_RE = re.compile(
    r"(?:no (?:information|data|results|content|pricing|sources?|evidence|prerequisites?|caveats?|pitfalls?) (?:found|available|provided))|"
    r"(?:not (?:applicable|available|found|stated))|"
    r"(?:n/a)|"
    r"(?:none (?:found|available|provided|applicable))|"
    r"(?:none\.)|"
    r"(?:data pending)|"
    r"(?:analysis pending)",
    re.IGNORECASE,
)

_SECTION_HEADER_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)


def _strip_filler_sections(markdown: str) -> str:
    result2: List[str] = []
    i = 0
    lines_list = markdown.split("\n")

    while i < len(lines_list):
        line = lines_list[i]
        header_match = re.match(r"^(#{2,3})\s+(.+)$", line)

        if header_match:
            header_text = header_match.group(2).strip()
            if "[SKIP IF" in header_text.upper():
                block_lines = [line]
                i += 1
                while i < len(lines_list) and not re.match(r"^(#{2,3})\s+", lines_list[i]):
                    block_lines.append(lines_list[i])
                    i += 1

                body = "\n".join(block_lines[1:])
                if not body.strip() or _FILLER_RE.search(body):
                    continue

                result2.extend(block_lines)
                continue

        result2.append(line)
        i += 1

    return "\n".join(result2)


def _clean_garbled(text: str) -> str:
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'[\ufffd]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _extract_clean_sources(raw_results: List[str]) -> str:
    cleaned_parts: List[str] = []
    for result in raw_results:
        clean = _clean_garbled(result)
        if clean and len(clean) > 20:
            cleaned_parts.append(clean)
    return "\n\n---\n\n".join(cleaned_parts)


def _template_fallback(topic: str, raw_results: List[str], urls: List[str]) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    title = topic.title() if len(topic) < 80 else topic[:77] + "..."
    sections = [
        f"# {title}",
        f"*auto research -- {len(raw_results)} sources -- generated {timestamp}\n",
        "---\n",
        "## Summary",
        f"> Research conducted on '{topic}' across {len(raw_results)} search queries.\n",
        "---\n",
        "## Findings",
    ]

    if raw_results:
        seen = set()
        for result in raw_results[:5]:
            clean = _clean_garbled(result)
            if clean and clean not in seen:
                seen.add(clean)
                snippet = clean[:300]
                if snippet:
                    sections.append(f"- {snippet}")
    sections.append("")

    sections.extend([
        "---\n",
        "## Sources",
    ])
    if urls:
        seen = set()
        for url in urls[:10]:
            if url.startswith("http") and url not in seen:
                seen.add(url)
                label = url.split("//")[-1].split("/")[0][:50]
                sections.append(f"1. [{label}]({url})")

    sections.append("")
    return "\n".join(sections)


async def decompose(topic: str) -> List[str]:
    subtopics: List[str] = []
    keywords = topic.split()
    if len(keywords) > 3:
        subtopics.append(topic)
        subtopics.append(f"{topic} overview")
        subtopics.append(f"{topic} comparison")
    else:
        subtopics.append(topic)
        subtopics.append(f"{topic} explained")
        subtopics.append(f"{topic} pros and cons")
        subtopics.append(f"{topic} latest news")
        subtopics.append(f"{topic} alternatives")
    return subtopics[:6]


async def run_research(
    topic: str,
    mode: str = "auto",
    max_sources: int = 10,
    run_id: Optional[int] = None,
) -> Dict[str, Any]:
    if run_id is None:
        run_id = await create_research_run(topic, mode)
    await update_research_run(run_id, status="running")

    try:
        subtopics = await decompose(topic)

        detected_mode = _classify_mode(topic, subtopics)
        effective_mode = mode if mode in CONTENT_MODES and mode != "auto" else detected_mode
        logger.info(f"Research mode: {effective_mode} (requested={mode}, detected={detected_mode})")

        raw_results: List[str] = []
        collected_urls: List[str] = []

        for subtopic in subtopics:
            try:
                result = await web_search(subtopic)
                if result and len(result.strip()) > 50:
                    raw_results.append(result)
                    urls_found = re.findall(r'https?://[^\s\)]+', result)
                    collected_urls.extend(urls_found)
                logger.info(f"Search OK for '{subtopic}': {len(result)} chars")
            except Exception as e:
                logger.warning(f"Search failed for '{subtopic}': {e}")

        clean_sources = _extract_clean_sources(raw_results)

        if not clean_sources:
            fallback = f"No search results found for '{topic}'. Try a different query."
            await update_research_run(run_id, status="completed", sources_count=0)
            return {
                "report": fallback,
                "report_html": markdown_to_odysseus_html(fallback, topic),
                "run_id": run_id,
            }

        llm_prompt = _build_prompt(effective_mode, topic, len(raw_results), clean_sources)

        logger.info(f"Sending {len(clean_sources)} chars to LLM for {effective_mode} synthesis")
        synthesized_report = await run_opencode_task(
            task=llm_prompt,
            system_context=(
                "You are a world-class research analyst. Produce polished, "
                "Odysseus-quality reports. Never use placeholder text. "
                "Omit sections marked [SKIP IF ...] entirely instead of filling them with filler."
            ),
            timeout=180,
        )

        if synthesized_report.startswith("Agent error"):
            logger.warning("LLM synthesis failed, using template fallback")
            synthesized_report = _template_fallback(topic, raw_results, collected_urls)

        synthesized_report = _strip_filler_sections(synthesized_report)

        url_pattern = re.compile(r'https?://[^\s\)\]>"]+')
        found_in_report = set(url_pattern.findall(synthesized_report))

        missing_urls = [u for u in collected_urls if u not in found_in_report and u.startswith("http")]
        if missing_urls:
            sources_header = re.search(
                r"^## Sources\s*$", synthesized_report, re.MULTILINE
            )
            if sources_header:
                source_section = "\n"
                seen = set()
                for url in missing_urls[:10]:
                    if url not in seen:
                        seen.add(url)
                        label = url.split("//")[-1].split("/")[0][:50]
                        source_section += f"* [{label}]({url})\n"
                synthesized_report = synthesized_report.replace(
                    "## Sources", "## Sources" + source_section, 1
                )

        report_html = markdown_to_odysseus_html(synthesized_report, topic)

        await update_research_run(
            run_id,
            status="completed",
            sources_count=len(raw_results),
            report=synthesized_report,
            report_html=report_html,
            completed_at=datetime.utcnow().isoformat(),
        )

        return {
            "report": synthesized_report,
            "report_html": report_html,
            "run_id": run_id,
        }

    except Exception as e:
        await update_research_run(run_id, status="failed", error=str(e))
        logger.error(f"Research failed: {e}")
        error_msg = f"Research failed: {e}"
        return {
            "report": error_msg,
            "report_html": markdown_to_odysseus_html(error_msg, topic),
            "run_id": run_id,
        }
