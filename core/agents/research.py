import re
import json
import time
import asyncio
import logging
from difflib import SequenceMatcher
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import settings
from core.tools.browser import (
    search_searxng_and_ddg, fetch_all, is_usable, _content_hash,
)
from core.schemas import SectionSpec, Source, SectionResult, Report
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

SECTION_WRITE_CONCURRENCY = 3
MAX_CALL_RETRY_ATTEMPTS = 4
BASE_BACKOFF_SECONDS = 2

FAILURE_MARKERS = [
    "no response from agent",
    "request failed",
    "error:",
    "timeout",
    "rate limit",
]


class SectionGenerationError(Exception):
    pass


def is_failed_response(text: str) -> bool:
    if not text or not text.strip():
        return True
    normalized = text.strip().lower()
    return any(normalized == marker or normalized.startswith(marker) for marker in FAILURE_MARKERS)


_SECTION_PROMPT_TEMPLATE = """You are writing ONE SECTION of a research report on: {topic}

SECTION: {section_title}
DEPTH TIER: {depth_tier}
DEPTH INSTRUCTION: {depth_instruction}

YOUR SOURCES ({source_count} sources, {source_word_count} total words):
{sources_text}

INSTRUCTIONS:
- Write ONLY this section, do not include headers for other sections
- Use information from the sources above — cite naturally, no footnotes needed
- {coverage_note}
- Write at least {min_words} words of substantive content
- Do NOT include a "Sources" or "References" section — that is assembled separately
- Use plain ASCII, no emojis

{depth_instruction}

Write the section now:"""

_DEPTH_INSTRUCTIONS = {
    "broad": "Provide context, background, and landscape framing. Define key terms. Assume the reader is unfamiliar with this subtopic. Cover definitions, history, and current state.",
    "deep": "Go technical. Cover mechanics, comparisons, data points, named cases or examples from the sources. Assume the reader has read the broad sections already. Include specific numbers, dates, and names where sources provide them.",
    "synthesis": "Connect this back to earlier sections. Discuss implications, tensions between sources, and open questions. Do not re-introduce basics. Draw connections and highlight what matters.",
}

SCAFFOLD_PATTERNS = [
    r"^(Now I have.*?\.)\s*",
    r"^(Let me write.*?\.)\s*",
    r"^(Here is|Here's) (the|my|an?) (expanded )?section.*?:\s*",
    r"^(I('ll| will) (now )?(write|draft|expand).*?\.)\s*",
    r"^(Based on (the|my) (research|sources).*?\.)\s*",
]


def strip_scaffolding(text: str) -> str:
    cleaned = text.strip()
    for pattern in SCAFFOLD_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip()


def _fuzz_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def strip_model_title(text: str, expected_title: str) -> str:
    lines = text.strip().split("\n", 1)
    if not lines:
        return text
    first_line = lines[0].strip().lstrip("#").strip()
    if first_line and (
        first_line.lower() == expected_title.lower()
        or _fuzz_ratio(first_line.lower(), expected_title.lower()) > 0.85
    ):
        return lines[1].strip() if len(lines) > 1 else ""
    return text


def ensure_paragraph_breaks(text: str) -> str:
    lines = text.split("\n")
    result = []
    for i, line in enumerate(lines):
        result.append(line)
        if i < len(lines) - 1:
            current_ends_sentence = line.strip().endswith((".", "!", "?", ":"))
            next_is_content = lines[i + 1].strip() != ""
            if current_ends_sentence and next_is_content and lines[i + 1].strip() and line.strip():
                result.append("")
    return "\n".join(result)


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


