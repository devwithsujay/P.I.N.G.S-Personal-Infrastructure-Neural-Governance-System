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

ZEN_MODELS = [
    {"id": "opencode/mimo-v2.5-free", "name": "MiMo V2.5 Free", "tag": "default"},
    {"id": "opencode/deepseek-v4-flash-free", "name": "DeepSeek V4 Flash Free", "tag": ""},
    {"id": "opencode/nemotron-3-ultra-free", "name": "Nemotron 3 Ultra Free", "tag": ""},
    {"id": "opencode/big-pickle", "name": "Big Pickle", "tag": ""},
    {"id": "opencode/north-mini-code-free", "name": "North Mini Code Free", "tag": ""},
]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


class ResearchState(StatesGroup):
    waiting_topic = State()


class ChatState(StatesGroup):
    waiting_message = State()


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
        "/clear - Clear conversation history\n"
        "/history - View recent history\n"
        "/tasks - View active tasks\n"
        "/status - System status\n"
        "/model - Switch AI model\n"
        "/research - Start a research run\n\n"
        "Send any message to chat, or attach a photo/document."
    )


# ── /clear ──────────────────────────────────────────────────────────────────
@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    if not is_allowed(message):
        return
    sid = get_session_id(message)
    await core_request("/api/chat/clear", {"session_id": sid})
    await message.reply("History cleared.")


# ── /history ────────────────────────────────────────────────────────────────
@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    if not is_allowed(message):
        return
    sid = get_session_id(message)
    data = await core_get("/api/chat/history", {"session_id": sid, "limit": 20})
    messages = data.get("messages", [])
    if not messages:
        await message.reply("No history found.")
        return
    lines = []
    for m in messages:
        role = m.get("role", "unknown")
        content = m.get("content", "")[:200]
        lines.append(f"<b>{role}</b>: {content}")
    await message.reply("\n\n".join(lines))


# ── /tasks ──────────────────────────────────────────────────────────────────
@dp.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    if not is_allowed(message):
        return
    sid = get_session_id(message)
    data = await core_get("/api/tasks/list", {"session_id": sid})
    tasks = data.get("tasks", [])
    if not tasks:
        await message.reply("No active tasks.")
        return
    lines = []
    for t in tasks:
        status_icon = "⏳" if t["status"] == "pending" else "✅" if t["status"] == "done" else "🔄"
        lines.append(f"{status_icon} <b>{t['title']}</b> - {t['status']}")
    await message.reply("\n".join(lines))


# ── /status ─────────────────────────────────────────────────────────────────
@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if not is_allowed(message):
        return
    data = await core_get("/api/status")
    model = data.get("current_model", "unknown")
    uptime = data.get("uptime", "unknown")
    await message.reply(
        f"<b>System Status</b>\n\n"
        f"Model: {model}\n"
        f"Uptime: {uptime}\n"
        f"Core API: OK"
    )


# ── /model ──────────────────────────────────────────────────────────────────
@dp.message(Command("model"))
async def cmd_model(message: types.Message):
    if not is_allowed(message):
        return
    sid = get_session_id(message)
    data = await core_get("/api/model/current", {"session_id": sid})
    current = data.get("model", "opencode/mimo-v2.5-free")

    buttons = []
    for i, m in enumerate(ZEN_MODELS, 1):
        label = f"{m['name']}"
        if m["id"] == current:
            label = f"✅ {label}"
        if m["tag"] == "default" and m["id"] != current:
            label = f"⭐ {label}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"model:{m['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(f"<b>Current model:</b> {current}\n\nSelect a model:", reply_markup=kb)


@dp.callback_query(F.data.startswith("model:"))
async def callback_model(callback: types.CallbackQuery):
    model_id = callback.data.split(":", 1)[1]
    sid = get_session_id(callback.message)
    await core_request("/api/model/set", {"session_id": sid, "model": model_id})
    name = next((m["name"] for m in ZEN_MODELS if m["id"] == model_id), model_id)
    await callback.message.edit_text(f"Switched to <b>{name}</b>.")
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
