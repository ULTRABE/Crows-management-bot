import logging
import asyncio
import re
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
WELCOME_TEXT = {}
RULES_TEXT = {}

# STATE
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

# ---------------- LINKS ----------------
LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

@app.on_message(filters.group & filters.text & ~filters.command)
async def link_and_state_handler(client, message):
    chat_id = message.chat.id

    # ---------- STATE: RULES ----------
    if chat_id in WAITING_FOR_RULES and await is_admin(client, message):
        RULES_TEXT[chat_id] = message.text
        WAITING_FOR_RULES.remove(chat_id)
        await message.reply_text("Rules saved.")
        return

    # ---------- STATE: WELCOME ----------
    if chat_id in WAITING_FOR_WELCOME and await is_admin(client, message):
        WELCOME_TEXT[chat_id] = message.text
        WELCOME_ENABLED[chat_id] = True
        WAITING_FOR_WELCOME.remove(chat_id)
        await message.reply_text("Welcome message saved.")
        return

    # ---------- LINK DELETE ----------
    if LINK_DELETE_ENABLED.get(chat_id, True):
        if LINK_REGEX.search(message.text):
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
    if not WELCOME_ENABLED.get(message.chat.id):
        return
    template = WELCOME_TEXT.get(message.chat.id, "Welcome {mention}")
    for user in message.new_chat_members:
        sent = await message.reply_text(
            template.replace("{mention}", user.mention)
        )
        await asyncio.sleep(WELCOME_DELETE_AFTER)
        try:
            await sent.delete()
        except Exception:
            pass

# ---------------- RUN ----------------
app.run()