async def decompose(topic: str) -> List[SectionSpec]:
    prompt = f"""Decompose this research topic into 5-9 sections for a comprehensive report.

TOPIC: {topic}

Return a JSON array of objects, each with:
- "title": section heading (concise, specific)
- "subtopic_query": a search query that would find sources for this section (10-20 words)
- "depth_tier": one of "broad", "deep", "synthesis"
- "order": integer starting at 1

DEPTH TIER RULES:
- First ~20% of sections: "broad" (context, background, definitions, landscape)
- Middle ~60% of sections: "deep" (technical mechanics, comparisons, data, cases)
- Last ~20% of sections: "synthesis" (implications, connections, open questions, outlook)

Return ONLY the JSON array, no explanation:"""

    response = await run_opencode_task(
        task=prompt,
        system_context="You are a research planning assistant. Return only valid JSON.",
        timeout=60,
    )

    try:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            sections_data = json.loads(json_match.group())
            sections = []
            for i, s in enumerate(sections_data):
                tier = s.get("depth_tier", "deep")
                if tier not in ("broad", "deep", "synthesis"):
                    tier = "deep"
                sections.append(SectionSpec(
                    title=s.get("title", f"Section {i+1}"),
                    subtopic_query=s.get("subtopic_query", topic),
                    depth_tier=tier,
                    order=s.get("order", i + 1),
                ))
            if sections:
                return sections
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse decompose response: {e}")

    return [
        SectionSpec(title="Overview", subtopic_query=f"{topic} overview background", depth_tier="broad", order=1),
        SectionSpec(title="Key Concepts", subtopic_query=f"{topic} definitions key terms", depth_tier="broad", order=2),
        SectionSpec(title="How It Works", subtopic_query=f"{topic} how it works mechanics", depth_tier="deep", order=3),
        SectionSpec(title="Comparisons", subtopic_query=f"{topic} comparison alternatives", depth_tier="deep", order=4),
        SectionSpec(title="Use Cases", subtopic_query=f"{topic} use cases examples", depth_tier="deep", order=5),
        SectionSpec(title="Current State", subtopic_query=f"{topic} current state 2024 2025", depth_tier="deep", order=6),
        SectionSpec(title="Implications", subtopic_query=f"{topic} implications future outlook", depth_tier="synthesis", order=7),
    ]


async def gather_sources(section: SectionSpec) -> List[Source]:
    query = section.subtopic_query
    kept: List[Source] = []
    seen_urls: set = set()
    seen_hashes: set = set()
    attempt = 0
    queries_tried = [query]

    while len(kept) < settings.MIN_SOURCES_PER_SUBTOPIC and attempt < settings.MAX_SEARCH_REFORMULATIONS:
        raw_results = await search_searxng_and_ddg(query)
        candidates = [r for r in raw_results if r.url not in seen_urls]

        fetched = await fetch_all(candidates)
        usable = [f for f in fetched if is_usable(f)]

        for f in usable:
            content_h = _content_hash(f.full_text or "")
            if content_h not in seen_hashes:
                seen_hashes.add(content_h)
                seen_urls.add(f.url)
                kept.append(f)

        attempt += 1
        if len(kept) < settings.MIN_SOURCES_PER_SUBTOPIC and attempt < settings.MAX_SEARCH_REFORMULATIONS:
            query = await _reformulate_query(section.subtopic_query, queries_tried)
            queries_tried.append(query)

    logger.info(f"Gathered {len(kept)} sources for '{section.title}' after {attempt} attempts")
    return kept


async def _reformulate_query(original: str, tried: List[str]) -> str:
    tried_list = "\n".join(f"- {q}" for q in tried[-3:])
    prompt = f"""The search query "{original}" did not return enough sources.
Previously tried queries:
{tried_list}

Suggest ONE new search query that would find different sources on the same subtopic.
Be specific, use different keywords, try alternative phrasings.
Return ONLY the query text, nothing else:"""

    response = await run_opencode_task(
        task=prompt,
        system_context="You are a search query reformulation assistant. Return only the query.",
        timeout=30,
    )
    reformulated = response.strip().strip('"').strip("'")
    if reformulated and len(reformulated) > 5:
        return reformulated
    return f"{original} detailed analysis"


