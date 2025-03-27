# Advanced Telegram Forwarder Bot
# Improved by Replit AI - PostgreSQL Version

import os
import asyncio
import logging
from pyrogram import Client, idle
from .database import db, mongodb_version
from .config import Config, temp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create the bot instance
bot = Client(
    Config.BOT_SESSION,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="new_bot/plugins")
)

# Import plugins here to avoid circular imports
from .plugins import commands, regix, settings, utils

async def main():
    """Main entry point for the bot"""
    os.makedirs("logs", exist_ok=True)
    os.makedirs("sessions", exist_ok=True)
    
    # Connect to the database
    try:
        await db.connect()
        db_version = await mongodb_version()
        logger.info(f"Connected to PostgreSQL database: {db_version}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return
    
    try:
        # Start the bot
        await bot.start()
        info = await bot.get_me()
        logger.info(f"Starting bot - {info.first_name} (@{info.username})")
        logger.info("Bot started successfully!")
        logger.info("--------------------------------------")
        
        # Get all active forwarding tasks and update them to "paused" status
        # This ensures we don't leave tasks in a state where they can't be resumed
        active_tasks = await db.get_user_active_tasks(0)  # Get all active tasks
        for task in active_tasks:
            if task.get("status") == "active":
                await db.update_task_status(task["task_id"], "paused")
                logger.info(f"Set task {task['task_id']} to paused state for resuming")
                
        # Start idle to keep the bot running
        await idle()
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Properly clean up when stopping
        # Update any remaining active tasks to paused
        try:
            active_tasks = await db.get_user_active_tasks(0)  # Get all active tasks
            for task in active_tasks:
                if task.get("status") == "active":
                    await db.update_task_status(task["task_id"], "paused")
        except Exception as e:
            logger.error(f"Error updating tasks during shutdown: {e}")
                
        if bot.is_connected:
            await bot.stop()
            logger.info("Bot stopped")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())