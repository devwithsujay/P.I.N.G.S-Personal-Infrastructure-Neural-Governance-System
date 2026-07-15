import os
import re
import asyncio
import logging
from datetime import datetime

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

import httpx

logger = logging.getLogger("pings.research.report_builder")

TAILSCALE_IP = os.getenv("TAILSCALE_NODE_PRIMARY", "localhost")
REPORTS_DIR = "/app/workspace/research"


async def generate_pdf(html_path: str, pdf_path: str) -> bool:
    try:
        from weasyprint import HTML as WeasyprintHTML
        loop = asyncio.get_event_loop()
        def _convert():
            WeasyprintHTML(filename=html_path).write_pdf(pdf_path)
        await loop.run_in_executor(None, _convert)
        logger.info(f"PDF generated: {pdf_path}")
        return True
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False


def save_report_files(topic: str, run_id: int, html: str, markdown: str) -> dict:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    slug = slugify(topic)[:50]
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    folder_name = f"{slug}-{timestamp}"
    report_dir = os.path.join(REPORTS_DIR, folder_name)
    os.makedirs(report_dir, exist_ok=True)

    html_path = os.path.join(report_dir, "report.html")
    md_path = os.path.join(report_dir, "report.md")

    with open(html_path, "w") as f:
        f.write(html)
    with open(md_path, "w") as f:
        f.write(markdown)

    html_url = f"http://{TAILSCALE_IP}/research/reports/{folder_name}/report.html"

    return {
        "html_path": html_path,
        "md_path": md_path,
        "report_dir": report_dir,
        "html_url": html_url,
        "folder_name": folder_name,
    }


async def send_telegram_notification(
    topic: str,
    run_id: int,
    html_path: str,
    pdf_path: str,
    html_url: str,
    source_count: int,
    duration_seconds: int,
) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")

    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not set, skipping notification")
        return

    duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"
    message_text = (
        f"Research complete\n\n"
        f"Topic: {topic}\n"
        f"Sources: {source_count} | Duration: {duration_str}\n\n"
        f"Full report: {html_url}"
    )

    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message_text},
        )

    if pdf_path and os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        if file_size > 50 * 1024 * 1024:
            logger.warning(f"PDF too large for Telegram: {file_size} bytes")
            return

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                with open(pdf_path, 'rb') as f:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendDocument",
                        data={
                            "chat_id": chat_id,
                            "caption": f"Research Report: {topic}",
                        },
                        files={"document": (os.path.basename(pdf_path), f, "application/pdf")}
                    )
            logger.info("PDF sent to Telegram")
        except Exception as e:
            logger.error(f"Failed to send PDF to Telegram: {e}")