async def write_section(section: SectionSpec, sources: List[Source], force_expand: bool = False) -> SectionResult:
    depth_instruction = _DEPTH_INSTRUCTIONS[section.depth_tier]

    source_count = len(sources)
    source_word_count = sum(s.word_count for s in sources)
    sources_text = "\n\n---\n\n".join(
        f"[Source {i+1}: {s.title}] ({s.url})\n{s.full_text[:2000]}"
        for i, s in enumerate(sources[:20])
    )

    if source_count < settings.MIN_SOURCES_PER_SUBTOPIC:
        coverage_note = (
            f"Only {source_count} sources were found on this subtopic after exhausted search reformulation. "
            "Work with what is available — do not pad with unsupported statements."
        )
    else:
        coverage_note = (
            "If the fetched sources do not adequately cover some part of this subtopic, "
            "state plainly: 'Limited sources available on this aspect' — do not pad with "
            "generic or unsupported statements to fill space."
        )

    prompt = _SECTION_PROMPT_TEMPLATE.format(
        topic=section.subtopic_query,
        section_title=section.title,
        depth_tier=section.depth_tier,
        depth_instruction=depth_instruction,
        source_count=source_count,
        source_word_count=source_word_count,
        sources_text=sources_text[:15000],
        min_words=settings.MIN_WORDS_PER_SECTION,
        coverage_note=coverage_note,
    )

    if force_expand:
        prompt += (
            f"\n\nEXPAND THIS SECTION: The current draft is too short. "
            f"Expand with more source-grounded detail — do not repeat sentences to inflate length. "
            f"Target at least {settings.MIN_WORDS_PER_SECTION} words."
        )

    draft = ""
    word_count = 0

    for rewrite_attempt in range(1, settings.MAX_SECTION_REWRITE_ATTEMPTS + 1):
        draft = None
        t0 = time.time()

        for call_attempt in range(1, MAX_CALL_RETRY_ATTEMPTS + 1):
            try:
                draft = await run_opencode_task(
                    task=prompt,
                    system_context=(
                        "You are a research writer producing one section of a report. "
                        "Write substantive, source-grounded content. Never use placeholder text. "
                        "Output only the section content. Do not narrate what you are about to do "
                        "or acknowledge the instructions. Never start with phrases like "
                        "'Now I have', 'Let me write', 'Here is the section', or similar scaffolding."
                    ),
                    timeout=120,
                )
            except (TimeoutError, ConnectionError, OSError) as e:
                logger.warning(f"Call error for '{section.title}' call_attempt={call_attempt}: {e}")
                draft = None

            if draft is not None and not is_failed_response(draft):
                break

            backoff = BASE_BACKOFF_SECONDS * (2 ** (call_attempt - 1))
            logger.warning(f"Failed call for '{section.title}' call_attempt={call_attempt}, retrying in {backoff}s")
            await asyncio.sleep(backoff)

        latency = time.time() - t0

        if draft is None or is_failed_response(draft):
            logger.error(
                f"Section '{section.title}' FAILED after {MAX_CALL_RETRY_ATTEMPTS} call attempts "
                f"({latency:.1f}s total). response={draft!r}"
            )
            return SectionResult(
                section=section,
                text="",
                word_count=0,
                attempts=rewrite_attempt,
                under_minimum=True,
                call_failed=True,
                sources=sources,
                sources_found=source_count,
            )

        draft = strip_scaffolding(draft)
        draft = strip_model_title(draft, section.title)
        draft = ensure_paragraph_breaks(draft)
        word_count = len(draft.split())
        logger.info(
            f"Section '{section.title}' rewrite={rewrite_attempt} call_ok "
            f"({latency:.1f}s): {word_count} words after cleanup"
        )

        if word_count >= settings.MIN_WORDS_PER_SECTION:
            return SectionResult(
                section=section,
                text=draft,
                word_count=word_count,
                attempts=rewrite_attempt,
                under_minimum=False,
                call_failed=False,
                sources=sources,
                sources_found=source_count,
            )

        prompt += (
            f"\n\nPrevious draft was {word_count} words, below the {settings.MIN_WORDS_PER_SECTION} minimum. "
            f"Expand with more source-grounded detail — do not repeat sentences to inflate length."
        )

    return SectionResult(
        section=section,
        text=draft or "",
        word_count=word_count,
        attempts=settings.MAX_SECTION_REWRITE_ATTEMPTS,
        under_minimum=True,
        call_failed=False,
        sources=sources,
        sources_found=source_count,
    )


async def write_all_sections(section_results: List[SectionResult]) -> List[SectionResult]:
    sem = asyncio.Semaphore(SECTION_WRITE_CONCURRENCY)
    written: List[SectionResult] = []

    async def _write_one(sr: SectionResult) -> SectionResult:
        async with sem:
            if not sr.sources:
                return SectionResult(
                    section=sr.section,
                    text="",
                    word_count=0,
                    attempts=0,
                    under_minimum=True,
                    call_failed=False,
                    sources=[],
                    sources_found=0,
                )
            return await write_section(sr.section, sr.sources)

    tasks = [_write_one(sr) for sr in section_results]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"Section '{section_results[i].section.title}' raised: {r}")
            written.append(SectionResult(
                section=section_results[i].section,
                text="",
                word_count=0,
                attempts=0,
                under_minimum=True,
                call_failed=True,
                sources=[],
                sources_found=0,
            ))
        else:
            written.append(r)

    return written


