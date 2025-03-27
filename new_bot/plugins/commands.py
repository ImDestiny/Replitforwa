import re
import time
import asyncio
import logging
from database import db
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# State management for forward process
FORWARD_STATE = {}

@Client.on_message(filters.command(["start"]) & ~filters.bot)
async def start(client, message):
    """Bot start command handler"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Check if user exists, add if not
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, user_name)
    
    # Get bot username
    bot_username = (await client.get_me()).username
    
    # Create start menu
    buttons = [
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 Status", callback_data="status")
        ]
    ]
    
    await message.reply_text(
        Translation.START_TXT.format(user_name, "👋"),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["help"]) & ~filters.bot)
async def help_command(client, message):
    """Bot help command handler"""
    buttons = [
        [
            InlineKeyboardButton("🔄 How to Use", callback_data="how_to_use"),
            InlineKeyboardButton("◀️ Back", callback_data="start")
        ]
    ]
    
    await message.reply_text(
        Translation.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["about"]) & ~filters.bot)
async def about_command(client, message):
    """Bot about command handler"""
    await message.reply_text(
        Translation.ABOUT_TXT,
        disable_web_page_preview=True
    )

@Client.on_message(filters.command(["status"]) & ~filters.bot)
async def status_command(client, message):
    """Bot status command handler"""
    user_count, bot_count = await db.total_users_bots_count()
    channel_count = await db.total_channels()
    
    await message.reply_text(
        Translation.STATUS_TXT.format(user_count, bot_count, channel_count)
    )

@Client.on_message(filters.command(["forward"]) & ~filters.bot)
async def forward_command(client, message):
    """Forward command handler to start a new forwarding task"""
    user_id = message.from_user.id
    
    # Check if user has a bot
    user_bot = await db.get_bot(user_id)
    if not user_bot:
        buttons = [[InlineKeyboardButton("⚙️ Settings", callback_data="settings_bot")]]
        return await message.reply_text(
            "<b>❌ No Bot Added</b>\n\nYou need to add a bot first to use forwarding.\nGo to Settings > Bot Settings to add a bot.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Check if user is already forwarding
    active_tasks = await db.get_user_active_tasks(user_id)
    if active_tasks and any(task.get("status") == "active" for task in active_tasks):
        buttons = [
            [InlineKeyboardButton("✅ View Tasks", callback_data="view_tasks")],
            [InlineKeyboardButton("🔄 Continue Anyway", callback_data="forward_start")]
        ]
        return await message.reply_text(
            "<b>⚠️ Active Forwarding</b>\n\nYou already have active forwarding tasks. Do you want to view them or start a new forwarding task?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Start forward process
    FORWARD_STATE[user_id] = {"step": "source"}
    await message.reply_text(Translation.FROM_MSG)

@Client.on_message(filters.command(["tasks"]) & ~filters.bot)
async def tasks_command(client, message):
    """View and manage forwarding tasks"""
    user_id = message.from_user.id
    tasks = await db.get_user_active_tasks(user_id)
    
    if not tasks or len(tasks) == 0:
        return await message.reply_text(Translation.NO_TASKS)
    
    text = "<b>Your Active Forwarding Tasks:</b>\n\n"
    buttons = []
    
    for task in tasks:
        task_id = task.get("task_id")
        created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.get("created_at", 0)))
        from_chat = task.get("from_chat")
        to_chat = task.get("to_chat")
        status = task.get("status", "unknown")
        
        text += Translation.TASK_DETAILS.format(
            task_id,
            from_chat,
            to_chat,
            task.get("last_forwarded_msg_id", 0),
            task.get("total_count", 0),
            status,
            created_time
        )
        
        if status in ["active", "paused", "failed"]:
            buttons.append([InlineKeyboardButton(
                f"Resume {task_id[-4:]}", 
                callback_data=f"resume_task_{task_id}"
            )])
    
    if buttons:
        buttons.append([InlineKeyboardButton("Close", callback_data="close_btn")])
        return await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        return await message.reply_text(text)

@Client.on_message(filters.command(["cancel"]) & ~filters.bot)
async def cancel_command(client, message):
    """Cancel the current operation"""
    user_id = message.from_user.id
    
    if user_id in FORWARD_STATE:
        del FORWARD_STATE[user_id]
        await message.reply_text(Translation.CANCEL)
    elif user_id in temp.CANCEL:
        temp.CANCEL[user_id] = True
        await message.reply_text("<b>Forwarding will be cancelled after current batch completes.</b>")
    else:
        await message.reply_text("<b>No active process to cancel.</b>")

@Client.on_callback_query(filters.regex(r'^help$'))
async def help_callback(bot, query):
    """Help button callback handler"""
    buttons = [
        [
            InlineKeyboardButton("🔄 How to Use", callback_data="how_to_use"),
            InlineKeyboardButton("◀️ Back", callback_data="start")
        ]
    ]
    
    await query.message.edit_text(
        Translation.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex(r'^how_to_use$'))
async def how_to_use(bot, query):
    """How to use button callback handler"""
    buttons = [
        [InlineKeyboardButton("◀️ Back", callback_data="help")]
    ]
    
    await query.message.edit_text(
        Translation.HOW_USE_TXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex(r'^about$'))
async def about(bot, query):
    """About button callback handler"""
    buttons = [
        [InlineKeyboardButton("◀️ Back", callback_data="start")]
    ]
    
    await query.message.edit_text(
        Translation.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )
    await query.answer()

@Client.on_callback_query(filters.regex(r'^status$'))
async def status(bot, query):
    """Status button callback handler"""
    user_count, bot_count = await db.total_users_bots_count()
    channel_count = await db.total_channels()
    
    buttons = [
        [InlineKeyboardButton("◀️ Back", callback_data="start")]
    ]
    
    await query.message.edit_text(
        Translation.STATUS_TXT.format(user_count, bot_count, channel_count),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex(r'^start$'))
async def back(bot, query):
    """Back to start button callback handler"""
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    buttons = [
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 Status", callback_data="status")
        ]
    ]
    
    await query.message.edit_text(
        Translation.START_TXT.format(user_name, "👋"),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    """Close button callback handler"""
    await update.answer()
    await update.message.delete()