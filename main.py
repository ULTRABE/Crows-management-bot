import logging
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

# ---------------- ADMIN CHECK (FIXED) ----------------
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

# ---------------- START COMMAND ----------------
@app.on_message(filters.command("start"))
def start_cmd(client, message: Message):
    message.reply_text("Bot is alive. Phase 0 OK.")

# ---------------- ADMIN TEST COMMAND ----------------
@app.on_message(filters.command("admin") & filters.group)
async def admin_test_cmd(client, message: Message):
    if await is_admin(client, message):
        await message.reply_text("You are admin.")
    else:
        await message.reply_text("You are not admin.")

# ---------------- RUN ----------------
app.run()