async def check_cross_section_consistency(sections: List[SectionResult]) -> List[str]:
    valid_sections = [s for s in sections if s.text and not s.call_failed]
    if len(valid_sections) < 2:
        return []

    full_text = "\n\n".join(f"[{s.section.title}]\n{s.text}" for s in valid_sections)

    prompt = (
        "Below is a multi-section research report. Identify any specific factual claims "
        "(numbers, dates, names, statistics) that contradict each other across sections. "
        "List only clear contradictions, not stylistic differences or rounding variations. "
        "Format each as: 'Section A says X; Section B says Y.' "
        "If none, respond with exactly: 'No contradictions found.'\n\n" + full_text[:12000]
    )
    result = await run_opencode_task(
        task=prompt,
        system_context="You are a fact-checking assistant. Return only contradiction findings.",
        timeout=60,
    )
    if "no contradictions found" in result.lower():
        return []
    contradictions = [
        line.strip().lstrip("- ").lstrip("* ")
        for line in result.strip().split("\n")
        if line.strip() and "says" in line.lower()
    ]
    return contradictions[:10]


async def assemble_report(topic: str, sections: List[SectionResult]) -> Report:
    hard_failures = [s for s in sections if getattr(s, "call_failed", False)]

    if hard_failures:
        logger.info(f"Assembly: {len(hard_failures)} sections failed, retrying in isolation")
        for i, s in enumerate(hard_failures):
            if s.sources:
                retried = await write_section(s.section, s.sources)
                if not retried.call_failed:
                    idx = sections.index(s)
                    sections[idx] = retried
                    hard_failures.remove(s)

    still_failed = [s for s in sections if getattr(s, "call_failed", False)]
    if still_failed:
        failed_titles = [s.section.title for s in still_failed]
        raise SectionGenerationError(
            f"{len(still_failed)} section(s) failed to generate after retries: {failed_titles}"
        )

    total_words = sum(s.word_count for s in sections)
    under_min_sections = [s.section.title for s in sections if s.under_minimum]

    logger.info(f"Assembly: total_words={total_words}, target={settings.MIN_WORDS_TOTAL}, under_min={under_min_sections}")

    if total_words < settings.MIN_WORDS_TOTAL:
        deficit = settings.MIN_WORDS_TOTAL - total_words
        logger.info(f"Assembly: deficit={deficit}, expanding sections to meet floor")
        candidates = sorted(
            [s for s in sections if not s.under_minimum],
            key=lambda s: s.word_count,
        )
        for s in candidates:
            if total_words >= settings.MIN_WORDS_TOTAL:
                break
            logger.info(f"Assembly: expanding '{s.section.title}' (current={s.word_count} words)")
            expanded = await write_section(s.section, s.sources, force_expand=True)
            delta = expanded.word_count - s.word_count
            total_words += delta
            logger.info(f"Assembly: '{s.section.title}' expanded by {delta} words to {expanded.word_count}")
            idx = sections.index(s)
            sections[idx] = expanded

        logger.info(f"Assembly: after top-up, total_words={total_words}")

    contradictions = await check_cross_section_consistency(sections)
    if contradictions:
        logger.info(f"Assembly: found {len(contradictions)} cross-section contradictions")

    flagged = under_min_sections.copy()
    if total_words < settings.MIN_WORDS_TOTAL:
        flagged.append(f"TOTAL: {total_words} words (below {settings.MIN_WORDS_TOTAL} target)")

    return Report(
        topic=topic,
        sections=sections,
        total_words=total_words,
        flagged_sections=flagged,
        metadata={
            "sections_count": len(sections),
            "sources_per_section": {s.section.title: s.sources_found for s in sections},
            "word_counts": {s.section.title: s.word_count for s in sections},
            "flagged_contradictions": contradictions,
        },
    )


