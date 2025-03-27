import os
import logging
import asyncio
from telegram_client import main as start_telegram_bot

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Add file handler
logger = logging.getLogger(__name__)
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.FileHandler('logs/bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

async def run():
    try:
        logger.info("Starting Telegram bot...")
        await start_telegram_bot()
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")

if __name__ == "__main__":
    logger.info("Bot script started")
    asyncio.run(run())