import os
import re
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.config import settings
from core.tools.browser import (
    search_searxng_and_ddg, fetch_all, is_usable, _content_hash,
)
from core.agents.opencode_engine import run_opencode_task
from core.memory.db import create_briefing_run, update_briefing_run, update_automation
from core.tools.report_builder import generate_pdf, save_report_files, slugify
from core.tools.ntfy import send_ntfy

logger = logging.getLogger("pings.agents.daily_brief")

# ── Constants ──────────────────────────────────────────────────────────

MIN_SOURCES_PER_EVENT = 2
MAX_SOURCES_PER_EVENT = 4
MAX_ITEMS = 12
MAX_ANALYSIS_WORDS = 90
MAX_BRIEF_WORDS = 900
BRIEF_ITEM_CONCURRENCY = 4

USER_CONTEXT = (
    "someone building a self-hosted personal AI assistant platform, "
    "tracking model pricing, API changes, agent tooling, and open-source AI infrastructure"
)

# ── Models ─────────────────────────────────────────────────────────────


class BriefItem(BaseModel):
    headline: str
    event_date: str
    rank: int
    search_query: str


class RenderedItem(BaseModel):
    headline: str
    event_date: str
    rank: int
    bullets: List[str]
    analysis: str
    source_url: str = ""
    source_title: str = ""


class Brief(BaseModel):
    topic: str
    date: str
    items: List[RenderedItem]
    total_words: int = 0


# ── Stage 1: Decompose (event-level, date-filtered) ───────────────────


async def decompose_daily_events(topic_scope: str, since: datetime) -> List[BriefItem]:
    since_str = since.strftime("%Y-%m-%d %H:%M UTC")
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    prompt = (
        f"List the 8-12 most significant {topic_scope} news events that occurred "
        f"specifically between {since_str} and {now_str}.\n\n"
        f"RULES:\n"
        f"- Only discrete reported events — no general trend pieces, opinion columns, or explainers\n"
        f"- Each must be a specific thing that happened on a specific date\n"
        f"- Discard anything older than {since_str}\n"
        f"- Rank by significance (most important = rank 1)\n\n"
        f"Return a JSON array of objects, each with:\n"
        f'- "headline": one-line event description\n'
        f'- "event_date": ISO date when it happened (YYYY-MM-DD)\n'
        f'- "rank": significance order (1 = most important)\n'
        f'- "search_query": a specific search query to find sources about this event (8-15 words)\n\n'
        f"Return ONLY the JSON array, no explanation:"
    )

    response = await run_opencode_task(
        task=prompt,
        system_context="You are a news editor. Return only valid JSON.",
        timeout=60,
    )

    try:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            items_data = json.loads(json_match.group())
            items = []
            for item in items_data:
                event_date = item.get("event_date", "")
                if event_date and event_date < since.strftime("%Y-%m-%d"):
                    logger.info(f"Skipping stale event: {item.get('headline', '')} (date={event_date})")
                    continue
                items.append(BriefItem(
                    headline=item.get("headline", ""),
                    event_date=event_date,
                    rank=item.get("rank", len(items) + 1),
                    search_query=item.get("search_query", item.get("headline", topic_scope)),
                ))
            items.sort(key=lambda x: x.rank)
            return items[:MAX_ITEMS]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse decompose response: {e}")

    return []


# ── Stage 2: Gather sources (light, 2-4 per event) ────────────────────


async def gather_event_sources(item: BriefItem) -> List:
    """Return 2-4 usable sources for one event. Drop event if < 2 found."""
    from core.schemas import Source

    seen_urls: set = set()
    seen_hashes: set = set()
    kept: List[Source] = []

    raw_results = await search_searxng_and_ddg(item.search_query)
    candidates = [r for r in raw_results if r.url not in seen_urls]

    fetched = await fetch_all(candidates[:10])
    usable = [f for f in fetched if is_usable(f)]

    for f in usable:
        content_h = _content_hash(f.full_text or "")
        if content_h not in seen_hashes:
            seen_hashes.add(content_h)
            seen_urls.add(f.url)
            kept.append(f)
        if len(kept) >= MAX_SOURCES_PER_EVENT:
            break

    if len(kept) < MIN_SOURCES_PER_EVENT:
        logger.info(f"Dropping event '{item.headline}': only {len(kept)} sources")
        return []

    logger.info(f"Gathered {len(kept)} sources for event '{item.headline}'")
    return kept