def _render_report_markdown(report: Report, topic: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    title = topic.title() if len(topic) < 80 else topic[:77] + "..."

    total_sources = sum(s.sources_found for s in report.sections)
    lines = [
        f"# {title}",
        f"*deep research -- {total_sources} sources -- {report.total_words} words -- generated {timestamp}*",
        "",
        "---",
        "",
    ]

    section_blocks = []
    for section in report.sections:
        body = re.sub(r"\n{3,}", "\n\n", section.text.strip())
        heading = f"## {section.section.title}"
        section_blocks.append(f"{heading}\n\n{body}")

    lines.append("\n\n---\n\n".join(section_blocks))
    lines.append("")
    lines.append("---")
    lines.append("")

    seen_urls = set()
    source_lines = []
    idx = 1
    for section in report.sections:
        for source in section.sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                source_lines.append(f"{idx}. [{source.title}]({source.url})")
                idx += 1

    lines.append("## Sources")
    lines.append("")
    lines.extend(source_lines)
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("### Report Metadata")
    lines.append(f"- Sources used: {total_sources} across {len(report.sections)} sections (min {settings.MIN_SOURCES_PER_SUBTOPIC}/section target)")
    lines.append(f"- Total length: {report.total_words:,} words (target: {settings.MIN_WORDS_TOTAL:,})")

    under_target_sources = [s for s in report.sections if s.sources_found < settings.MIN_SOURCES_PER_SUBTOPIC]
    if under_target_sources:
        lines.append(
            "- Sections with limited sources: " +
            ", ".join(f'"{s.section.title}" ({s.sources_found} found)' for s in under_target_sources)
        )
    else:
        lines.append("- Sections with limited sources: none")

    if report.flagged_sections:
        lines.append(f"- Sections below target: {', '.join(report.flagged_sections)}")
    else:
        lines.append("- Sections below target: none")

    contradictions = report.metadata.get("flagged_contradictions", [])
    if contradictions:
        lines.append("- Possible cross-section contradictions:")
        lines.extend(f"  - {c}" for c in contradictions)

    per_section = []
    for s in report.sections:
        status = "OK" if not s.under_minimum else f"BELOW MIN ({s.word_count} words)"
        per_section.append(f"  - {s.section.title}: {s.sources_found} sources, {s.word_count} words [{status}]")
    lines.append("- Per-section breakdown:")
    lines.extend(per_section)
    lines.append("")

    return "\n".join(lines)


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
        await update_research_run(run_id, progress="Decomposing topic into sections...")
        sections = await decompose(topic)
        logger.info(f"Decomposed into {len(sections)} sections")

        section_results: List[SectionResult] = []
        for i, section in enumerate(sections):
            await update_research_run(
                run_id,
                progress=f"Gathering sources for section {i+1}/{len(sections)}: {section.title}",
            )
            sources = await gather_sources(section)
            section_results.append(SectionResult(
                section=section,
                sources=sources,
                sources_found=len(sources),
            ))

        await update_research_run(run_id, progress=f"Writing {len(section_results)} sections (concurrency={SECTION_WRITE_CONCURRENCY})...")
        written_sections = await write_all_sections(section_results)

        for r in written_sections:
            logger.info(
                f"Section '{r.section.title}': words={r.word_count} sources={r.sources_found} "
                f"attempts={r.attempts} under_min={r.under_minimum} call_failed={r.call_failed}"
            )

        pre_assembly_words = sum(s.word_count for s in written_sections)
        logger.info(f"Pre-assembly total: {pre_assembly_words} words across {len(written_sections)} sections")

        await update_research_run(run_id, progress="Assembling report...")
        report = await assemble_report(topic, written_sections)
        logger.info(f"Final report: {report.total_words} words, flagged={report.flagged_sections}")

        report_markdown = _render_report_markdown(report, topic)
        report_html = markdown_to_odysseus_html(report_markdown, topic)

        total_sources = sum(s.sources_found for s in report.sections)
        await update_research_run(
            run_id,
            status="completed",
            sources_count=total_sources,
            report=report_markdown,
            report_html=report_html,
            completed_at=datetime.utcnow().isoformat(),
        )

        return {
            "report": report_markdown,
            "report_html": report_html,
            "run_id": run_id,
            "metadata": report.metadata,
            "flagged_sections": report.flagged_sections,
            "total_words": report.total_words,
        }

    except SectionGenerationError as e:
        await update_research_run(run_id, status="failed", error=str(e))
        logger.error(f"Research section generation failed: {e}")
        return {
            "report": f"Research failed: {e}",
            "report_html": markdown_to_odysseus_html(f"Research failed: {e}", topic),
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
