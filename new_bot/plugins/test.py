import os
import sys
import json
import asyncio
import logging
from pyrogram import Client
from config import Config, temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def start_clone_bot(client):
    """Start a client session"""
    try:
        await client.start()
        return client
    except Exception as e:
        logger.error(f"Failed to start client: {e}")
        raise e

class CLIENT:
    """Client manager for bot or user accounts"""
    def __init__(self):
        pass
        
    def client(self, data, user=None):
        """Create a new Pyrogram Client instance"""
        try:
            if data['is_bot']:
                return Client(
                    name=f"{data['username']}",
                    api_id=Config.API_ID,
                    api_hash=Config.API_HASH,
                    bot_token=data['token'],
                    in_memory=False,
                    no_updates=True,
                    workdir="sessions"
                )
            else:
                # User client - provide string session
                return Client(
                    name=f"{data['phone']}",
                    api_id=data['api_id'],
                    api_hash=data['api_hash'],
                    session_string=data['session_string'],
                    in_memory=False,
                    no_updates=True,
                    workdir="sessions"
                )
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            return None

def parse_buttons(text, markup=True):
    """Parse button text into InlineKeyboardMarkup"""
    if not text or not markup:
        return None
        
    try:
        if "{" in text and "}" in text:
            buttons = []
            for line in text.split("\n"):
                if "{" in line and "}" in line:
                    matches = re.findall(r'\{([^}]+)\}\(([^)]+)\)', line)
                    btn_row = []
                    for match in matches:
                        btn_text, btn_url = match
                        btn_row.append(InlineKeyboardButton(btn_text, url=btn_url))
                    if btn_row:
                        buttons.append(btn_row)
            return InlineKeyboardMarkup(buttons) if buttons else None
    except Exception as e:
        logger.error(f"Error parsing buttons: {e}")
    
    return None