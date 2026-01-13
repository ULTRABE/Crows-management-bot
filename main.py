import os
import asyncio
import logging
from dotenv import load_dotenv

from pyrogram import Client, filters, idle
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.types import (
    ChatPermissions,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# ---------------- CORE SETUP ----------------
logging.basicConfig(level=logging.INFO)
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("MANAGER_BOT_TOKEN")

app = Client(
    name="nageshwar_manager",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
    workers=1
)

# ---------------- MEMORY ----------------
LINK_DELETE_ENABLED = {}
WELCOME_ENABLED = {}
WELCOME_DATA = {}
TAG_RUNNING = {}

WELCOME_DELETE_AFTER = 10

# ---------------- ADMIN CHECK ----------------
async def is_admin(client, message):
    try:
        m = await client.get_chat_member(message.chat.id, message.from_user.id)
        return m.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False

# ---------------- START ----------------
@app.on_message(filters.command("start"))
async def start(_, msg):
    text = (
        "𝗧𝗵𝗲 𝗧𝗵𝗿𝗲𝗲 𝗘𝘆𝗲𝗱 𝗥𝗮𝘃𝗲𝗻 𝗶𝘀 𝗔𝘄𝗮𝗸𝗲\n\n"
        "System Status: Active\n"
        "Access Level: Manager\n\n"
        "Use /help to view available controls."
    )
    await msg.reply_text(text)

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
    await message.reply_text(
        "𝗔𝗱𝗺𝗶𝗻 𝗥𝗼𝘀𝘁𝗲𝗿\n\n" + "\n".join(admins)
    )

# ---------------- PROMOTE / DEMOTE ----------------
@app.on_message(filters.command("promote") & filters.group & filters.reply)
async def promote(client, msg):
    if not await is_admin(client, msg):
        return
    await client.promote_chat_member(
        msg.chat.id,
        msg.reply_to_message.from_user.id,
        can_delete_messages=True,
        can_invite_users=True,
        can_restrict_members=True,
        can_pin_messages=True
    )
    await msg.reply_text("Rank Updated: Administrator")

@app.on_message(filters.command("demote") & filters.group & filters.reply)
async def demote(client, msg):
    if not await is_admin(client, msg):
        return
    await client.promote_chat_member(
        msg.chat.id,
        msg.reply_to_message.from_user.id,
        can_change_info=False,
        can_delete_messages=False,
        can_invite_users=False,
        can_pin_messages=False,
        can_restrict_members=False,
        can_promote_members=False
    )
    await msg.reply_text("Rank Updated: Member")

# ---------------- TAG ALL ----------------
@app.on_message(filters.command("tagall") & filters.group)
async def tag_all(client, message):
    if TAG_RUNNING.get(message.chat.id):
        return

    TAG_RUNNING[message.chat.id] = True
    text = "Summoning Members\n\n"

    async for m in client.get_chat_members(message.chat.id):
        if not TAG_RUNNING.get(message.chat.id):
            break

        u = m.user
        if not u or u.is_bot or not u.first_name:
            continue

        mention = f'<a href="tg://user?id={u.id}">{u.first_name}</a>\n'
        if len(text) + len(mention) > 350:
            await message.reply_text(text, parse_mode="html")
            text = ""
            await asyncio.sleep(2)

        text += mention

    if text:
        await message.reply_text(text, parse_mode="html")

    TAG_RUNNING.pop(message.chat.id, None)

@app.on_message(filters.command("endtag") & filters.group)
async def end_tag(_, msg):
    TAG_RUNNING.pop(msg.chat.id, None)
    await msg.reply_text("Tag Process Terminated")

# ---------------- PURGE ----------------
@app.on_message(filters.command("purge") & filters.group & filters.reply)
async def purge(client, msg):
    for i in range(msg.reply_to_message.id, msg.id):
        try:
            await client.delete_messages(msg.chat.id, i)
        except Exception:
            pass
    await msg.delete()

# ---------------- LOCK / UNLOCK ----------------
@app.on_message(filters.command("lock") & filters.group)
async def lock(client, msg):
    if not await is_admin(client, msg):
        return
    await client.set_chat_permissions(msg.chat.id, ChatPermissions())
    await msg.reply_text("Chat Status: Locked")

@app.on_message(filters.command("unlock") & filters.group)
async def unlock(client, msg):
    if not await is_admin(client, msg):
        return
    await client.set_chat_permissions(
        msg.chat.id,
        ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    await msg.reply_text("Chat Status: Unlocked")

# ---------------- LINKS ----------------
@app.on_message(filters.command("links") & filters.group)
async def toggle_links(client, message):
    if not await is_admin(client, message):
        return
    if len(message.command) < 2:
        return await message.reply_text("Usage: /links on | off")

    LINK_DELETE_ENABLED[message.chat.id] = message.command[1].lower() == "on"
    await message.reply_text("Link Control Updated")

@app.on_message(filters.group & filters.text & ~filters.regex(r"^/"))
async def link_delete_handler(_, message):
    if not LINK_DELETE_ENABLED.get(message.chat.id, True):
        return

    entities = message.entities or []
    if not any(e.type in ("url", "text_link") for e in entities):
        return

    await asyncio.sleep(5)
    try:
        await message.delete()
    except Exception:
        pass

# ---------------- WELCOME ----------------
@app.on_message(filters.command("welcome") & filters.group)
async def toggle_welcome(client, message):
    if not await is_admin(client, message):
        return
    if len(message.command) < 2:
        return await message.reply_text("Usage: /welcome on | off")

    WELCOME_ENABLED[message.chat.id] = message.command[1].lower() == "on"
    await message.reply_text("Welcome Protocol Updated")

@app.on_message(filters.new_chat_members & filters.group)
async def welcome_new(client, message):
    if not WELCOME_ENABLED.get(message.chat.id):
        return

    for user in message.new_chat_members:
        text = (
            f"𝗔𝗰𝗰𝗲𝘀𝘀 𝗚𝗿𝗮𝗻𝘁𝗲𝗱\n\n"
            f"{user.mention}\n"
            "Observe. Learn. Act."
        )
        sent = await message.reply_text(text)
        await asyncio.sleep(WELCOME_DELETE_AFTER)
        await sent.delete()

# ---------------- HELP ----------------
HELP_TEXT = {
    "main": "𝗖𝗼𝗻𝘁𝗿𝗼𝗹 𝗣𝗮𝗻𝗲𝗹\nSelect Module:",
    "moderation": "/lock\n/unlock\n/slowmode\n/purge\n/del",
    "admin": "/promote\n/demote\n/admins",
    "utils": "/tagall\n/endtag\n/stats\n/links\n/welcome",
}

def help_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Moderation", callback_data="help_moderation"),
            InlineKeyboardButton("Administration", callback_data="help_admin")
        ],
        [InlineKeyboardButton("Utilities", callback_data="help_utils")],
        [InlineKeyboardButton("Back", callback_data="help_main")]
    ])

@app.on_message(filters.command("help") & filters.group)
async def help_cmd(_, msg):
    await msg.reply_text(HELP_TEXT["main"], reply_markup=help_kb())

@app.on_callback_query(filters.regex("^help_"))
async def help_cb(_, q):
    key = q.data.replace("help_", "")
    await q.message.edit_text(
        HELP_TEXT.get(key, HELP_TEXT["main"]),
        reply_markup=help_kb()
    )
    await q.answer()

# ---------------- RUN ----------------
if __name__ == "__main__":
    logging.info("Nageshwar Manager | System Online")
    app.start()
    idle()
    app.stop()
