import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from bot_manager import BotManager
from storage import Storage

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables
bot_manager = BotManager()
storage = Storage()
user_states = {}  # To keep track of user states in the conversation

# State constants
STATE_INITIAL = 0
STATE_AWAITING_API_ID = 1
STATE_AWAITING_API_HASH = 2
STATE_AWAITING_PHONE = 3
STATE_AWAITING_CODE = 4
STATE_AWAITING_SOURCE = 5
STATE_AWAITING_DESTINATION = 6
STATE_AWAITING_LAST_MESSAGE = 7
STATE_SELECTING_SOURCE = 8
STATE_SELECTING_DESTINATION = 9

# Session storage for users
sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    user_states[user_id] = STATE_INITIAL

    # Create main menu keyboard
    keyboard = [
        [
            InlineKeyboardButton("🤖 Login", callback_data="login"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("👤 About", callback_data="about")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to Telegram Forwarder Bot!\n\n"
        "This bot helps you forward messages from source channels to destination channels with resume capability.\n\n"
        "Please select an option:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "📚 *Bot Commands*\n\n"
        "/start - Start the bot and show main menu\n"
        "/help - Show this help message\n"
        "/login - Login with your Telegram API credentials\n"
        "/sources - Manage your source channels\n"
        "/destinations - Manage your destination channels\n"
        "/forward - Start forwarding messages\n"
        "/status - Check forwarding status\n"
        "/cancel - Cancel active forwarding task\n"
        "/logout - Logout from the bot\n\n"
        
        "📋 *How to use*\n\n"
        "1. Login with your Telegram API credentials\n"
        "2. Add source and destination channels\n"
        "3. Start forwarding with optional last message link\n"
        "4. Monitor progress and cancel if needed\n\n"
        
        "⚠️ *Important*\n"
        "• Use this bot responsibly\n"
        "• Excessive forwarding may trigger Telegram's anti-spam measures\n"
        "• The bot forwards at a rate of 1 message every 3 seconds (20 messages per minute)\n"
        "• If rate-limited, the bot will wait and resume forwarding automatically"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message about the bot."""
    about_text = (
        "🤖 *Telegram Forwarder Bot*\n"
        "Version 1.0.0\n\n"
        
        "A powerful bot to forward messages from source channels to destination channels.\n\n"
        
        "*Features*\n"
        "• Forward messages from source channels/groups to destination channels/groups\n"
        "• Support for restricted channels and groups\n"
        "• Resume forwarding if interrupted\n"
        "• Forward from a specific message onwards\n"
        "• Cancel forwarding process at any time\n\n"
        
        "Stay connected, forward with ease!"
    )
    
    await update.message.reply_text(about_text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "login":
        user_states[user_id] = STATE_AWAITING_API_ID
        await query.edit_message_text(
            "Please enter your API ID from my.telegram.org/apps\n\n"
            "Send /cancel to cancel the login process."
        )
    
    elif data == "help":
        help_text = (
            "📚 *Bot Commands*\n\n"
            "/start - Start the bot and show main menu\n"
            "/help - Show this help message\n"
            "/login - Login with your Telegram API credentials\n"
            "/sources - Manage your source channels\n"
            "/destinations - Manage your destination channels\n"
            "/forward - Start forwarding messages\n"
            "/status - Check forwarding status\n"
            "/cancel - Cancel active forwarding task\n"
            "/logout - Logout from the bot\n\n"
            
            "📋 *How to use*\n\n"
            "1. Login with your Telegram API credentials\n"
            "2. Add source and destination channels\n"
            "3. Start forwarding with optional last message link\n"
            "4. Monitor progress and cancel if needed\n\n"
            
            "⚠️ *Important*\n"
            "• Use this bot responsibly\n"
            "• Excessive forwarding may trigger Telegram's anti-spam measures\n"
            "• The bot forwards at a rate of 1 message every 3 seconds (20 messages per minute)\n"
            "• If rate-limited, the bot will wait and resume forwarding automatically"
        )
        
        await query.edit_message_text(help_text, parse_mode="Markdown")
    
    elif data == "about":
        about_text = (
            "🤖 *Telegram Forwarder Bot*\n"
            "Version 1.0.0\n\n"
            
            "A powerful bot to forward messages from source channels to destination channels.\n\n"
            
            "*Features*\n"
            "• Forward messages from source channels/groups to destination channels/groups\n"
            "• Support for restricted channels and groups\n"
            "• Resume forwarding if interrupted\n"
            "• Forward from a specific message onwards\n"
            "• Cancel forwarding process at any time\n\n"
            
            "Stay connected, forward with ease!"
        )
        
        await query.edit_message_text(about_text, parse_mode="Markdown")
    
    elif data == "add_source":
        user_states[user_id] = STATE_AWAITING_SOURCE
        await query.edit_message_text(
            "Please enter the source channel/group link or username\n\n"
            "Examples:\n"
            "• Public channel: @channelname or https://t.me/channelname\n"
            "• Private channel: https://t.me/joinchat/XXXXXXXXXXXX\n\n"
            "Send /cancel to cancel."
        )

    elif data == "add_destination":
        user_states[user_id] = STATE_AWAITING_DESTINATION
        await query.edit_message_text(
            "Please enter the destination channel/group link or username\n\n"
            "Examples:\n"
            "• Public channel: @channelname or https://t.me/channelname\n"
            "• Private channel: https://t.me/joinchat/XXXXXXXXXXXX\n\n"
            "Send /cancel to cancel."
        )

    elif data == "back_to_main":
        await show_main_menu(query)

    elif data == "sources_menu":
        await show_sources_menu(user_id, query)

    elif data == "destinations_menu":
        await show_destinations_menu(user_id, query)

    elif data == "start_forwarding":
        await show_forwarding_menu(user_id, query)

    elif data == "cancel_forwarding":
        phone = sessions.get(user_id, {}).get('phone')
        if phone:
            try:
                result = bot_manager.cancel_forwarding(phone)
                if result.get('success'):
                    await query.edit_message_text(
                        "✅ Forwarding has been cancelled successfully.",
                        reply_markup=create_back_to_main_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Error cancelling forwarding: {result.get('error', 'Unknown error')}",
                        reply_markup=create_back_to_main_keyboard()
                    )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Error: {str(e)}",
                    reply_markup=create_back_to_main_keyboard()
                )
        else:
            await query.edit_message_text(
                "❌ You are not logged in. Please login first.",
                reply_markup=create_back_to_main_keyboard()
            )

    elif data.startswith("select_source:"):
        source_id = data.split(":")[1]
        sessions[user_id]['selected_source_id'] = source_id
        user_states[user_id] = STATE_SELECTING_SOURCE
        
        # Now ask for destination
        await show_destinations_for_forwarding(user_id, query)

    elif data.startswith("select_destination:"):
        if user_states.get(user_id) == STATE_SELECTING_SOURCE:
            destination_id = data.split(":")[1]
            source_id = sessions[user_id].get('selected_source_id')
            
            if source_id and destination_id:
                # Ask if user wants to set last message
                keyboard = [
                    [
                        InlineKeyboardButton("Yes", callback_data=f"set_last_message:{source_id}:{destination_id}"),
                        InlineKeyboardButton("No", callback_data=f"forward_now:{source_id}:{destination_id}")
                    ],
                    [InlineKeyboardButton("« Back", callback_data="start_forwarding")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "Do you want to set a last message link? This will forward all messages from the beginning up to this message.",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    "❌ Error: Source or destination not selected properly.",
                    reply_markup=create_back_to_main_keyboard()
                )

    elif data.startswith("set_last_message:"):
        parts = data.split(":")
        source_id = parts[1]
        destination_id = parts[2]
        
        sessions[user_id]['selected_source_id'] = source_id
        sessions[user_id]['selected_destination_id'] = destination_id
        user_states[user_id] = STATE_AWAITING_LAST_MESSAGE
        
        await query.edit_message_text(
            "Please enter the last message link from the source channel.\n\n"
            "Format: https://t.me/c/1234567890/123\n\n"
            "Send /cancel to cancel."
        )

    elif data.startswith("forward_now:"):
        parts = data.split(":")
        source_id = parts[1]
        destination_id = parts[2]
        
        phone = sessions.get(user_id, {}).get('phone')
        if phone:
            # Start forwarding in async task
            asyncio.create_task(
                async_forward_messages(query, phone, source_id, destination_id)
            )
            
            await query.edit_message_text(
                "✅ Forwarding task has been started!\n\n"
                "You can check the status or cancel the task from the main menu.",
                reply_markup=create_back_to_main_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ You are not logged in. Please login first.",
                reply_markup=create_back_to_main_keyboard()
            )
            
    elif data.startswith("delete_source:"):
        source_id = data.split(":")[1]
        phone = sessions.get(user_id, {}).get('phone')
        
        if phone:
            try:
                result = bot_manager.delete_source(phone, source_id)
                if result.get('success'):
                    await query.edit_message_text(
                        "✅ Source deleted successfully.",
                        reply_markup=create_back_button("sources_menu")
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Error deleting source: {result.get('error', 'Unknown error')}",
                        reply_markup=create_back_button("sources_menu")
                    )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Error: {str(e)}",
                    reply_markup=create_back_button("sources_menu")
                )
        else:
            await query.edit_message_text(
                "❌ You are not logged in. Please login first.",
                reply_markup=create_back_to_main_keyboard()
            )
            
    elif data.startswith("delete_destination:"):
        destination_id = data.split(":")[1]
        phone = sessions.get(user_id, {}).get('phone')
        
        if phone:
            try:
                result = bot_manager.delete_destination(phone, destination_id)
                if result.get('success'):
                    await query.edit_message_text(
                        "✅ Destination deleted successfully.",
                        reply_markup=create_back_button("destinations_menu")
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Error deleting destination: {result.get('error', 'Unknown error')}",
                        reply_markup=create_back_button("destinations_menu")
                    )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Error: {str(e)}",
                    reply_markup=create_back_button("destinations_menu")
                )
        else:
            await query.edit_message_text(
                "❌ You are not logged in. Please login first.",
                reply_markup=create_back_to_main_keyboard()
            )

    elif data == "check_status":
        await show_status(user_id, query)
        
    elif data == "logout":
        phone = sessions.get(user_id, {}).get('phone')
        if phone:
            bot_manager.logout_user(phone)
            if user_id in sessions:
                del sessions[user_id]
            
            await query.edit_message_text(
                "✅ You have been successfully logged out.",
                reply_markup=create_back_to_main_keyboard()
            )
        else:
            await query.edit_message_text(
                "You are not logged in.",
                reply_markup=create_back_to_main_keyboard()
            )

async def show_main_menu(query):
    """Show the main menu."""
    user_id = query.from_user.id
    phone = sessions.get(user_id, {}).get('phone')
    
    if phone:
        # User is logged in
        keyboard = [
            [
                InlineKeyboardButton("📂 Sources", callback_data="sources_menu"),
                InlineKeyboardButton("📁 Destinations", callback_data="destinations_menu")
            ],
            [
                InlineKeyboardButton("▶️ Start Forwarding", callback_data="start_forwarding"),
                InlineKeyboardButton("⏹️ Cancel Forwarding", callback_data="cancel_forwarding")
            ],
            [
                InlineKeyboardButton("📊 Status", callback_data="check_status"),
                InlineKeyboardButton("🚪 Logout", callback_data="logout")
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="help")
            ]
        ]
    else:
        # User is not logged in
        keyboard = [
            [
                InlineKeyboardButton("🤖 Login", callback_data="login"),
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="help"),
                InlineKeyboardButton("👤 About", callback_data="about")
            ]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👋 Welcome to Telegram Forwarder Bot!\n\n"
        "This bot helps you forward messages from source channels to destination channels with resume capability.\n\n"
        "Please select an option:",
        reply_markup=reply_markup
    )

async def show_sources_menu(user_id, query):
    """Show the sources menu."""
    phone = sessions.get(user_id, {}).get('phone')
    
    if not phone:
        await query.edit_message_text(
            "❌ You are not logged in. Please login first.",
            reply_markup=create_back_to_main_keyboard()
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    sources = user_data.get('sources', {})
    
    if not sources:
        keyboard = [
            [InlineKeyboardButton("➕ Add Source", callback_data="add_source")],
            [InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "You have no source channels added yet. Add a source to start forwarding messages.",
            reply_markup=reply_markup
        )
        return
    
    # Create a list of sources with delete buttons
    keyboard = []
    for source_id, source in sources.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{source['title']}",
                callback_data=f"source_info:{source_id}"
            ),
            InlineKeyboardButton(
                "🗑️", 
                callback_data=f"delete_source:{source_id}"
            )
        ])
    
    # Add Add Source and Back buttons
    keyboard.append([InlineKeyboardButton("➕ Add Source", callback_data="add_source")])
    keyboard.append([InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📂 Your Source Channels\n\nSelect a source for more information or add a new one:",
        reply_markup=reply_markup
    )

async def show_destinations_menu(user_id, query):
    """Show the destinations menu."""
    phone = sessions.get(user_id, {}).get('phone')
    
    if not phone:
        await query.edit_message_text(
            "❌ You are not logged in. Please login first.",
            reply_markup=create_back_to_main_keyboard()
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    destinations = user_data.get('destinations', {})
    
    if not destinations:
        keyboard = [
            [InlineKeyboardButton("➕ Add Destination", callback_data="add_destination")],
            [InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "You have no destination channels added yet. Add a destination to start forwarding messages.",
            reply_markup=reply_markup
        )
        return
    
    # Create a list of destinations with delete buttons
    keyboard = []
    for dest_id, dest in destinations.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{dest['title']}",
                callback_data=f"destination_info:{dest_id}"
            ),
            InlineKeyboardButton(
                "🗑️", 
                callback_data=f"delete_destination:{dest_id}"
            )
        ])
    
    # Add Add Destination and Back buttons
    keyboard.append([InlineKeyboardButton("➕ Add Destination", callback_data="add_destination")])
    keyboard.append([InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📁 Your Destination Channels\n\nSelect a destination for more information or add a new one:",
        reply_markup=reply_markup
    )

async def show_forwarding_menu(user_id, query):
    """Show the forwarding menu."""
    phone = sessions.get(user_id, {}).get('phone')
    
    if not phone:
        await query.edit_message_text(
            "❌ You are not logged in. Please login first.",
            reply_markup=create_back_to_main_keyboard()
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    sources = user_data.get('sources', {})
    
    if not sources:
        keyboard = [
            [InlineKeyboardButton("➕ Add Source", callback_data="add_source")],
            [InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "You have no source channels added yet. Add a source to start forwarding.",
            reply_markup=reply_markup
        )
        return
    
    # Create a list of sources
    keyboard = []
    for source_id, source in sources.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{source['title']}",
                callback_data=f"select_source:{source_id}"
            )
        ])
    
    # Add Back button
    keyboard.append([InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔄 Start Forwarding\n\nSelect a source channel to forward from:",
        reply_markup=reply_markup
    )

async def show_destinations_for_forwarding(user_id, query):
    """Show destination selection for forwarding."""
    phone = sessions.get(user_id, {}).get('phone')
    
    if not phone:
        await query.edit_message_text(
            "❌ You are not logged in. Please login first.",
            reply_markup=create_back_to_main_keyboard()
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    destinations = user_data.get('destinations', {})
    
    if not destinations:
        keyboard = [
            [InlineKeyboardButton("➕ Add Destination", callback_data="add_destination")],
            [InlineKeyboardButton("« Back", callback_data="start_forwarding")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "You have no destination channels added yet. Add a destination to start forwarding.",
            reply_markup=reply_markup
        )
        return
    
    # Create a list of destinations
    keyboard = []
    for dest_id, dest in destinations.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{dest['title']}",
                callback_data=f"select_destination:{dest_id}"
            )
        ])
    
    # Add Back button
    keyboard.append([InlineKeyboardButton("« Back", callback_data="start_forwarding")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔄 Start Forwarding\n\nSelect a destination channel to forward to:",
        reply_markup=reply_markup
    )

async def show_status(user_id, query):
    """Show the current forwarding status."""
    phone = sessions.get(user_id, {}).get('phone')
    
    if not phone:
        await query.edit_message_text(
            "❌ You are not logged in. Please login first.",
            reply_markup=create_back_to_main_keyboard()
        )
        return
    
    status = bot_manager.get_forwarding_status(phone)
    
    if not status.get('active'):
        await query.edit_message_text(
            "📊 Status: No active forwarding task.",
            reply_markup=create_back_to_main_keyboard()
        )
        return
    
    # Get source and destination names
    user_data = bot_manager.get_user_data(phone)
    sources = user_data.get('sources', {})
    destinations = user_data.get('destinations', {})
    
    source_name = sources.get(status.get('source_id', '')).get('title', 'Unknown')
    destination_name = destinations.get(status.get('destination_id', '')).get('title', 'Unknown')
    
    status_text = (
        f"📊 Forwarding Status\n\n"
        f"Status: {status.get('status', 'Unknown')}\n"
        f"Source: {source_name}\n"
        f"Destination: {destination_name}\n"
        f"Progress: {status.get('forwarded_messages', 0)}/{status.get('total_messages', 0)} "
        f"({status.get('progress', 0)}%)\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="check_status")],
        [InlineKeyboardButton("⏹️ Cancel Forwarding", callback_data="cancel_forwarding")],
        [InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        status_text,
        reply_markup=reply_markup
    )

async def async_forward_messages(query, phone, source_id, destination_id):
    """Asynchronous wrapper for the forwarding process."""
    try:
        # Call the bot manager's forwarding method
        bot_manager.start_forwarding(phone, source_id, destination_id)
    except Exception as e:
        logger.error(f"Error in async_forward_messages: {str(e)}")

def create_back_to_main_keyboard():
    """Create a keyboard with just a back to main menu button."""
    keyboard = [[InlineKeyboardButton("« Back to Main Menu", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(keyboard)

def create_back_button(callback_data):
    """Create a keyboard with just a back button."""
    keyboard = [[InlineKeyboardButton("« Back", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages based on user state."""
    user_id = update.effective_user.id
    message_text = update.message.text
    state = user_states.get(user_id, STATE_INITIAL)
    
    # Initialize user session if not exists
    if user_id not in sessions:
        sessions[user_id] = {}
    
    # Handle cancel command
    if message_text == "/cancel":
        user_states[user_id] = STATE_INITIAL
        await update.message.reply_text(
            "Operation cancelled. What would you like to do next?",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Main Menu", callback_data="back_to_main")
            ]])
        )
        return

    # Handle login process states
    if state == STATE_AWAITING_API_ID:
        try:
            api_id = int(message_text)
            sessions[user_id]['api_id'] = api_id
            user_states[user_id] = STATE_AWAITING_API_HASH
            
            await update.message.reply_text(
                "Great! Now please enter your API Hash from my.telegram.org/apps\n\n"
                "Send /cancel to cancel the login process."
            )
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid API ID. Please enter a valid numeric API ID.\n\n"
                "Send /cancel to cancel the login process."
            )
    
    elif state == STATE_AWAITING_API_HASH:
        api_hash = message_text
        sessions[user_id]['api_hash'] = api_hash
        user_states[user_id] = STATE_AWAITING_PHONE
        
        await update.message.reply_text(
            "Now please enter your phone number with country code (e.g., +1234567890)\n\n"
            "Send /cancel to cancel the login process."
        )
    
    elif state == STATE_AWAITING_PHONE:
        phone = message_text
        sessions[user_id]['phone'] = phone
        api_id = sessions[user_id]['api_id']
        api_hash = sessions[user_id]['api_hash']
        
        try:
            result = bot_manager.initialize_bot(phone, api_id, api_hash)
            
            if result.get('needs_code'):
                user_states[user_id] = STATE_AWAITING_CODE
                await update.message.reply_text(
                    "Please enter the verification code sent to your Telegram app.\n\n"
                    "Send /cancel to cancel the login process."
                )
            else:
                user_states[user_id] = STATE_INITIAL
                await update.message.reply_text(
                    "✅ Login successful! You can now use the bot features.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                    ]])
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error during login: {str(e)}\n\n"
                "Please try again or send /cancel to cancel the login process."
            )
    
    elif state == STATE_AWAITING_CODE:
        code = message_text
        phone = sessions[user_id]['phone']
        
        try:
            result = bot_manager.submit_code(phone, code)
            
            if result.get('success'):
                user_states[user_id] = STATE_INITIAL
                await update.message.reply_text(
                    "✅ Login successful! You can now use the bot features.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                    ]])
                )
            else:
                await update.message.reply_text(
                    f"❌ Error: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel the login process."
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error submitting code: {str(e)}\n\n"
                "Please try again or send /cancel to cancel the login process."
            )
    
    elif state == STATE_AWAITING_SOURCE:
        source_link = message_text
        phone = sessions[user_id]['phone']
        
        try:
            result = bot_manager.add_source(phone, source_link)
            
            if result.get('success'):
                user_states[user_id] = STATE_INITIAL
                source = result.get('source')
                await update.message.reply_text(
                    f"✅ Source added successfully!\n\n"
                    f"Title: {source['title']}\n"
                    f"Link: {source['link']}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Sources Menu", callback_data="sources_menu")
                    ], [
                        InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                    ]])
                )
            else:
                await update.message.reply_text(
                    f"❌ Error adding source: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel."
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}\n\n"
                "Please try again or send /cancel to cancel."
            )
    
    elif state == STATE_AWAITING_DESTINATION:
        destination_link = message_text
        phone = sessions[user_id]['phone']
        
        try:
            result = bot_manager.add_destination(phone, destination_link)
            
            if result.get('success'):
                user_states[user_id] = STATE_INITIAL
                destination = result.get('destination')
                await update.message.reply_text(
                    f"✅ Destination added successfully!\n\n"
                    f"Title: {destination['title']}\n"
                    f"Link: {destination['link']}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Destinations Menu", callback_data="destinations_menu")
                    ], [
                        InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                    ]])
                )
            else:
                await update.message.reply_text(
                    f"❌ Error adding destination: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel."
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}\n\n"
                "Please try again or send /cancel to cancel."
            )
    
    elif state == STATE_AWAITING_LAST_MESSAGE:
        last_message_link = message_text
        phone = sessions[user_id]['phone']
        source_id = sessions[user_id].get('selected_source_id')
        destination_id = sessions[user_id].get('selected_destination_id')
        
        if not source_id or not destination_id:
            await update.message.reply_text(
                "❌ Error: Source or destination not selected properly.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                ]])
            )
            return
        
        try:
            # Set the last message
            result = bot_manager.set_last_message(phone, source_id, last_message_link)
            
            if result.get('success'):
                # Start forwarding
                asyncio.create_task(
                    async_forward_messages(None, phone, source_id, destination_id)
                )
                
                user_states[user_id] = STATE_INITIAL
                
                await update.message.reply_text(
                    "✅ Last message set and forwarding task started!\n\n"
                    "You can check the status or cancel the task from the main menu.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                    ]])
                )
            else:
                await update.message.reply_text(
                    f"❌ Error setting last message: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel."
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}\n\n"
                "Please try again or send /cancel to cancel."
            )
    
    else:
        # Default response for unhandled states or general messages
        await update.message.reply_text(
            "I'm not sure what you want to do. Please use the commands or buttons to interact with me.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Main Menu", callback_data="back_to_main")
            ]])
        )

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /logout command."""
    user_id = update.effective_user.id
    phone = sessions.get(user_id, {}).get('phone')
    
    if phone:
        bot_manager.logout_user(phone)
        if user_id in sessions:
            del sessions[user_id]
        
        await update.message.reply_text(
            "✅ You have been successfully logged out.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Main Menu", callback_data="back_to_main")
            ]])
        )
    else:
        await update.message.reply_text(
            "You are not logged in.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Main Menu", callback_data="back_to_main")
            ]])
        )

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /login command."""
    user_id = update.effective_user.id
    user_states[user_id] = STATE_AWAITING_API_ID
    
    await update.message.reply_text(
        "Please enter your API ID from my.telegram.org/apps\n\n"
        "Send /cancel to cancel the login process."
    )

