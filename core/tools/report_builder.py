import os
import re
import json
import asyncio
import logging
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import slugify

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


def convert_html_to_telegraph_nodes(html: str) -> list:
    class TelegraphParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.nodes = []
            self.current_node = None
            self.tag_map = {
                'h1': 'h3', 'h2': 'h3', 'h3': 'h4', 'h4': 'h4',
                'p': 'p', 'b': 'b', 'strong': 'b', 'i': 'i',
                'em': 'i', 'code': 'code', 'pre': 'pre',
                'blockquote': 'blockquote', 'ul': 'ul', 'ol': 'ol',
                'li': 'li', 'br': 'br', 'hr': 'hr'
            }
            self.skip_tags = {'div', 'span', 'section', 'article',
                              'header', 'footer', 'nav', 'style',
                              'script', 'table', 'thead', 'tbody',
                              'tr', 'th', 'td'}

        def handle_starttag(self, tag, attrs):
            if tag in self.tag_map:
                self.current_node = {'tag': self.tag_map[tag], 'children': []}

        def handle_endtag(self, tag):
            if tag in self.tag_map and self.current_node:
                if self.current_node['children']:
                    self.nodes.append(self.current_node)
                self.current_node = None

        def handle_data(self, data):
            text = data.strip()
            if not text:
                return
            if self.current_node:
                self.current_node['children'].append(text)
            else:
                self.nodes.append({'tag': 'p', 'children': [text]})

    parser = TelegraphParser()
    parser.feed(html)
    return parser.nodes[:300]


async def publish_to_telegraph(title: str, html_content: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            account = await client.post(
                "https://api.telegra.ph/createAccount",
                json={"short_name": "PINGS", "author_name": "P.I.N.G.S Research"}
            )
            token = account.json()["result"]["access_token"]

            telegraph_content = convert_html_to_telegraph_nodes(html_content)

            content_size = len(json.dumps(telegraph_content).encode('utf-8'))
            if content_size > 60000:
                telegraph_content = telegraph_content[:100]
                telegraph_content.append({
                    "tag": "p",
                    "children": [{"tag": "i", "children": ["Report truncated for Telegraph. Full report available via link."]}]
                })

            page = await client.post(
                "https://api.telegra.ph/createPage",
                json={
                    "access_token": token,
                    "title": title[:256],
                    "content": telegraph_content,
                    "return_content": False
                }
            )
            url = page.json()["result"]["url"]
            logger.info(f"Published to Telegraph: {url}")
            return url
    except Exception as e:
        logger.warning(f"Telegraph publish failed: {e}")
        return ""


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

    telegraph_url = ""
    try:
        with open(html_path) as f:
            html_content = f.read()
        telegraph_url = await publish_to_telegraph(topic, html_content)
    except Exception as e:
        logger.warning(f"Telegraph publish failed: {e}")

    duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"
    lines = [
        "Research complete",
        "",
        f"Topic: {topic}",
        f"Sources: {source_count} | Duration: {duration_str}",
        "",
    ]

    if telegraph_url:
        lines.append(f"Read on Telegram: {telegraph_url}")
    lines.append(f"Full report: {html_url}")

    message_text = "\n".join(lines)

    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message_text,
            }
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
