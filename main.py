import logging
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN

logging.basicConfig(level=logging.INFO)

app = Client(
    "phase_zero_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
def start_cmd(client, message):
    message.reply_text("Bot is alive. Phase 0 OK.")

app.run()