# ── Stage 3: Write structured item (not prose) ────────────────────────


async def write_brief_item(item: BriefItem, sources: list, user_context: str) -> Optional[RenderedItem]:
    from core.schemas import Source

    sources_text = "\n".join(
        f"[{i+1}] {s.title} — {s.url}\n{(s.full_text or '')[:800]}"
        for i, s in enumerate(sources[:4])
    )

    prompt = (
        f"Write a brief news item based on these sources.\n\n"
        f"HEADLINE: {item.headline}\n"
        f"EVENT DATE: {item.event_date}\n"
        f"SOURCES:\n{sources_text}\n\n"
        f"Write EXACTLY this format:\n"
        f"### {item.headline}\n\n"
        f"• First key fact\n"
        f"• Second key fact\n"
        f"• Third key fact\n\n"
        f"Why it matters: [one sentence, max {MAX_ANALYSIS_WORDS} words, connecting to: {user_context}]\n"
        f"Source: {sources[0].url}\n\n"
        f"RULES:\n"
        f"- 3-5 short bullet points, just the facts, no elaboration\n"
        f"- One 'Why it matters' line, max {MAX_ANALYSIS_WORDS} words\n"
        f"- Do NOT write paragraphs\n"
        f"- Do NOT restate the headline in the bullets\n"
        f"- If there's no genuine connection to the user context, write a general significance line"
    )

    for attempt in range(3):
        try:
            draft = await run_opencode_task(
                task=prompt,
                system_context="You write concise news briefs. Output only the structured item, nothing else.",
                timeout=90,
            )

            if not draft or not draft.strip():
                continue

            return _parse_rendered_item(draft, item, sources)
        except Exception as e:
            logger.warning(f"write_brief_item attempt {attempt+1} failed: {e}")
            await asyncio.sleep(2)

    return None


def _parse_rendered_item(draft: str, item: BriefItem, sources: list) -> RenderedItem:
    """Parse LLM output into a RenderedItem."""
    lines = draft.strip().split("\n")
    bullets = []
    analysis = ""
    source_url = sources[0].url if sources else ""
    source_title = sources[0].title if sources else ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("• ") or stripped.startswith("- "):
            bullets.append(stripped[2:])
        elif stripped.lower().startswith("why it matters:"):
            analysis = stripped.split(":", 1)[1].strip()
        elif stripped.lower().startswith("source:"):
            url_part = stripped.split(":", 1)[1].strip()
            if url_part.startswith("http"):
                source_url = url_part

    if not analysis:
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("•") and not stripped.startswith("-") and not stripped.lower().startswith("source"):
                if len(stripped.split()) <= MAX_ANALYSIS_WORDS:
                    analysis = stripped
                    break

    return RenderedItem(
        headline=item.headline,
        event_date=item.event_date,
        rank=item.rank,
        bullets=bullets[:5],
        analysis=analysis,
        source_url=source_url,
        source_title=source_title,
    )


# ── Stage 4: Assemble brief (trim, don't pad) ─────────────────────────


def _count_words(text: str) -> int:
    return len(text.split())


def assemble_brief(topic: str, date: str, items: List[RenderedItem]) -> Brief:
    total_words = sum(
        _count_words(" ".join(i.bullets) + " " + i.analysis)
        for i in items
    )

    if total_words > MAX_BRIEF_WORDS:
        trimmed = []
        running = 0
        for item in items:
            item_words = _count_words(" ".join(item.bullets) + " " + item.analysis)
            if running + item_words <= MAX_BRIEF_WORDS:
                trimmed.append(item)
                running += item_words
            else:
                break
        items = trimmed
        total_words = running

    return Brief(topic=topic, date=date, items=items, total_words=total_words)


# ── Stage 5: Render markdown ──────────────────────────────────────────


