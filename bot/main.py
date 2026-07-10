import os
import logging
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


def get_session_id(message: types.Message) -> str:
    return str(message.from_user.id)


def is_allowed(message: types.Message) -> bool:
    if ALLOWED_USER_ID == 0:
        return True
    return message.from_user.id == ALLOWED_USER_ID


async def core_request(path: str, payload: dict) -> dict:
    url = f"{CORE_API}{path}"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


# ── /start ──────────────────────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_allowed(message):
        await message.reply("Access denied.")
        return
    await message.reply(
        "<b>P.I.N.G.S Core v2</b>\n"
        "Personal Infrastructure & Neural Governance System\n\n"
        "Send any message to chat, or attach a photo/document."
    )



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

    try:
        data = await core_request(
            "/chat",
            {"session_id": sid, "message": text},
        )
        reply = data.get("reply", "No response from core.")
        await message.reply(reply)
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
