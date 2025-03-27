# Advanced Telegram Forwarder Bot
# Improved by Replit AI

import time as tm
import logging
from database import db 
from .test import parse_buttons

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

STATUS = {}

class STS:
    """Tracking class for forwarding status"""
    def __init__(self, id):
        self.id = id
        self.data = STATUS
    
    def verify(self):
        """Check if status exists for this ID"""
        return self.data.get(self.id)
    
    def store(self, From, to, skip, limit):
        """Initialize or update status data"""
        self.data[self.id] = {
            "FROM": From, 
            'TO': to, 
            'total_files': 0, 
            'skip': skip, 
            'limit': limit,
            'fetched': skip, 
            'filtered': 0, 
            'deleted': 0, 
            'duplicate': 0, 
            'total': limit, 
            'start': 0
        }
        self.get(full=True)
        return STS(self.id)
        
    def get(self, value=None, full=False):
        """Get a value or all values from status"""
        values = self.data.get(self.id)
        if not values:
            return None if value else {}
        
        if not full:
           return values.get(value)
        
        # Set all values as attributes for easier access
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def add(self, key=None, value=1, time=False):
        """Increment a counter or set the start time"""
        if time:
          return self.data[self.id].update({'start': tm.time()})
        
        # Only add if the key exists
        if key in self.data[self.id]:
            self.data[self.id].update({key: self.get(key) + value})
    
    def divide(self, no, by):
        """Safe division with fallback to 1 if divisor is 0"""
        by = 1 if int(by) == 0 else by 
        return int(no) / by 
    
    async def get_data(self, user_id):
        """Get all necessary data for forwarding"""
        try:
            bot = await db.get_bot(user_id)
            k, filters = self, await db.get_filters(user_id)
            size, configs = None, await db.get_configs(user_id)
            
            if configs['duplicate']:
               duplicate = [configs['db_uri'], self.TO]
            else:
               duplicate = False
               
            button = parse_buttons(configs['button'] if configs['button'] else '')
            
            if configs['file_size'] != 0:
                size = [configs['file_size'], configs['size_limit']]
                
            return bot, configs['caption'], configs['forward_tag'], {
                'chat_id': k.FROM, 
                'limit': k.limit, 
                'offset': k.skip, 
                'filters': filters,
                'keywords': configs['keywords'], 
                'media_size': size, 
                'extensions': configs['extension'], 
                'skip_duplicate': duplicate
            }, configs['protect'], button
            
        except Exception as e:
            logger.error(f"Error in get_data: {str(e)}")
            return None, None, False, {}, False, None
            
    async def load_from_task(self, task_id):
        """Load status data from a saved task"""
        try:
            task = await db.get_task(task_id)
            if not task:
                return False
                
            self.store(
                task["from_chat"],
                task["to_chat"],
                task.get("last_forwarded_msg_id", 0),
                task["total_count"]
            )
            
            # Set task-specific values
            self.data[self.id].update({
                'task_id': task_id,
                'bot_details': task.get("bot_details", {}),
                'configs': task.get("configs", {})
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading task {task_id}: {str(e)}")
            return False
            
    def update_last_message(self, msg_id):
        """Update the last forwarded message ID"""
        if self.id in self.data:
            self.data[self.id]['last_message_id'] = msg_id
            
    def get_progress(self):
        """Calculate progress percentage"""
        if not self.verify():
            return 0
            
        total = self.get('total')
        fetched = self.get('fetched')
        
        if not total or total == 0:
            return 0
            
        return int((fetched / total) * 100)