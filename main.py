import logging
import asyncio
from pyrogram import Client, filters
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
WELCOME_DATA = {}
RULES_TEXT = {}

WAITING_FOR_RULES = set()
WAITING_FOR_WELCOME = set()

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

# =================================================
# CONFIG + CONTENT PIPELINE (NO COMMANDS HERE)
# =================================================
@app.on_message(
    filters.group
    & (filters.text | filters.photo | filters.video)
    & ~filters.command
)
async def content_pipeline(client, message):
    chat_id = message.chat.id

    # ---------- RULES CAPTURE ----------
    if chat_id in WAITING_FOR_RULES and await is_admin(client, message):
        if message.text:
            RULES_TEXT[chat_id] = message.text
            WAITING_FOR_RULES.remove(chat_id)
            await message.reply_text("Rules saved.")
        return

    # ---------- WELCOME CAPTURE ----------
    if chat_id in WAITING_FOR_WELCOME and await is_admin(client, message):
        if message.text:
            data = {
                "type": "text",
                "text": message.text
            }
        elif message.photo:
            data = {
                "type": "photo",
                "file_id": message.photo.file_id,
                "text": message.caption or ""
            }
        elif message.video:
            data = {
                "type": "video",
                "file_id": message.video.file_id,
                "text": message.caption or ""
            }
        else:
            await message.reply_text("Unsupported welcome type.")
            return

        WELCOME_DATA[chat_id] = data
        WELCOME_ENABLED[chat_id] = True
        WAITING_FOR_WELCOME.remove(chat_id)

        await message.reply_text("Welcome message saved.")
        return

# =================================================
# LINK DELETE — ENTITY BASED, PURE TEXT ONLY
# =================================================
@app.on_message(filters.group & filters.text & ~filters.command)
async def link_delete_handler(client, message):
    chat_id = message.chat.id

    # Skip media & config mode
    if message.media:
        return
    if chat_id in WAITING_FOR_RULES or chat_id in WAITING_FOR_WELCOME:
        return
    if not LINK_DELETE_ENABLED.get(chat_id, True):
        return

    entities = message.entities or []
    has_url = any(e.type in ("url", "text_link") for e in entities)

    if not has_url:
        return

    await asyncio.sleep(5)
    try:
        await message.delete()
    except Exception:
        pass

# ---------------- LINKS TOGGLE ----------------
@app.on_message(filters.command("links") & filters.group)
async def links_toggle(client, message):
    if not await is_admin(client, message):
        return
    if len(message.command) < 2:
        await message.reply_text("Usage: /links on | off")
        return
    LINK_DELETE_ENABLED[message.chat.id] = message.command[1].lower() == "on"
    await message.reply_text("Link setting updated.")

# ---------------- SET RULES ----------------
@app.on_message(filters.command("setrules") & filters.group)
async def set_rules(client, message):
    if not await is_admin(client, message):
        return
    WAITING_FOR_RULES.add(message.chat.id)
    WAITING_FOR_WELCOME.discard(message.chat.id)
    await message.reply_text("Send the rules message now.")

# ---------------- SHOW RULES ----------------
@app.on_message(filters.command("rules") & filters.group)
async def show_rules(client, message):
    rules = RULES_TEXT.get(message.chat.id)
    if not rules:
        await message.reply_text("No rules set.")
        return
    await message.reply_text("Rules:\n" + rules)

# ---------------- SET WELCOME ----------------
@app.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome(client, message):
    if not await is_admin(client, message):
        return
    WAITING_FOR_WELCOME.add(message.chat.id)
    WAITING_FOR_RULES.discard(message.chat.id)
    await message.reply_text("Send the welcome message now.")

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
    chat_id = message.chat.id
    if not WELCOME_ENABLED.get(chat_id):
        return
    data = WELCOME_DATA.get(chat_id)
    if not data:
        return

    for user in message.new_chat_members:
        text = data.get("text", "").replace("{mention}", user.mention)
        try:
            if data["type"] == "text":
                sent = await message.reply_text(text)
            elif data["type"] == "photo":
                sent = await message.reply_photo(
                    photo=data["file_id"], caption=text or None
                )
            elif data["type"] == "video":
                sent = await message.reply_video(
                    video=data["file_id"], caption=text or None
                )
            await asyncio.sleep(WELCOME_DELETE_AFTER)
            await sent.delete()
        except Exception:
            pass

# ---------------- RUN ----------------
app.run()
