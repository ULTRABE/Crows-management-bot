import asyncio
import logging
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "phase_zero_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("Bot is alive. Phase 0 OK.")

async def main():
    await app.start()
    logging.info("Bot started successfully (Phase 0)")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
