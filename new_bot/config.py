# Advanced Telegram Forwarder Bot
# Improved by Replit AI

from os import environ 

class Config:
    
    API_ID = environ.get("API_ID", "")
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN", "") 
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '0').split()]
    BOT_SESSION = environ.get("BOT_SESSION", "advanced_forwarder_bot") 

    PICS = (environ.get('PICS', 'https://graph.org/file/e223aea8aca83e99162bb.jpg'))
    
    # We'll use a PostgreSQL database on Replit with connection string
    DATABASE_URI = environ.get("DATABASE_URL", "")
    DATABASE_NAME = environ.get("PGDATABASE", "ForwarderBot")
    
    LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '0'))
    FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "") # FORCE SUB channel link 
    FORCE_SUB_ON = environ.get("FORCE_SUB_ON", "FALSE")  # FORCE SUB ON - OFF
    
    # New settings for improved forwarding
    FORWARD_SLEEP = 3  # Sleep time between forwards in seconds (changed from 10 to 3)


class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    
    # New: Task tracking for resume functionality
    ACTIVE_TASKS = {}  # Stores active forwarding tasks for resume capability