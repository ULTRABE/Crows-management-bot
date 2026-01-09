import logging
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from config import API_ID, API_HASH, BOT_TOKEN

logging.basicConfig(level=logging.INFO)

app = Client(
    "crow_manager_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- STORAGE ----------------
LINK_DELETE_ENABLED = {}
WELCOME_ENABLED = {}
WELCOME_TEXT = {}
RULES_TEXT = {}

WELCOME_DELETE_AFTER = 10

# ---------------- ADMIN CHECK ----------------
async def is_admin(client, message):
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

# ---------------- ADMINS ----------------
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

# ---------------- LINK DELETE ----------------
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

# ---------------- SET RULES ----------------
@app.on_message(
    (filters.command("setrules") | filters.command(["set", "rules"])) & filters.group
)
async def set_rules(client, message):
    if not await is_admin(client, message):
        return

    text = None

    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption

    if not text and len(message.command) > 1:
        text = message.text.split(None, 1)[1]

    if not text:
        await message.reply_text(
            "Usage:\n/setrules <text>\nor reply to a message with /setrules"
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

# ---------------- SET WELCOME ----------------
@app.on_message(
    (filters.command("setwelcome") | filters.command(["set", "welcome"])) & filters.group
)
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
            "Usage:\n/setwelcome <text>\nor reply to a message with /setwelcome"
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

    WELCOME_ENABLED[message.chat.id] = message.command[1].lower() == "on"
    await message.reply_text("Welcome updated.")

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
