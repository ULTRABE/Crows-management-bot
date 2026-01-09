import logging
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from config import API_ID, API_HASH, BOT_TOKEN

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- BOT CLIENT ----------------
app = Client(
    "crow_manager_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- IN-MEMORY SETTINGS ----------------
LINK_DELETE_ENABLED = {}
WELCOME_ENABLED = {}
WELCOME_TEXT = {}
RULES_TEXT = {}

WELCOME_DELETE_AFTER = 10

# ---------------- ADMIN CHECK ----------------
async def is_admin(client: Client, message: Message) -> bool:
    try:
        member = await client.get_chat_member(
            message.chat.id, message.from_user.id
        )
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except Exception:
        return False

# ---------------- START ----------------
@app.on_message(filters.command("start"))
def start_cmd(client, message):
    message.reply_text("Bot is alive.")

# ---------------- ADMINS LIST ----------------
@app.on_message(filters.command("admins") & filters.group)
async def list_admins(client, message):
    admins = []
    async for m in client.get_chat_members(
        message.chat.id,
        filter=ChatMembersFilter.ADMINISTRATORS
    ):
        if m.user:
            admins.append(m.user.mention)

    await message.reply_text("Admins:\n" + "\n".join(admins))

# ---------------- AUTO DELETE LINKS ----------------
LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

@app.on_message(filters.group & filters.text)
async def auto_delete_links(client, message):
    if LINK_DELETE_ENABLED.get(message.chat.id, True):
        if LINK_REGEX.search(message.text):
            await asyncio.sleep(5)
            try:
                await message.delete()
            except Exception:
                pass

# ---------------- SET RULES (FIXED) ----------------
@app.on_message(filters.command("setrules") & filters.group)
async def set_rules(client, message):
    if not await is_admin(client, message):
        return

    text = None

    # Case 1: reply-based
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption

    # Case 2: inline text
    if not text and len(message.command) > 1:
        text = message.text.split(None, 1)[1]

    if not text:
        await message.reply_text(
            "Usage:\nReply to a message with /setrules\nor\n/setrules <rules text>"
        )
        return

    RULES_TEXT[message.chat.id] = text
    await message.reply_text("Rules updated.")

# ---------------- SHOW RULES ----------------
@app.on_message(filters.command("rules") & filters.group)
async def show_rules(client, message):
    rules = RULES_TEXT.get(message.chat.id)
    if not rules:
        await message.reply_text("No rules set.")
        return
    await message.reply_text("Rules:\n" + rules)

# ---------------- SET WELCOME (FIXED) ----------------
@app.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome(client, message):
    if not await is_admin(client, message):
        return

    text = None

    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption

    if not text and len(message.command) > 1:
        text = message.text.split(None, 1)[1]

    if not text:
        await message.reply_text(
            "Usage:\nReply to a message with /setwelcome\nor\n/setwelcome <welcome text>"
        )
        return

    WELCOME_TEXT[message.chat.id] = text
    WELCOME_ENABLED[message.chat.id] = True
    await message.reply_text("Welcome message updated.")

# ---------------- TOGGLE WELCOME ----------------
@app.on_message(filters.command("welcome") & filters.group)
async def toggle_welcome(client, message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 2:
        await message.reply_text("Usage: /welcome on | off")
        return

    state = message.command[1].lower()
    WELCOME_ENABLED[message.chat.id] = state == "on"
    await message.reply_text(f"Welcome {'enabled' if state=='on' else 'disabled'}.")

# ---------------- WELCOME HANDLER ----------------
@app.on_message(filters.new_chat_members & filters.group)
async def welcome_new_members(client, message):
    if not WELCOME_ENABLED.get(message.chat.id):
        return

    template = WELCOME_TEXT.get(message.chat.id, "Welcome {mention}")
    for user in message.new_chat_members:
        text = template.replace("{mention}", user.mention)
        sent = await message.reply_text(text)
        await asyncio.sleep(WELCOME_DELETE_AFTER)
        try:
            await sent.delete()
        except Exception:
            pass

# ---------------- RUN ----------------
app.run()
