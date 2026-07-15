import os
import re
import logging
import asyncio
import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pings-bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0"))
CORE_API = os.getenv("PINGS_CORE_URL", "http://pings-core:8000")
API_KEY = os.getenv("BRAIN_SECRET_KEY", "")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

RESEARCH_POLL_INTERVAL = 15
RESEARCH_MAX_WAIT = 1800

RESEARCH_PATTERNS = [
    r"^research\s+(on|about)\s+(.+)",
    r"^deep\s+research\s+(on|about)\s+(.+)",
    r"^research\s+(.+)",
    r"^investigate\s+(.+)",
    r"^analyze\s+(.+)",
    r"^study\s+(.+)",
]


def get_session_id(message: types.Message) -> str:
    return str(message.from_user.id)


def is_allowed(message: types.Message) -> bool:
    if ALLOWED_USER_ID == 0:
        return True
    return message.from_user.id == ALLOWED_USER_ID


def extract_research_topic(text: str) -> str:
    for pattern in RESEARCH_PATTERNS:
        m = re.match(pattern, text, re.IGNORECASE)
        if m:
            return m.group(m.lastindex).strip()
    return text.strip()


async def core_request(path: str, payload: dict) -> dict:
    url = f"{CORE_API}{path}"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def core_get(path: str) -> dict:
    url = f"{CORE_API}{path}"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def poll_research_and_send(chat_id: int, run_id: int, topic: str):
    try:
        elapsed = 0
        last_progress = ""
        while elapsed < RESEARCH_MAX_WAIT:
            await asyncio.sleep(RESEARCH_POLL_INTERVAL)
            elapsed += RESEARCH_POLL_INTERVAL

            try:
                run_data = await core_get(f"/research/runs/{run_id}")
            except Exception as e:
                logger.warning(f"Poll failed for run {run_id}: {e}")
                continue

            status = run_data.get("status", "")
            progress = run_data.get("progress", "")

            if progress and progress != last_progress:
                try:
                    await bot.send_message(chat_id, f"Research progress: {progress}")
                except Exception:
                    pass
                last_progress = progress

            if status == "completed":
                try:
                    html_url = f"{CORE_API}/research/{run_id}/report.html"
                    await bot.send_message(chat_id, f"Research complete. PDF sent above.\nHTML report: {html_url}")
                except Exception as e:
                    logger.error(f"Failed to send completion message: {e}")
                return

            if status == "failed":
                error = run_data.get("error", "Unknown error")
                await bot.send_message(chat_id, f"Research failed: {error}")
                return

        await bot.send_message(chat_id, f"Research timed out after {RESEARCH_MAX_WAIT//60} minutes. Check the web UI for status.")

    except Exception as e:
        logger.error(f"Poll task error: {e}")
        try:
            await bot.send_message(chat_id, f"Error monitoring research: {e}")
        except Exception:
            pass


# ── /start ──────────────────────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_allowed(message):
        await message.reply("Access denied.")
        return
    await message.reply(
        "<b>P.I.N.G.S Core v2</b>\n"
        "Personal Infrastructure & Neural Governance System\n\n"
        "Send any message to chat, or attach a photo/document.\n"
        "Use 'research about &lt;topic&gt;' for deep research."
    )


# ── /history ─────────────────────────────────────────────────────────────────
@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    if not is_allowed(message):
        await message.reply("Access denied.")
        return
    sid = get_session_id(message)
    try:
        data = await core_get(f"/sessions/{sid}")
        if not data:
            await message.reply("No history found.")
            return
        lines = []
        for entry in data[-20:]:
            role = entry.get("role", "?")
            content = entry.get("content", "")[:200]
            lines.append(f"<b>{role}</b>: {content}")
        await message.reply("\n\n".join(lines))
    except Exception as e:
        await message.reply(f"Failed to fetch history: {e}")


# ── /clear ──────────────────────────────────────────────────────────────────
@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    if not is_allowed(message):
        await message.reply("Access denied.")
        return
    sid = get_session_id(message)
    try:
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(f"{CORE_API}/history/{sid}", headers=headers)
            resp.raise_for_status()
        await message.reply("History cleared.")
    except Exception as e:
        await message.reply(f"Failed to clear history: {e}")


# ── Photo / Document uploads ────────────────────────────────────────────────
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if not is_allowed(message):
        return
    sid = get_session_id(message)
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)

    files = {"file": (f"{photo.file_id}.jpg", file_bytes, "image/jpeg")}
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{CORE_API}/chat/upload",
            data={"session_id": sid, "caption": message.caption or ""},
            files=files,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    await message.reply(data.get("response", "Image processed."))


@dp.message(F.document)
async def handle_document(message: types.Message):
    if not is_allowed(message):
        return
    sid = get_session_id(message)
    doc = message.document
    file = await bot.get_file(doc.file_id)
    file_bytes = await bot.download_file(file.file_path)

    files = {"file": (doc.file_name, file_bytes, doc.mime_type or "application/octet-stream")}
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{CORE_API}/chat/upload",
            data={"session_id": sid, "caption": message.caption or ""},
            files=files,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    await message.reply(data.get("response", "Document processed."))


# ── Free text → intent classify → agent dispatch ───────────────────────────
@dp.message(F.text & ~F.text.startswith("/"))
async def handle_free_text(message: types.Message):
    if not is_allowed(message):
        return
    sid = get_session_id(message)
    text = message.text.strip()

    is_research = any(re.match(p, text, re.IGNORECASE) for p in RESEARCH_PATTERNS)

    try:
        data = await core_request(
            "/chat",
            {"session_id": sid, "message": text},
        )
        reply = data.get("reply", "No response from core.")
        await message.reply(reply)

        if is_research:
            run_id_match = re.search(r"Run ID:\s*(\d+)", reply)
            if run_id_match:
                run_id = int(run_id_match.group(1))
                topic = extract_research_topic(text)
                asyncio.create_task(poll_research_and_send(message.chat.id, run_id, topic))

    except httpx.HTTPStatusError as e:
        logger.error("Core API error: %s", e)
        await message.reply("Core API error. Check logs.")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        await message.reply("Something went wrong.")


# ── Main ────────────────────────────────────────────────────────────────────
async def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    logger.info("Starting P.I.N.G.S bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
