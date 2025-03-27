# Advanced Telegram Forwarder Bot
# Improved by Replit AI - PostgreSQL Version

import os
import json
import asyncio
import psycopg2
import logging
from config import Config
import asyncpg

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def dict_to_json(dict_value):
    """Convert dict to JSON string for storage"""
    if dict_value is None:
        return None
    return json.dumps(dict_value)

def json_to_dict(json_value):
    """Convert JSON string to dict"""
    if json_value is None:
        return None
    try:
        return json.loads(json_value)
    except:
        return None

class Database:
    
    def __init__(self, uri, database_name):
        """Initialize the PostgreSQL database connection"""
        self.uri = uri
        self.database_name = database_name
        self.pool = None
        
    async def connect(self):
        """Create connection pool and initialize tables"""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(dsn=self.uri)
                await self._init_tables()
                logger.info("Successfully connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                raise e
    
    async def _init_tables(self):
        """Initialize database tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    name TEXT,
                    ban_status JSONB DEFAULT '{"is_banned": false, "ban_reason": ""}'::jsonb,
                    configs JSONB DEFAULT '{
                        "caption": null,
                        "duplicate": true,
                        "forward_tag": false,
                        "file_size": 0,
                        "size_limit": null,
                        "extension": null,
                        "keywords": null,
                        "protect": null,
                        "button": null,
                        "db_uri": null,
                        "filters": {
                            "poll": true,
                            "text": true,
                            "audio": true,
                            "voice": true,
                            "video": true,
                            "photo": true,
                            "document": true,
                            "animation": true,
                            "sticker": true
                        }
                    }'::jsonb
                )
            ''')
            
            # Bots table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    bot_id BIGINT,
                    name TEXT,
                    username TEXT,
                    token TEXT,
                    is_bot BOOLEAN DEFAULT TRUE,
                    api_id TEXT DEFAULT NULL,
                    api_hash TEXT DEFAULT NULL,
                    phone TEXT DEFAULT NULL,
                    session_string TEXT DEFAULT NULL
                )
            ''')
            
            # Channels table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    ch_id BIGINT NOT NULL,
                    title TEXT,
                    type TEXT,
                    username TEXT,
                    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Notify table (forwarding status)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS notify (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tasks table (for resuming forwarding)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    task_id TEXT UNIQUE NOT NULL,
                    user_id BIGINT NOT NULL,
                    from_chat TEXT NOT NULL,
                    to_chat TEXT NOT NULL,
                    bot_details JSONB,
                    last_forwarded_msg_id BIGINT DEFAULT 0,
                    total_count BIGINT DEFAULT 0,
                    offset BIGINT DEFAULT 0,
                    configs JSONB,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def new_user(self, id, name):
        """Create a new user object"""
        return {
            'id': id,
            'name': name,
            'ban_status': {
                'is_banned': False,
                'ban_reason': ''
            }
        }
      
    async def add_user(self, id, name):
        """Add a new user to the database"""
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO users (id, name) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING',
                id, name
            )
    
    async def is_user_exist(self, id):
        """Check if a user exists in the database"""
        await self.connect()
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow('SELECT id FROM users WHERE id = $1', int(id))
            return bool(user)
    
    async def total_users_bots_count(self):
        """Get total users and bots count"""
        await self.connect()
        async with self.pool.acquire() as conn:
            user_count = await conn.fetchval('SELECT COUNT(*) FROM users')
            bot_count = await conn.fetchval('SELECT COUNT(*) FROM bots')
            return user_count, bot_count

    async def total_channels(self):
        """Get total channels count"""
        await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetchval('SELECT COUNT(*) FROM channels')
    
    async def remove_ban(self, id):
        """Remove ban from a user"""
        await self.connect()
        async with self.pool.acquire() as conn:
            ban_status = {
                'is_banned': False,
                'ban_reason': ''
            }
            await conn.execute(
                'UPDATE users SET ban_status = $1 WHERE id = $2',
                json.dumps(ban_status), id
            )
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        """Ban a user"""
        await self.connect()
        async with self.pool.acquire() as conn:
            ban_status = {
                'is_banned': True,
                'ban_reason': ban_reason
            }
            await conn.execute(
                'UPDATE users SET ban_status = $1 WHERE id = $2',
                json.dumps(ban_status), user_id
            )

    async def get_ban_status(self, id):
        """Get a user's ban status"""
        await self.connect()
        default = {
            'is_banned': False,
            'ban_reason': ''
        }
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow('SELECT ban_status FROM users WHERE id = $1', int(id))
            if not user:
                return default
            return json.loads(user['ban_status']) if user['ban_status'] else default

    async def get_all_users(self):
        """Get all users"""
        await self.connect()
        async with self.pool.acquire() as conn:
            users = await conn.fetch('SELECT id, name, ban_status FROM users')
            return [dict(u) for u in users]
    
    async def delete_user(self, user_id):
        """Delete a user"""
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM users WHERE id = $1', int(user_id))
 
    async def get_banned(self):
        """Get all banned users"""
        await self.connect()
        async with self.pool.acquire() as conn:
            users = await conn.fetch("SELECT id FROM users WHERE ban_status->>'is_banned' = 'true'")
            return [u['id'] for u in users]

    async def update_configs(self, id, configs):
        """Update a user's configuration"""
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET configs = $1 WHERE id = $2',
                json.dumps(configs), int(id)
            )
         
    async def get_configs(self, id):
        """Get a user's configuration"""
        await self.connect()
        default = {
            'caption': None,
            'duplicate': True,
            'forward_tag': False,
            'file_size': 0,
            'size_limit': None,
            'extension': None,
            'keywords': None,
            'protect': None,
            'button': None,
            'db_uri': None,
            'filters': {
               'poll': True,
               'text': True,
               'audio': True,
               'voice': True,
               'video': True,
               'photo': True,
               'document': True,
               'animation': True,
               'sticker': True
            }
        }
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow('SELECT configs FROM users WHERE id = $1', int(id))
            if user and user['configs']:
                return json.loads(user['configs'])
            return default
       
    async def add_bot(self, data):
        """Add a bot for a user"""
        await self.connect()
        
        # Check if bot exists for user
        if not await self.is_bot_exist(data['user_id']):
            async with self.pool.acquire() as conn:
                # First remove any existing bots for this user
                await conn.execute('DELETE FROM bots WHERE user_id = $1', data['user_id'])
                
                # Add the new bot
                await conn.execute('''
                    INSERT INTO bots 
                    (user_id, bot_id, name, username, token, is_bot, api_id, api_hash, phone, session_string)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ''', 
                    data['user_id'],
                    data.get('bot_id'),
                    data.get('name'),
                    data.get('username'),
                    data.get('token'),
                    data.get('is_bot', True),
                    data.get('api_id'),
                    data.get('api_hash'),
                    data.get('phone'),
                    data.get('session_string')
                )
    
    async def remove_bot(self, user_id):
        """Remove a user's bot"""
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM bots WHERE user_id = $1', int(user_id))
      
    async def get_bot(self, user_id: int):
        """Get a user's bot"""
        await self.connect()
        async with self.pool.acquire() as conn:
            bot = await conn.fetchrow('SELECT * FROM bots WHERE user_id = $1', user_id)
            if bot:
                return dict(bot)
            return None
                                          
    async def is_bot_exist(self, user_id):
        """Check if a user has a bot"""
        await self.connect()
        async with self.pool.acquire() as conn:
            bot = await conn.fetchrow('SELECT id FROM bots WHERE user_id = $1', user_id)
            return bool(bot)
       
    async def get_filters(self, user_id):
        """Get a user's filters"""
        await self.connect()
        configs = await self.get_configs(int(user_id))
        return configs['filters']
       
    async def update_filter(self, user_id, new_filter):
        """Update a user's filters"""
        await self.connect()
        configs = await self.get_configs(int(user_id))
        configs['filters'] = new_filter
        await self.update_configs(int(user_id), configs)
       
    async def get_db_channels(self, user_id):
        """Get a user's channels"""
        await self.connect()
        async with self.pool.acquire() as conn:
            channels = await conn.fetch(
                'SELECT * FROM channels WHERE user_id = $1 ORDER BY added_on DESC',
                int(user_id)
            )
            return [dict(ch) for ch in channels]
    
    async def get_channel(self, user_id, channel_id):
        """Get a specific channel"""
        await self.connect()
        async with self.pool.acquire() as conn:
            channel = await conn.fetchrow(
                'SELECT * FROM channels WHERE user_id = $1 AND ch_id = $2',
                int(user_id), int(channel_id)
            )
            return dict(channel) if channel else None
        
    async def add_channel(self, data):
        """Add a channel"""
        await self.connect()
        try:
            user_id = int(data.get('user_id', 0))
            ch_id = int(data.get('ch_id', 0))
            
            if not user_id or not ch_id:
                return False
                
            async with self.pool.acquire() as conn:
                # Check if channel already exists
                existing = await conn.fetchrow(
                    'SELECT id FROM channels WHERE user_id = $1 AND ch_id = $2',
                    user_id, ch_id
                )
                
                if not existing:
                    await conn.execute('''
                        INSERT INTO channels (user_id, ch_id, title, type, username)
                        VALUES ($1, $2, $3, $4, $5)
                    ''',
                        user_id,
                        ch_id,
                        data.get('title'),
                        data.get('type'),
                        data.get('username')
                    )
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            return False
        
    async def del_channel(self, user_id, channel_id):
        """Delete a channel"""
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM channels WHERE user_id = $1 AND ch_id = $2',
                int(user_id), int(channel_id)
            )
        
    async def add_frwd(self, user_id):
        """Add a forwarding notification"""
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO notify (user_id) VALUES ($1)',
                int(user_id)
            )
            return True
    
    async def rmve_frwd(self, user_id=0, all=False):
        """Remove forwarding notifications"""
        await self.connect()
        async with self.pool.acquire() as conn:
            if all:
                await conn.execute('DELETE FROM notify')
            else:
                await conn.execute('DELETE FROM notify WHERE user_id = $1', int(user_id))
            return True
    
    async def get_all_frwd(self):
        """Get all forwarding notifications"""
        await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT user_id FROM notify')
    
    # Task management methods for resume functionality
    
    async def save_forwarding_task(self, task_id, data):
        """Save a forwarding task for potential resume later"""
        await self.connect()
        async with self.pool.acquire() as conn:
            # Check if task exists
            existing = await conn.fetchrow('SELECT id FROM tasks WHERE task_id = $1', task_id)
            
            if existing:
                # Update existing task
                await conn.execute('''
                    UPDATE tasks SET
                    user_id = $1,
                    from_chat = $2,
                    to_chat = $3,
                    bot_details = $4,
                    last_forwarded_msg_id = $5,
                    total_count = $6,
                    offset = $7,
                    configs = $8,
                    status = $9,
                    created_at = $10
                    WHERE task_id = $11
                ''',
                    data.get('user_id'),
                    str(data.get('from_chat')),
                    str(data.get('to_chat')),
                    json.dumps(data.get('bot_details', {})),
                    data.get('last_forwarded_msg_id', 0),
                    data.get('total_count', 0),
                    data.get('offset', 0),
                    json.dumps(data.get('configs', {})),
                    data.get('status', 'active'),
                    data.get('created_at', 0),
                    task_id
                )
            else:
                # Create new task
                await conn.execute('''
                    INSERT INTO tasks
                    (task_id, user_id, from_chat, to_chat, bot_details, last_forwarded_msg_id,
                    total_count, offset, configs, status, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ''',
                    task_id,
                    data.get('user_id'),
                    str(data.get('from_chat')),
                    str(data.get('to_chat')),
                    json.dumps(data.get('bot_details', {})),
                    data.get('last_forwarded_msg_id', 0),
                    data.get('total_count', 0),
                    data.get('offset', 0),
                    json.dumps(data.get('configs', {})),
                    data.get('status', 'active'),
                    data.get('created_at', 0)
                )
                
            return True
    
    async def get_task(self, task_id):
        """Get a task by its ID"""
        await self.connect()
        async with self.pool.acquire() as conn:
            task = await conn.fetchrow('SELECT * FROM tasks WHERE task_id = $1', task_id)
            
            if not task:
                return None
                
            # Convert to dict and parse JSON fields
            task_dict = dict(task)
            task_dict['bot_details'] = json.loads(task_dict['bot_details']) if task_dict['bot_details'] else {}
            task_dict['configs'] = json.loads(task_dict['configs']) if task_dict['configs'] else {}
            
            return task_dict
    
    async def get_user_active_tasks(self, user_id):
        """Get all active tasks for a user"""
        await self.connect()
        async with self.pool.acquire() as conn:
            tasks = await conn.fetch(
                "SELECT * FROM tasks WHERE user_id = $1 AND status IN ('active', 'paused', 'failed') ORDER BY created_at DESC",
                int(user_id)
            )
            
            result = []
            for task in tasks:
                task_dict = dict(task)
                task_dict['bot_details'] = json.loads(task_dict['bot_details']) if task_dict['bot_details'] else {}
                task_dict['configs'] = json.loads(task_dict['configs']) if task_dict['configs'] else {}
                result.append(task_dict)
                
            return result
    
    async def update_task_status(self, task_id, status, last_msg_id=None):
        """Update task status and optionally the last forwarded message ID"""
        await self.connect()
        async with self.pool.acquire() as conn:
            if last_msg_id is not None:
                await conn.execute(
                    'UPDATE tasks SET status = $1, last_forwarded_msg_id = $2 WHERE task_id = $3',
                    status, last_msg_id, task_id
                )
            else:
                await conn.execute(
                    'UPDATE tasks SET status = $1 WHERE task_id = $2',
                    status, task_id
                )
                
            return True
    
    async def delete_task(self, task_id):
        """Delete a task"""
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM tasks WHERE task_id = $1', task_id)
            return True

# Initialize database
db = Database(Config.DATABASE_URI, Config.DATABASE_NAME)

# Function for compatibility with the MongoDB version
async def mongodb_version():
    """Mock MongoDB version function for compatibility"""
    await db.connect()
    return "PostgreSQL"