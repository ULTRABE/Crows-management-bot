import logging
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from config import API_ID, API_HASH, BOT_TOKEN

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- BOT CLIENT ----------------
app = Client(
    "crow_manager_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- IN-MEMORY SETTINGS ----------------
LINK_DELETE_ENABLED = {}  # chat_id: bool (default True)

# ---------------- ADMIN CHECK ----------------
async def is_admin(client: Client, message: Message) -> bool:
    if not message.from_user or not message.chat:
        return False
    try:
        member = await client.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except Exception:
        return False

# ---------------- START ----------------
@app.on_message(filters.command("start"))
def start_cmd(client, message: Message):
    message.reply_text("Bot is alive. Phase 0 OK.")

# ---------------- ADMIN TEST ----------------
@app.on_message(filters.command("admin") & filters.group)
async def admin_test_cmd(client, message: Message):
    if await is_admin(client, message):
        await message.reply_text("You are admin.")
    else:
        await message.reply_text("You are not admin.")

# ---------------- LINKS TOGGLE ----------------
@app.on_message(filters.command("links") & filters.group)
async def links_toggle(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    args = message.text.split(maxsplit=1)
    chat_id = message.chat.id

    if len(args) < 2:
        await message.reply_text("Usage: /links on | off")
        return

    state = args[1].lower()

    if state == "off":
        LINK_DELETE_ENABLED[chat_id] = False
        await message.reply_text("Link auto-delete disabled.")
    elif state == "on":
        LINK_DELETE_ENABLED[chat_id] = True
        await message.reply_text("Link auto-delete enabled.")
    else:
        await message.reply_text("Usage: /links on | off")

# ---------------- AUTO DELETE LINKS ----------------
LINK_REGEX = re.compile(
    r"(https?://|t\.me/|www\.)",
    re.IGNORECASE
)

@app.on_message(filters.group & filters.text)
async def auto_delete_links(client: Client, message: Message):
    chat_id = message.chat.id

    # default = enabled
    if LINK_DELETE_ENABLED.get(chat_id, True) is False:
        return

    if message.text and LINK_REGEX.search(message.text):
        try:
            await asyncio.sleep(5)
            await message.delete()
        except Exception:
            pass

# ---------------- RUN ----------------
app.run()
