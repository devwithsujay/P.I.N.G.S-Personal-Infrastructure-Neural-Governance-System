import os
import logging
import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pings-bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0"))
CORE_API = os.getenv("PINGS_CORE_URL", "http://pings-core:8000")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


class ResearchState(StatesGroup):
    waiting_topic = State()


async def fetch_models() -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{CORE_API}/api/models")
            resp.raise_for_status()
            data = resp.json()
            return data.get("models", data.get("available", []))
    except Exception:
        return []


def get_session_id(message: types.Message) -> str:
    return str(message.from_user.id)


def is_allowed(message: types.Message) -> bool:
    if ALLOWED_USER_ID == 0:
        return True
    return message.from_user.id == ALLOWED_USER_ID


async def core_request(path: str, payload: dict) -> dict:
    url = f"{CORE_API}{path}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


async def core_get(path: str, params: dict = None) -> dict:
    url = f"{CORE_API}{path}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url, params=params)
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
        "Commands:\n"
        "/chat - Start a chat session\n"
        "/model - Switch AI model\n"
        "/research - Start a research run\n\n"
        "Send any message to chat, or attach a photo/document."
    )


# ── /model ──────────────────────────────────────────────────────────────────
@dp.message(Command("model"))
async def cmd_model(message: types.Message):
    if not is_allowed(message):
        return
    models = await fetch_models()
    if not models:
        await message.reply("No models available from core API.")
        return
    sid = get_session_id(message)
    data = await core_get("/api/model/current", {"session_id": sid})
    current = data.get("model", "")

    buttons = []
    for m in models:
        mid = m.get("id", m.get("model", ""))
        name = m.get("name", mid)
        label = f"✅ {name}" if mid == current else name
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"model:{mid}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(f"<b>Current model:</b> {current}\n\nSelect a model:", reply_markup=kb)


@dp.callback_query(F.data.startswith("model:"))
async def callback_model(callback: types.CallbackQuery):
    model_id = callback.data.split(":", 1)[1]
    sid = get_session_id(callback.message)
    await core_request("/api/model/set", {"session_id": sid, "model": model_id})
    await callback.message.edit_text(f"Switched to <b>{model_id}</b>.")
    await callback.answer()


# ── /research ───────────────────────────────────────────────────────────────
@dp.message(Command("research"))
async def cmd_research(message: types.Message, state: FSMContext):
    if not is_allowed(message):
        return
    await state.set_state(ResearchState.waiting_topic)
    await message.reply("What topic should I research?")


@dp.message(ResearchState.waiting_topic)
async def process_research_topic(message: types.Message, state: FSMContext):
    topic = message.text.strip()
    sid = get_session_id(message)
    await message.reply(f"Starting research on: <b>{topic}</b>...")
    data = await core_request("/api/research/start", {"session_id": sid, "topic": topic})
    run_id = data.get("run_id", "unknown")
    await message.reply(f"Research run created: <code>{run_id}</code>\nResults will be sent when complete.")
    await state.clear()


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
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{CORE_API}/api/chat/upload",
            data={"session_id": sid, "caption": message.caption or ""},
            files=files,
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
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{CORE_API}/api/chat/upload",
            data={"session_id": sid, "caption": message.caption or ""},
            files=files,
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
            "/api/chat/message",
            {"session_id": sid, "content": text},
        )
        reply = data.get("response", "No response from core.")
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
