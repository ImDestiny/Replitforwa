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

# State management for multi-step workflows
USER_STATE = {}
FILTERS = ['text', 'audio', 'document', 'photo', 'video', 'animation', 'voice', 'sticker', 'poll']

@Client.on_message(filters.command(["settings"]) & ~filters.bot)
async def settings(client, message):
    """Settings menu command handler"""
    user_id = message.from_user.id
    
    # Check if user exists
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    
    # Create settings menu
    buttons = main_buttons()
    await message.reply_text(
        "<b>⚙️ Bot Settings</b>\n\nConfigure your forwarding settings here.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
    """Handle settings menu interactions"""
    user_id = query.from_user.id
    data = query.data.split("_")
    
    # Main menu
    if len(data) == 1:
        buttons = main_buttons()
        await query.message.edit_text(
            "<b>⚙️ Bot Settings</b>\n\nConfigure your forwarding settings here.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await query.answer()
        return
    
    # Bot settings
    if data[1] == "bot":
        # Check if user has any bots
        user_bot = await db.get_bot(user_id)
        if not user_bot:
            buttons = [
                [InlineKeyboardButton("➕ Add Bot", callback_data="settings_add_bot")],
                [InlineKeyboardButton("◀️ Back", callback_data="settings")]
            ]
            await query.message.edit_text(
                "<b>🤖 Bot Settings</b>\n\nYou haven't added any bots yet.\nAdd a bot to start forwarding messages.",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            # Display bot information
            name = user_bot.get("name", "Unknown")
            username = user_bot.get("username", "Unknown")
            bot_id = user_bot.get("bot_id", "Unknown")
            
            buttons = [
                [InlineKeyboardButton("🔄 Change Bot", callback_data="settings_add_bot")],
                [InlineKeyboardButton("🗑️ Remove Bot", callback_data="settings_remove_bot")],
                [InlineKeyboardButton("◀️ Back", callback_data="settings")]
            ]
            
            await query.message.edit_text(
                Translation.BOT_DETAILS.format(name, bot_id, username),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    
    # Filter settings
    elif data[1] == "filter":
        user_filters = await db.get_filters(user_id)
        buttons = await filters_buttons(user_id)
        
        await query.message.edit_text(
            "<b>🔍 Filter Settings</b>\n\nChoose which types of messages to forward:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Caption settings
    elif data[1] == "caption":
        configs = await db.get_configs(user_id)
        caption = configs.get('caption', None)
        
        buttons = [
            [InlineKeyboardButton("✏️ Change Caption", callback_data="settings_set_caption")],
            [InlineKeyboardButton("❌ Remove Caption", callback_data="settings_clear_caption")],
            [InlineKeyboardButton("◀️ Back", callback_data="settings")]
        ]
        
        await query.message.edit_text(
            f"<b>📝 Caption Settings</b>\n\nCurrent Caption:\n<code>{caption or 'None'}</code>\n\nYou can use format variables:\n<code>{'{filename}'}</code> - File name\n<code>{'{size}'}</code> - File size\n<code>{'{caption}'}</code> - Original caption",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Toggle a specific filter
    elif data[1] == "toggle" and len(data) > 2:
        filter_type = data[2]
        if filter_type in FILTERS:
            user_filters = await db.get_filters(user_id)
            user_filters[filter_type] = not user_filters.get(filter_type, True)
            await db.update_filter(user_id, user_filters)
            
            buttons = await filters_buttons(user_id)
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
    
    # Add bot process
    elif data[1] == "add_bot":
        USER_STATE[user_id] = {"state": "waiting_bot_token"}
        
        buttons = [[InlineKeyboardButton("❌ Cancel", callback_data="settings_cancel")]]
        await query.message.edit_text(
            "<b>🤖 Add Bot</b>\n\nPlease send me your bot token from @BotFather.\n\nFormat: <code>123456789:ABCdefGhIJklmNoPQRstUVwxyZ</code>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Remove bot confirmation
    elif data[1] == "remove_bot":
        buttons = [
            [
                InlineKeyboardButton("✅ Yes", callback_data="settings_confirm_remove_bot"),
                InlineKeyboardButton("❌ No", callback_data="settings_bot")
            ]
        ]
        
        await query.message.edit_text(
            "<b>⚠️ Remove Bot</b>\n\nAre you sure you want to remove this bot?\nAll forwarding tasks using this bot will be stopped.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Confirm bot removal
    elif data[1] == "confirm_remove_bot":
        await db.remove_bot(user_id)
        
        buttons = [[InlineKeyboardButton("◀️ Back", callback_data="settings")]]
        await query.message.edit_text(
            "<b>✅ Bot Removed</b>\n\nYour bot has been removed successfully.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Set caption
    elif data[1] == "set_caption":
        USER_STATE[user_id] = {"state": "waiting_caption"}
        
        buttons = [[InlineKeyboardButton("❌ Cancel", callback_data="settings_caption")]]
        await query.message.edit_text(
            "<b>📝 Set Caption</b>\n\nPlease send me the caption you want to use for forwarded messages.\n\nYou can use format variables:\n<code>{filename}</code> - File name\n<code>{size}</code> - File size\n<code>{caption}</code> - Original caption",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Clear caption
    elif data[1] == "clear_caption":
        configs = await db.get_configs(user_id)
        configs['caption'] = None
        await db.update_configs(user_id, configs)
        
        buttons = [[InlineKeyboardButton("◀️ Back", callback_data="settings_caption")]]
        await query.message.edit_text(
            "<b>✅ Caption Cleared</b>\n\nYour caption has been cleared successfully.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Cancel any settings operation
    elif data[1] == "cancel":
        if user_id in USER_STATE:
            del USER_STATE[user_id]
        
        buttons = main_buttons()
        await query.message.edit_text(
            "<b>⚙️ Bot Settings</b>\n\nConfigure your forwarding settings here.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    await query.answer()

@Client.on_message(filters.private & ~filters.command())
async def handle_settings_input(client, message):
    """Handle user input for settings"""
    user_id = message.from_user.id
    
    if user_id not in USER_STATE:
        return
    
    state = USER_STATE[user_id]["state"]
    
    # Handle bot token input
    if state == "waiting_bot_token":
        token = message.text.strip()
        
        # Validate bot token format
        if not re.match(r'^\d+:[\w-]+$', token):
            await message.reply_text(
                "<b>❌ Invalid Bot Token</b>\n\nPlease send a valid bot token from @BotFather.\n\nFormat: <code>123456789:ABCdefGhIJklmNoPQRstUVwxyZ</code>"
            )
            return
        
        # Try to get bot info using the token
        try:
            bot = Client(
                "temp_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=token,
                in_memory=True
            )
            
            await bot.start()
            bot_info = await bot.get_me()
            await bot.stop()
            
            # Save bot details
            bot_data = {
                "user_id": user_id,
                "bot_id": bot_info.id,
                "name": bot_info.first_name,
                "username": bot_info.username,
                "token": token,
                "is_bot": True
            }
            
            await db.add_bot(bot_data)
            del USER_STATE[user_id]
            
            # Show success message
            buttons = [[InlineKeyboardButton("◀️ Back to Settings", callback_data="settings")]]
            await message.reply_text(
                f"<b>✅ Bot Added Successfully</b>\n\n<b>Name:</b> {bot_info.first_name}\n<b>Username:</b> @{bot_info.username}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            
        except Exception as e:
            logger.error(f"Error adding bot: {e}")
            await message.reply_text(
                f"<b>❌ Error Adding Bot</b>\n\nThere was an error adding your bot: {str(e)}\nPlease check the token and try again."
            )
    
    # Handle caption input
    elif state == "waiting_caption":
        caption = message.text
        
        # Save caption
        configs = await db.get_configs(user_id)
        configs['caption'] = caption
        await db.update_configs(user_id, configs)
        
        del USER_STATE[user_id]
        
        # Show success message
        buttons = [[InlineKeyboardButton("◀️ Back to Settings", callback_data="settings_caption")]]
        await message.reply_text(
            "<b>✅ Caption Saved</b>\n\nYour caption has been saved successfully.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

def main_buttons():
    """Create main settings menu buttons"""
    return [
        [InlineKeyboardButton("🤖 Bot Settings", callback_data="settings_bot")],
        [InlineKeyboardButton("🔍 Filter Settings", callback_data="settings_filter")],
        [InlineKeyboardButton("📝 Caption Settings", callback_data="settings_caption")]
    ]

async def filters_buttons(user_id):
    """Create filter settings buttons"""
    user_filters = await db.get_filters(user_id)
    buttons = []
    
    for filter_type in FILTERS:
        status = user_filters.get(filter_type, True)
        icon = "✅" if status else "❌"
        button_text = f"{icon} {filter_type.capitalize()}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"settings_toggle_{filter_type}")])
    
    buttons.append([InlineKeyboardButton("◀️ Back", callback_data="settings")])
    return buttons