async def sources_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /sources command."""
    query = await update.message.reply_text(
        "Loading sources...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Please wait...", callback_data="dummy")
        ]])
    )
    
    # Create a dummy callback query to reuse the show_sources_menu function
    class DummyObj:
        pass
    
    dummy_query = DummyObj()
    dummy_query.message = query
    dummy_query.from_user = update.effective_user
    dummy_query.edit_message_text = query.edit_text
    
    await show_sources_menu(update.effective_user.id, dummy_query)

async def destinations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /destinations command."""
    query = await update.message.reply_text(
        "Loading destinations...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Please wait...", callback_data="dummy")
        ]])
    )
    
    # Create a dummy callback query to reuse the show_destinations_menu function
    class DummyObj:
        pass
    
    dummy_query = DummyObj()
    dummy_query.message = query
    dummy_query.from_user = update.effective_user
    dummy_query.edit_message_text = query.edit_text
    
    await show_destinations_menu(update.effective_user.id, dummy_query)

async def forward_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /forward command."""
    query = await update.message.reply_text(
        "Loading forwarding options...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Please wait...", callback_data="dummy")
        ]])
    )
    
    # Create a dummy callback query to reuse the show_forwarding_menu function
    class DummyObj:
        pass
    
    dummy_query = DummyObj()
    dummy_query.message = query
    dummy_query.from_user = update.effective_user
    dummy_query.edit_message_text = query.edit_text
    
    await show_forwarding_menu(update.effective_user.id, dummy_query)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /status command."""
    query = await update.message.reply_text(
        "Loading status...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Please wait...", callback_data="dummy")
        ]])
    )
    
    # Create a dummy callback query to reuse the show_status function
    class DummyObj:
        pass
    
    dummy_query = DummyObj()
    dummy_query.message = query
    dummy_query.from_user = update.effective_user
    dummy_query.edit_message_text = query.edit_text
    
    await show_status(update.effective_user.id, dummy_query)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /cancel command."""
    user_id = update.effective_user.id
    phone = sessions.get(user_id, {}).get('phone')
    
    if not phone:
        await update.message.reply_text(
            "❌ You are not logged in. Please login first.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Main Menu", callback_data="back_to_main")
            ]])
        )
        return
    
    try:
        result = bot_manager.cancel_forwarding(phone)
        
        if result.get('success'):
            await update.message.reply_text(
                "✅ Forwarding has been cancelled successfully.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                ]])
            )
        else:
            await update.message.reply_text(
                f"❌ Error cancelling forwarding: {result.get('error', 'Unknown error')}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Main Menu", callback_data="back_to_main")
                ]])
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Main Menu", callback_data="back_to_main")
            ]])
        )

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("No bot token provided! Set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    application = Application.builder().token(bot_token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(CommandHandler("sources", sources_command))
    application.add_handler(CommandHandler("destinations", destinations_command))
    application.add_handler(CommandHandler("forward", forward_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()