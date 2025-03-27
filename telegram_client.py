import os
import logging
import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom import Button
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
user_sessions = {}  # Maps user_id to session data

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

# Create your Telegram bot client
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not bot_token:
    logger.error("No bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")
    exit(1)

# Initialize the bot client - for bot clients, we need to use TelegramClient.start() with a bot token
# Need to use real API ID and hash even for bots, as Telethon validates them
bot = TelegramClient('sessions/telegram_bot', 20188881, "a2649ce2b3c47c0d4f89a1e94ff52e4a")
bot.parse_mode = 'markdown'

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Handle the /start command."""
    user_id = event.sender_id
    
    # Reset user state
    if user_id in user_sessions:
        user_sessions[user_id] = {}
    
    # Create main menu keyboard
    keyboard = [
        [Button.inline("🤖 Login", b"login")],
        [Button.inline("ℹ️ Help", b"help"), Button.inline("👤 About", b"about")]
    ]
    
    await event.respond(
        "👋 Welcome to Telegram Forwarder Bot!\n\n"
        "This bot helps you forward messages from source channels to destination channels with resume capability.\n\n"
        "Please select an option:",
        buttons=keyboard
    )

@bot.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    """Handle the /help command."""
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
    
    await event.respond(help_text)

@bot.on(events.NewMessage(pattern='/about'))
async def about_command(event):
    """Handle the /about command."""
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
    
    await event.respond(about_text)

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    """Handle button callbacks."""
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    session = user_sessions[user_id]
    
    # Handle different button callbacks
    if data == "login":
        session['state'] = STATE_AWAITING_API_ID
        await event.edit(
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
        
        await event.edit(help_text)
    
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
        
        await event.edit(about_text)
    
    elif data == "back_to_main":
        await show_main_menu(event)
    
    elif data == "sources_menu":
        await show_sources_menu(event, user_id)
    
    elif data == "destinations_menu":
        await show_destinations_menu(event, user_id)
    
    elif data == "add_source":
        session['state'] = STATE_AWAITING_SOURCE
        await event.edit(
            "Please enter the source channel/group link or username\n\n"
            "Examples:\n"
            "• Public channel: @channelname or https://t.me/channelname\n"
            "• Private channel: https://t.me/joinchat/XXXXXXXXXXXX\n\n"
            "Send /cancel to cancel."
        )
    
    elif data == "add_destination":
        session['state'] = STATE_AWAITING_DESTINATION
        await event.edit(
            "Please enter the destination channel/group link or username\n\n"
            "Examples:\n"
            "• Public channel: @channelname or https://t.me/channelname\n"
            "• Private channel: https://t.me/joinchat/XXXXXXXXXXXX\n\n"
            "Send /cancel to cancel."
        )
    
    elif data == "start_forwarding":
        await show_forwarding_menu(event, user_id)
    
    elif data == "cancel_forwarding":
        phone = session.get('phone')
        if phone:
            try:
                result = bot_manager.cancel_forwarding(phone)
                if result.get('success'):
                    await event.edit(
                        "✅ Forwarding has been cancelled successfully.",
                        buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
                    )
                else:
                    await event.edit(
                        f"❌ Error cancelling forwarding: {result.get('error', 'Unknown error')}",
                        buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
                    )
            except Exception as e:
                await event.edit(
                    f"❌ Error: {str(e)}",
                    buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
                )
        else:
            await event.edit(
                "❌ You are not logged in. Please login first.",
                buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
            )
    
    elif data == "check_status":
        await show_status(event, user_id)
    
    elif data == "logout":
        phone = session.get('phone')
        if phone:
            result = bot_manager.logout_user(phone)
            user_sessions[user_id] = {}
            
            await event.edit(
                "✅ You have been successfully logged out.",
                buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
            )
        else:
            await event.edit(
                "You are not logged in.",
                buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
            )
    
    elif data.startswith("delete_source:"):
        source_id = data.split(":")[1]
        phone = session.get('phone')
        
        if phone:
            try:
                result = bot_manager.delete_source(phone, source_id)
                if result.get('success'):
                    await event.edit(
                        "✅ Source deleted successfully.",
                        buttons=[Button.inline("« Back", b"sources_menu")]
                    )
                else:
                    await event.edit(
                        f"❌ Error deleting source: {result.get('error', 'Unknown error')}",
                        buttons=[Button.inline("« Back", b"sources_menu")]
                    )
            except Exception as e:
                await event.edit(
                    f"❌ Error: {str(e)}",
                    buttons=[Button.inline("« Back", b"sources_menu")]
                )
        else:
            await event.edit(
                "❌ You are not logged in. Please login first.",
                buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
            )
    
    elif data.startswith("delete_destination:"):
        destination_id = data.split(":")[1]
        phone = session.get('phone')
        
        if phone:
            try:
                result = bot_manager.delete_destination(phone, destination_id)
                if result.get('success'):
                    await event.edit(
                        "✅ Destination deleted successfully.",
                        buttons=[Button.inline("« Back", b"destinations_menu")]
                    )
                else:
                    await event.edit(
                        f"❌ Error deleting destination: {result.get('error', 'Unknown error')}",
                        buttons=[Button.inline("« Back", b"destinations_menu")]
                    )
            except Exception as e:
                await event.edit(
                    f"❌ Error: {str(e)}",
                    buttons=[Button.inline("« Back", b"destinations_menu")]
                )
        else:
            await event.edit(
                "❌ You are not logged in. Please login first.",
                buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
            )
    
    elif data.startswith("select_source:"):
        source_id = data.split(":")[1]
        session['selected_source_id'] = source_id
        session['state'] = STATE_SELECTING_SOURCE
        
        # Now ask for destination
        await show_destinations_for_forwarding(event, user_id)
    
    elif data.startswith("select_destination:"):
        if session.get('state') == STATE_SELECTING_SOURCE:
            destination_id = data.split(":")[1]
            source_id = session.get('selected_source_id')
            
            if source_id and destination_id:
                # Ask if user wants to set last message
                buttons = [
                    [
                        Button.inline("Yes", f"set_last_message:{source_id}:{destination_id}".encode('utf-8')),
                        Button.inline("No", f"forward_now:{source_id}:{destination_id}".encode('utf-8'))
                    ],
                    [Button.inline("« Back", b"start_forwarding")]
                ]
                
                await event.edit(
                    "Do you want to set a last message link? This will forward all messages from the beginning up to this message.",
                    buttons=buttons
                )
            else:
                await event.edit(
                    "❌ Error: Source or destination not selected properly.",
                    buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
                )
    
    elif data.startswith("set_last_message:"):
        parts = data.split(":")
        source_id = parts[1]
        destination_id = parts[2]
        
        session['selected_source_id'] = source_id
        session['selected_destination_id'] = destination_id
        session['state'] = STATE_AWAITING_LAST_MESSAGE
        
        await event.edit(
            "Please enter the last message link from the source channel.\n\n"
            "Format: https://t.me/c/1234567890/123\n\n"
            "Send /cancel to cancel."
        )
    
    elif data.startswith("forward_now:"):
        parts = data.split(":")
        source_id = parts[1]
        destination_id = parts[2]
        
        phone = session.get('phone')
        if phone:
            try:
                bot_manager.start_forwarding(phone, source_id, destination_id)
                
                await event.edit(
                    "✅ Forwarding task has been started!\n\n"
                    "You can check the status or cancel the task from the main menu.",
                    buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
                )
            except Exception as e:
                await event.edit(
                    f"❌ Error starting forwarding: {str(e)}",
                    buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
                )
        else:
            await event.edit(
                "❌ You are not logged in. Please login first.",
                buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
            )

@bot.on(events.NewMessage())
async def message_handler(event):
    """Handle incoming text messages."""
    user_id = event.sender_id
    
    # Ignore non-private chats
    if not event.is_private:
        return
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {'state': STATE_INITIAL}
    
    session = user_sessions[user_id]
    state = session.get('state', STATE_INITIAL)
    
    # Get the message text
    message_text = event.message.text
    
    # Handle cancel command
    if message_text == '/cancel':
        session['state'] = STATE_INITIAL
        await event.respond(
            "Operation cancelled. What would you like to do next?",
            buttons=[Button.inline("Main Menu", b"back_to_main")]
        )
        return
    
    # Handle login process states
    if state == STATE_AWAITING_API_ID:
        try:
            api_id = int(message_text)
            session['api_id'] = api_id
            session['state'] = STATE_AWAITING_API_HASH
            
            await event.respond(
                "Great! Now please enter your API Hash from my.telegram.org/apps\n\n"
                "Send /cancel to cancel the login process."
            )
        except ValueError:
            await event.respond(
                "❌ Invalid API ID. Please enter a valid numeric API ID.\n\n"
                "Send /cancel to cancel the login process."
            )
    
    elif state == STATE_AWAITING_API_HASH:
        api_hash = message_text
        session['api_hash'] = api_hash
        session['state'] = STATE_AWAITING_PHONE
        
        await event.respond(
            "Now please enter your phone number with country code (e.g., +1234567890)\n\n"
            "Send /cancel to cancel the login process."
        )
    
    elif state == STATE_AWAITING_PHONE:
        phone = message_text
        session['phone'] = phone
        api_id = session['api_id']
        api_hash = session['api_hash']
        
        try:
            result = bot_manager.initialize_bot(phone, api_id, api_hash)
            
            if result.get('needs_code'):
                session['state'] = STATE_AWAITING_CODE
                await event.respond(
                    "Please enter the verification code sent to your Telegram app.\n\n"
                    "Send /cancel to cancel the login process."
                )
            else:
                session['state'] = STATE_INITIAL
                await event.respond(
                    "✅ Login successful! You can now use the bot features.",
                    buttons=[Button.inline("Main Menu", b"back_to_main")]
                )
        except Exception as e:
            await event.respond(
                f"❌ Error during login: {str(e)}\n\n"
                "Please try again or send /cancel to cancel the login process."
            )
    
    elif state == STATE_AWAITING_CODE:
        code = message_text
        phone = session['phone']
        
        try:
            result = bot_manager.submit_code(phone, code)
            
            if result.get('success'):
                session['state'] = STATE_INITIAL
                await event.respond(
                    "✅ Login successful! You can now use the bot features.",
                    buttons=[Button.inline("Main Menu", b"back_to_main")]
                )
            else:
                await event.respond(
                    f"❌ Error: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel the login process."
                )
        except Exception as e:
            await event.respond(
                f"❌ Error submitting code: {str(e)}\n\n"
                "Please try again or send /cancel to cancel the login process."
            )
    
    elif state == STATE_AWAITING_SOURCE:
        source_link = message_text
        phone = session['phone']
        
        try:
            result = bot_manager.add_source(phone, source_link)
            
            if result.get('success'):
                session['state'] = STATE_INITIAL
                source = result.get('source')
                await event.respond(
                    f"✅ Source added successfully!\n\n"
                    f"Title: {source['title']}\n"
                    f"Link: {source['link']}",
                    buttons=[
                        [Button.inline("Sources Menu", b"sources_menu")],
                        [Button.inline("Main Menu", b"back_to_main")]
                    ]
                )
            else:
                await event.respond(
                    f"❌ Error adding source: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel."
                )
        except Exception as e:
            await event.respond(
                f"❌ Error: {str(e)}\n\n"
                "Please try again or send /cancel to cancel."
            )
    
    elif state == STATE_AWAITING_DESTINATION:
        destination_link = message_text
        phone = session['phone']
        
        try:
            result = bot_manager.add_destination(phone, destination_link)
            
            if result.get('success'):
                session['state'] = STATE_INITIAL
                destination = result.get('destination')
                await event.respond(
                    f"✅ Destination added successfully!\n\n"
                    f"Title: {destination['title']}\n"
                    f"Link: {destination['link']}",
                    buttons=[
                        [Button.inline("Destinations Menu", b"destinations_menu")],
                        [Button.inline("Main Menu", b"back_to_main")]
                    ]
                )
            else:
                await event.respond(
                    f"❌ Error adding destination: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel."
                )
        except Exception as e:
            await event.respond(
                f"❌ Error: {str(e)}\n\n"
                "Please try again or send /cancel to cancel."
            )
    
    elif state == STATE_AWAITING_LAST_MESSAGE:
        last_message_link = message_text
        phone = session['phone']
        source_id = session.get('selected_source_id')
        destination_id = session.get('selected_destination_id')
        
        if not source_id or not destination_id:
            await event.respond(
                "❌ Error: Source or destination not selected properly.",
                buttons=[Button.inline("Main Menu", b"back_to_main")]
            )
            return
        
        try:
            # Set the last message
            result = bot_manager.set_last_message(phone, source_id, last_message_link)
            
            if result.get('success'):
                # Start forwarding
                bot_manager.start_forwarding(phone, source_id, destination_id)
                
                session['state'] = STATE_INITIAL
                
                await event.respond(
                    "✅ Last message set and forwarding task started!\n\n"
                    "You can check the status or cancel the task from the main menu.",
                    buttons=[Button.inline("Main Menu", b"back_to_main")]
                )
            else:
                await event.respond(
                    f"❌ Error setting last message: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again or send /cancel to cancel."
                )
        except Exception as e:
            await event.respond(
                f"❌ Error: {str(e)}\n\n"
                "Please try again or send /cancel to cancel."
            )
    
    else:
        # Default response for unhandled states or general messages
        await event.respond(
            "I'm not sure what you want to do. Please use the commands or buttons to interact with me.",
            buttons=[Button.inline("Main Menu", b"back_to_main")]
        )

async def show_main_menu(event):
    """Show the main menu."""
    user_id = event.sender_id
    session = user_sessions.get(user_id, {})
    phone = session.get('phone')
    
    if phone:
        # User is logged in
        buttons = [
            [
                Button.inline("📂 Sources", b"sources_menu"),
                Button.inline("📁 Destinations", b"destinations_menu")
            ],
            [
                Button.inline("▶️ Start Forwarding", b"start_forwarding"),
                Button.inline("⏹️ Cancel Forwarding", b"cancel_forwarding")
            ],
            [
                Button.inline("📊 Status", b"check_status"),
                Button.inline("🚪 Logout", b"logout")
            ],
            [
                Button.inline("ℹ️ Help", b"help")
            ]
        ]
    else:
        # User is not logged in
        buttons = [
            [Button.inline("🤖 Login", b"login")],
            [Button.inline("ℹ️ Help", b"help"), Button.inline("👤 About", b"about")]
        ]
    
    await event.edit(
        "👋 Welcome to Telegram Forwarder Bot!\n\n"
        "This bot helps you forward messages from source channels to destination channels with resume capability.\n\n"
        "Please select an option:",
        buttons=buttons
    )

async def show_sources_menu(event, user_id):
    """Show the sources menu."""
    session = user_sessions.get(user_id, {})
    phone = session.get('phone')
    
    if not phone:
        await event.edit(
            "❌ You are not logged in. Please login first.",
            buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    sources = user_data.get('sources', {})
    
    if not sources:
        buttons = [
            [Button.inline("➕ Add Source", b"add_source")],
            [Button.inline("« Back to Main Menu", b"back_to_main")]
        ]
        
        await event.edit(
            "You have no source channels added yet. Add a source to start forwarding messages.",
            buttons=buttons
        )
        return
    
    # Create a list of sources with delete buttons
    buttons = []
    for source_id, source in sources.items():
        buttons.append([
            Button.inline(f"{source['title']}", f"source_info:{source_id}".encode('utf-8')),
            Button.inline("🗑️", f"delete_source:{source_id}".encode('utf-8'))
        ])
    
    # Add Add Source and Back buttons
    buttons.append([Button.inline("➕ Add Source", b"add_source")])
    buttons.append([Button.inline("« Back to Main Menu", b"back_to_main")])
    
    await event.edit(
        "📂 Your Source Channels\n\nSelect a source for more information or add a new one:",
        buttons=buttons
    )

async def show_destinations_menu(event, user_id):
    """Show the destinations menu."""
    session = user_sessions.get(user_id, {})
    phone = session.get('phone')
    
    if not phone:
        await event.edit(
            "❌ You are not logged in. Please login first.",
            buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    destinations = user_data.get('destinations', {})
    
    if not destinations:
        buttons = [
            [Button.inline("➕ Add Destination", b"add_destination")],
            [Button.inline("« Back to Main Menu", b"back_to_main")]
        ]
        
        await event.edit(
            "You have no destination channels added yet. Add a destination to start forwarding messages.",
            buttons=buttons
        )
        return
    
    # Create a list of destinations with delete buttons
    buttons = []
    for dest_id, dest in destinations.items():
        buttons.append([
            Button.inline(f"{dest['title']}", f"destination_info:{dest_id}".encode('utf-8')),
            Button.inline("🗑️", f"delete_destination:{dest_id}".encode('utf-8'))
        ])
    
    # Add Add Destination and Back buttons
    buttons.append([Button.inline("➕ Add Destination", b"add_destination")])
    buttons.append([Button.inline("« Back to Main Menu", b"back_to_main")])
    
    await event.edit(
        "📁 Your Destination Channels\n\nSelect a destination for more information or add a new one:",
        buttons=buttons
    )

async def show_forwarding_menu(event, user_id):
    """Show the forwarding menu."""
    session = user_sessions.get(user_id, {})
    phone = session.get('phone')
    
    if not phone:
        await event.edit(
            "❌ You are not logged in. Please login first.",
            buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    sources = user_data.get('sources', {})
    
    if not sources:
        buttons = [
            [Button.inline("➕ Add Source", b"add_source")],
            [Button.inline("« Back to Main Menu", b"back_to_main")]
        ]
        
        await event.edit(
            "You have no source channels added yet. Add a source to start forwarding.",
            buttons=buttons
        )
        return
    
    # Create a list of sources
    buttons = []
    for source_id, source in sources.items():
        buttons.append([
            Button.inline(f"{source['title']}", f"select_source:{source_id}".encode('utf-8'))
        ])
    
    # Add Back button
    buttons.append([Button.inline("« Back to Main Menu", b"back_to_main")])
    
    await event.edit(
        "🔄 Start Forwarding\n\nSelect a source channel to forward from:",
        buttons=buttons
    )

async def show_destinations_for_forwarding(event, user_id):
    """Show destination selection for forwarding."""
    session = user_sessions.get(user_id, {})
    phone = session.get('phone')
    
    if not phone:
        await event.edit(
            "❌ You are not logged in. Please login first.",
            buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
        )
        return
    
    user_data = bot_manager.get_user_data(phone)
    destinations = user_data.get('destinations', {})
    
    if not destinations:
        buttons = [
            [Button.inline("➕ Add Destination", b"add_destination")],
            [Button.inline("« Back", b"start_forwarding")]
        ]
        
        await event.edit(
            "You have no destination channels added yet. Add a destination to start forwarding.",
            buttons=buttons
        )
        return
    
    # Create a list of destinations
    buttons = []
    for dest_id, dest in destinations.items():
        buttons.append([
            Button.inline(f"{dest['title']}", f"select_destination:{dest_id}".encode('utf-8'))
        ])
    
    # Add Back button
    buttons.append([Button.inline("« Back", b"start_forwarding")])
    
    await event.edit(
        "🔄 Start Forwarding\n\nSelect a destination channel to forward to:",
        buttons=buttons
    )

async def show_status(event, user_id):
    """Show the current forwarding status."""
    session = user_sessions.get(user_id, {})
    phone = session.get('phone')
    
    if not phone:
        await event.edit(
            "❌ You are not logged in. Please login first.",
            buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
        )
        return
    
    status = bot_manager.get_forwarding_status(phone)
    
    if not status.get('active'):
        await event.edit(
            "📊 Status: No active forwarding task.",
            buttons=[Button.inline("« Back to Main Menu", b"back_to_main")]
        )
        return
    
    # Get source and destination names
    user_data = bot_manager.get_user_data(phone)
    sources = user_data.get('sources', {})
    destinations = user_data.get('destinations', {})
    
    source_id = status.get('source_id', '')
    destination_id = status.get('destination_id', '')
    
    source_name = sources.get(source_id, {}).get('title', 'Unknown')
    destination_name = destinations.get(destination_id, {}).get('title', 'Unknown')
    
    status_text = (
        f"📊 Forwarding Status\n\n"
        f"Status: {status.get('status', 'Unknown')}\n"
        f"Source: {source_name}\n"
        f"Destination: {destination_name}\n"
        f"Progress: {status.get('forwarded_messages', 0)}/{status.get('total_messages', 0)} "
        f"({status.get('progress', 0)}%)\n"
    )
    
    buttons = [
        [Button.inline("🔄 Refresh", b"check_status")],
        [Button.inline("⏹️ Cancel Forwarding", b"cancel_forwarding")],
        [Button.inline("« Back to Main Menu", b"back_to_main")]
    ]
    
    await event.edit(status_text, buttons=buttons)

@bot.on(events.NewMessage(pattern='/login'))
async def login_command(event):
    """Handle the /login command."""
    user_id = event.sender_id
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    user_sessions[user_id]['state'] = STATE_AWAITING_API_ID
    
    await event.respond(
        "Please enter your API ID from my.telegram.org/apps\n\n"
        "Send /cancel to cancel the login process."
    )

@bot.on(events.NewMessage(pattern='/logout'))
async def logout_command(event):
    """Handle the /logout command."""
    user_id = event.sender_id
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
        await event.respond(
            "You are not logged in.",
            buttons=[Button.inline("Main Menu", b"back_to_main")]
        )
        return
    
    phone = user_sessions[user_id].get('phone')
    if phone:
        bot_manager.logout_user(phone)
        user_sessions[user_id] = {}
        
        await event.respond(
            "✅ You have been successfully logged out.",
            buttons=[Button.inline("Main Menu", b"back_to_main")]
        )
    else:
        await event.respond(
            "You are not logged in.",
            buttons=[Button.inline("Main Menu", b"back_to_main")]
        )

@bot.on(events.NewMessage(pattern='/sources'))
async def sources_command(event):
    """Handle the /sources command."""
    user_id = event.sender_id
    
    # Send a reply that will be updated
    response = await event.respond("Loading sources...")
    
    # Update the message with the sources menu
    await show_sources_menu(response, user_id)

@bot.on(events.NewMessage(pattern='/destinations'))
async def destinations_command(event):
    """Handle the /destinations command."""
    user_id = event.sender_id
    
    # Send a reply that will be updated
    response = await event.respond("Loading destinations...")
    
    # Update the message with the destinations menu
    await show_destinations_menu(response, user_id)

@bot.on(events.NewMessage(pattern='/forward'))
async def forward_command(event):
    """Handle the /forward command."""
    user_id = event.sender_id
    
    # Send a reply that will be updated
    response = await event.respond("Loading forwarding options...")
    
    # Update the message with the forwarding menu
    await show_forwarding_menu(response, user_id)

@bot.on(events.NewMessage(pattern='/status'))
async def status_command(event):
    """Handle the /status command."""
    user_id = event.sender_id
    
    # Send a reply that will be updated
    response = await event.respond("Loading status...")
    
    # Update the message with the status
    await show_status(response, user_id)

@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel_command(event):
    """Handle the /cancel command."""
    user_id = event.sender_id
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    session = user_sessions[user_id]
    phone = session.get('phone')
    
    if not phone:
        await event.respond(
            "❌ You are not logged in. Please login first.",
            buttons=[Button.inline("Main Menu", b"back_to_main")]
        )
        return
    
    try:
        result = bot_manager.cancel_forwarding(phone)
        
        if result.get('success'):
            await event.respond(
                "✅ Forwarding has been cancelled successfully.",
                buttons=[Button.inline("Main Menu", b"back_to_main")]
            )
        else:
            await event.respond(
                f"❌ Error cancelling forwarding: {result.get('error', 'Unknown error')}",
                buttons=[Button.inline("Main Menu", b"back_to_main")]
            )
    except Exception as e:
        await event.respond(
            f"❌ Error: {str(e)}",
            buttons=[Button.inline("Main Menu", b"back_to_main")]
        )

async def main():
    """Start the bot."""
    try:
        # Start the bot with the bot token
        logger.info("Starting Telegram bot with token...")
        await bot.start(bot_token=bot_token)
        logger.info("Telegram Bot started successfully!")
        
        # Run the bot until disconnect
        await bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"Error in bot main loop: {e}")
        raise

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())