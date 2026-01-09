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
LINK_DELETE_ENABLED = {}     # chat_id: bool
WELCOME_ENABLED = {}         # chat_id: bool
WELCOME_TEXT = {}            # chat_id: str

WELCOME_DELETE_AFTER = 10    # seconds

# ---------------- ADMIN CHECK (HELPER) ----------------
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
    message.reply_text("Bot is alive. Core system running.")

# ---------------- ADMINS LIST ----------------
@app.on_message(filters.command("admins") & filters.group)
async def list_admins(client: Client, message: Message):
    admins = []

    async for member in client.get_chat_members(
        message.chat.id,
        filter="administrators"
    ):
        user = member.user
        if user:
            admins.append(user.mention)

    if not admins:
        await message.reply_text("No admins found.")
        return

    text = "Admins:\n" + "\n".join(admins)
    await message.reply_text(text)

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

    if LINK_DELETE_ENABLED.get(chat_id, True) is False:
        return

    if message.text and LINK_REGEX.search(message.text):
        try:
            await asyncio.sleep(5)
            await message.delete()
        except Exception:
            pass

# ---------------- WELCOME COMMANDS ----------------
@app.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if not message.reply_to_message or not message.reply_to_message.text:
        await message.reply_text("Reply to a message to set welcome text.")
        return

    chat_id = message.chat.id
    WELCOME_TEXT[chat_id] = message.reply_to_message.text
    WELCOME_ENABLED[chat_id] = True

    await message.reply_text("Welcome message set.")

@app.on_message(filters.command("welcome") & filters.group)
async def toggle_welcome(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    args = message.text.split(maxsplit=1)
    chat_id = message.chat.id

    if len(args) < 2:
        await message.reply_text("Usage: /welcome on | off")
        return

    state = args[1].lower()

    if state == "on":
        WELCOME_ENABLED[chat_id] = True
        await message.reply_text("Welcome enabled.")
    elif state == "off":
        WELCOME_ENABLED[chat_id] = False
        await message.reply_text("Welcome disabled.")
    else:
        await message.reply_text("Usage: /welcome on | off")

# ---------------- WELCOME HANDLER ----------------
@app.on_message(filters.new_chat_members)
async def welcome_new_members(client: Client, message: Message):
    chat_id = message.chat.id

    if not WELCOME_ENABLED.get(chat_id, False):
        return

    text = WELCOME_TEXT.get(chat_id, "Welcome {mention}")

    for user in message.new_chat_members:
        final_text = text.replace("{mention}", user.mention)

        try:
            sent = await message.reply_text(final_text)
            await asyncio.sleep(WELCOME_DELETE_AFTER)
            await sent.delete()
        except Exception:
            pass

# ---------------- RUN ----------------
app.run()
