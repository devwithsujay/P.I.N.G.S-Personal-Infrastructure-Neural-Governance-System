import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.memory.db import (
    get_automation, create_briefing_run, update_briefing_run,
    update_automation,
)
from core.schemas import SectionResult, Source
from core.agents.research import decompose, gather_sources, write_all_sections, assemble_report, _render_report_markdown
from core.agents.html_renderer import markdown_to_odysseus_html
from core.tools.report_builder import generate_pdf, save_report_files

logger = logging.getLogger("pings.agents.briefing")

BRIEFING_INSTRUCTION = (
    "Prioritize specific facts, numbers, and named sources over general "
    "summary. Do not restate common knowledge. Every claim must trace to a "
    "fetched source. If nothing genuinely new exists in the last 24h for "
    "a sub-topic, say so explicitly rather than padding with generic content."
)


async def generate_briefing(automation_id: int) -> Dict[str, Any]:
    automation = await get_automation(automation_id)
    if not automation:
        logger.error(f"Automation {automation_id} not found")
        return {"error": "Automation not found"}

    run_id = await create_briefing_run(automation_id)
    await update_briefing_run(run_id, status="running")
    await update_automation(automation_id, last_run_at=datetime.utcnow().isoformat())

    try:
        topic = automation["instructions"]

        sections = await decompose(topic)
        logger.info(f"Briefing decomposed into {len(sections)} sections")

        section_results = []
        for i, section in enumerate(sections):
            sources = await gather_sources(section)
            section_results.append(SectionResult(
                section=section,
                sources=sources,
                sources_found=len(sources),
            ))

        written_sections = await write_all_sections(section_results)

        report = await assemble_report(topic, written_sections)
        report_markdown = _render_report_markdown(report, topic)
        report_html = markdown_to_odysseus_html(report_markdown, topic)

        total_sources = sum(s.sources_found for s in report.sections)

        file_info = save_report_files(f"briefing-{automation['name']}", run_id, report_html, report_markdown)
        pdf_path = f"{file_info['report_dir']}/briefing.pdf"
        await generate_pdf(file_info["html_path"], pdf_path)

        await update_briefing_run(
            run_id,
            status="success",
            completed_at=datetime.utcnow().isoformat(),
            pdf_path=pdf_path,
        )

        await _send_telegram_pdf(automation["name"], pdf_path, topic, total_sources)

        return {
            "run_id": run_id,
            "status": "success",
            "pdf_path": pdf_path,
            "sources": total_sources,
        }

    except Exception as e:
        logger.error(f"Briefing generation failed: {e}")
        await update_briefing_run(run_id, status="failed", error_message=str(e))
        await _send_telegram_error(automation["name"], str(e))
        return {"run_id": run_id, "status": "failed", "error": str(e)}


async def _send_telegram_pdf(name: str, pdf_path: str, topic: str, source_count: int) -> None:
    import os
    import httpx

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
    if not bot_token or not chat_id:
        return

    message = (
        f"Briefing ready: {name}\n"
        f"Sources: {source_count}\n"
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
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
                        data={"chat_id": chat_id, "caption": f"Briefing: {name}"},
                        files={"document": (os.path.basename(pdf_path), f, "application/pdf")},
                    )
        except Exception as e:
            logger.error(f"Failed to send briefing PDF: {e}")


async def _send_telegram_error(name: str, error: str) -> None:
    import os
    import httpx

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
    if not bot_token or not chat_id:
        return

    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": f"Briefing failed: {name}\nError: {error}"},
        )