def render_brief_markdown(brief: Brief) -> str:
    lines = [
        f"🗞️ {brief.topic} — {brief.date}",
        f"*Covering news from {brief.date}*",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for item in brief.items:
        lines.append(f"📌 {item.headline}")
        for bullet in item.bullets:
            lines.append(f"• {bullet}")
        lines.append(f"→ Why it matters: {item.analysis}")
        if item.source_url:
            lines.append(f"🔗 {item.source_url}")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

    return "\n".join(lines)


# ── Stage 6: Render brief HTML (card-per-item) ────────────────────────


def brief_markdown_to_html(brief: Brief) -> str:
    import html as html_mod

    items_html = ""
    for item in brief.items:
        bullets_html = "".join(f"<li>{html_mod.escape(b)}</li>" for b in item.bullets)
        source_link = ""
        if item.source_url:
            source_link = (
                f'<a href="{html_mod.escape(item.source_url)}" target="_blank" '
                f'rel="noopener" class="source-link">🔗 Source</a>'
            )

        items_html += f"""
        <div class="brief-card">
            <div class="card-header">
                <span class="card-pin">📌</span>
                <h2>{html_mod.escape(item.headline)}</h2>
            </div>
            <div class="card-date">{html_mod.escape(item.event_date)}</div>
            <ul class="card-bullets">{bullets_html}</ul>
            <div class="card-analysis">
                <span class="analysis-label">→ Why it matters:</span>
                {html_mod.escape(item.analysis)}
            </div>
            {source_link}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_mod.escape(brief.topic)} — Daily Brief</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #0a0a12;
  color: #c8ccd8;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

.container {{
  max-width: 680px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}}

.brief-header {{
  text-align: center;
  margin-bottom: 2rem;
}}

.brief-header h1 {{
  font-size: 1.6rem;
  font-weight: 700;
  color: #a5b4fc;
  margin-bottom: 0.25rem;
}}

.brief-header .subtitle {{
  font-size: 0.8rem;
  color: #6b7094;
}}

.brief-header .divider {{
  height: 1px;
  background: rgba(165, 180, 252, 0.15);
  margin: 1.25rem 0 0;
}}

.brief-card {{
  background: rgba(99, 102, 241, 0.04);
  border: 1px solid rgba(165, 180, 252, 0.08);
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
}}

.card-header {{
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}}

.card-pin {{
  font-size: 1rem;
  flex-shrink: 0;
  margin-top: 2px;
}}

.card-header h2 {{
  font-size: 1.05rem;
  font-weight: 600;
  color: #eef0f6;
  line-height: 1.35;
}}

.card-date {{
  font-size: 0.72rem;
  color: #6b7094;
  margin-bottom: 0.65rem;
}}

.card-bullets {{
  list-style: none;
  padding: 0;
  margin: 0 0 0.65rem;
}}

.card-bullets li {{
  font-size: 0.88rem;
  color: #b0b6cc;
  line-height: 1.55;
  padding-left: 1.1rem;
  position: relative;
  margin-bottom: 0.25rem;
}}

.card-bullets li::before {{
  content: "•";
  position: absolute;
  left: 0;
  color: #818cf8;
}}

.card-analysis {{
  font-size: 0.82rem;
  color: #a5b4fc;
  line-height: 1.5;
  font-style: italic;
  padding: 0.5rem 0;
  border-top: 1px solid rgba(165, 180, 252, 0.06);
}}

.analysis-label {{
  font-weight: 600;
  font-style: normal;
}}

.source-link {{
  display: inline-block;
  font-size: 0.75rem;
  color: #818cf8;
  text-decoration: none;
  margin-top: 0.35rem;
}}

.source-link:hover {{
  color: #a5b4fc;
  text-decoration: underline;
}}
</style>
</head>
<body>
<div class="container">
  <div class="brief-header">
    <h1>🗞️ {html_mod.escape(brief.topic)}</h1>
    <div class="subtitle">Covering news from {html_mod.escape(brief.date)}</div>
    <div class="divider"></div>
  </div>
  {items_html}
</div>
</body>
</html>"""


# ── Main pipeline ──────────────────────────────────────────────────────


async def run_daily_brief(automation_id: int) -> Dict[str, Any]:
    from core.memory.db import get_automation

    automation = await get_automation(automation_id)
    if not automation:
        logger.error(f"Automation {automation_id} not found")
        return {"error": "Automation not found"}

    run_id = await create_briefing_run(automation_id)
    await update_briefing_run(run_id, status="running")
    await update_automation(automation_id, last_run_at=datetime.utcnow().isoformat())

    try:
        topic = automation["instructions"]
        since = datetime.utcnow() - timedelta(hours=24)
        date_str = datetime.utcnow().strftime("%B %d, %Y")

        logger.info(f"Decomposing events for '{topic}' since {since.isoformat()}")
        events = await decompose_daily_events(topic, since)
        if not events:
            raise RuntimeError("No events found for the last 24h")

        logger.info(f"Found {len(events)} events, gathering sources...")
        gather_tasks = [gather_event_sources(e) for e in events]
        gather_results = await asyncio.gather(*gather_tasks, return_exceptions=True)

        items_with_sources = []
        for event, result in zip(events, gather_results):
            if isinstance(result, Exception):
                logger.warning(f"Gather failed for '{event.headline}': {result}")
                continue
            if result:
                items_with_sources.append((event, result))

        logger.info(f"{len(items_with_sources)} events have sources, writing items...")
        sem = asyncio.Semaphore(BRIEF_ITEM_CONCURRENCY)

        async def _write_one(ev, srcs):
            async with sem:
                return await write_brief_item(ev, srcs, USER_CONTEXT)

        write_tasks = [_write_one(ev, srcs) for ev, srcs in items_with_sources]
        write_results = await asyncio.gather(*write_tasks, return_exceptions=True)

        rendered = []
        for r in write_results:
            if isinstance(r, RenderedItem):
                rendered.append(r)

        if not rendered:
            raise RuntimeError("No items could be written")

        brief = assemble_brief(automation["name"], date_str, rendered)
        logger.info(f"Brief assembled: {len(brief.items)} items, {brief.total_words} words")

        brief_md = render_brief_markdown(brief)
        brief_html = brief_markdown_to_html(brief)

        file_info = save_report_files(
            f"brief-{automation['name']}", run_id, brief_html, brief_md
        )
        pdf_path = f"{file_info['report_dir']}/brief.pdf"
        await generate_pdf(file_info["html_path"], pdf_path)

        await update_briefing_run(
            run_id,
            status="success",
            completed_at=datetime.utcnow().isoformat(),
            pdf_path=pdf_path,
        )

        await _send_telegram_brief(automation["name"], pdf_path, brief)

        total_sources = len(items_with_sources) * 3
        await send_ntfy(
            title="Daily Brief Ready",
            message=f"{automation['name']}: {len(brief.items)} items, {brief.total_words} words",
            priority="default",
            tags="newspaper",
        )

        return {
            "run_id": run_id,
            "status": "success",
            "pdf_path": pdf_path,
            "items": len(brief.items),
            "total_words": brief.total_words,
        }

    except Exception as e:
        logger.error(f"Daily brief failed: {e}", exc_info=True)
        await update_briefing_run(run_id, status="failed", error_message=str(e))
        await _send_telegram_error(automation["name"], str(e))
        return {"run_id": run_id, "status": "failed", "error": str(e)}


# ── Telegram delivery ──────────────────────────────────────────────────


async def _send_telegram_brief(name: str, pdf_path: str, brief: Brief) -> None:
    import httpx

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
    if not bot_token or not chat_id:
        return

    summary_lines = [f"📌 {item.headline}" for item in brief.items[:5]]
    summary = "\n".join(summary_lines)
    if len(brief.items) > 5:
        summary += f"\n+{len(brief.items) - 5} more"

    message = (
        f"🗞️ {name}\n"
        f"{len(brief.items)} items • {brief.total_words} words\n\n"
        f"{summary}"
    )

    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
        )

    if os.path.exists(pdf_path):
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                with open(pdf_path, "rb") as f:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendDocument",
                        data={"chat_id": chat_id, "caption": f"Brief: {name}"},
                        files={"document": (os.path.basename(pdf_path), f, "application/pdf")},
                    )
        except Exception as e:
            logger.error(f"Failed to send brief PDF: {e}")


async def _send_telegram_error(name: str, error: str) -> None:
    import httpx

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
    if not bot_token or not chat_id:
        return

    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": f"Brief failed: {name}\nError: {error}"},
        )
