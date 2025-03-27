import time
import logging
import asyncio
import threading
from telethon import errors
from datetime import datetime

logger = logging.getLogger(__name__)

class Forwarder:
    def __init__(self, client, storage, phone):
        self.client = client
        self.storage = storage
        self.phone = phone
        self.is_running = False
        self.should_cancel = False
        self.lock = threading.Lock()
        self.progress = {
            'source_id': None,
            'destination_id': None,
            'total_messages': 0,
            'forwarded_messages': 0,
            'last_forwarded_id': None,
            'status': 'idle',
            'error': None
        }

    def update_progress(self, **kwargs):
        """Update the progress data with thread safety."""
        with self.lock:
            for key, value in kwargs.items():
                self.progress[key] = value
            
            # Update the progress in the storage
            user_data = self.storage.get_user_data(self.phone)
            forwarding_progress = user_data.get('forwarding_progress', {})
            
            if self.progress['source_id'] and self.progress['destination_id']:
                key = f"{self.progress['source_id']}_{self.progress['destination_id']}"
                forwarding_progress[key] = self.progress.copy()
                
                # Update the storage
                self.storage.update_user(self.phone, {'forwarding_progress': forwarding_progress})

    def forward_messages(self, source_entity_id, destination_entity_id, source_id, destination_id, last_message_id=None):
        """Forward messages from source to destination."""
        # Check if already running
        if self.is_running:
            logger.warning(f"Forwarder already running for {self.phone}")
            return
        
        self.is_running = True
        self.should_cancel = False
        
        # Initialize progress
        self.update_progress(
            source_id=source_id,
            destination_id=destination_id,
            total_messages=0,
            forwarded_messages=0,
            last_forwarded_id=None,
            status='running',
            error=None
        )
        
        try:
            # Get previous progress if available
            user_data = self.storage.get_user_data(self.phone)
            forwarding_progress = user_data.get('forwarding_progress', {})
            key = f"{source_id}_{destination_id}"
            
            prev_progress = forwarding_progress.get(key, {})
            last_forwarded_id = prev_progress.get('last_forwarded_id')
            
            # If we're resuming and have a last forwarded ID, use that
            if last_forwarded_id and prev_progress.get('status') != 'completed':
                start_msg_id = last_forwarded_id + 1
            else:
                # Otherwise start from the beginning (or the specified last message)
                start_msg_id = 1
            
            logger.info(f"Starting forwarding from {source_entity_id} to {destination_entity_id} for {self.phone}")
            logger.info(f"Starting from message ID: {start_msg_id}")
            
            # Run the forwarding in the event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._forward_messages_async(
                    source_entity_id, 
                    destination_entity_id, 
                    start_msg_id, 
                    last_message_id
                ))
            finally:
                loop.close()
                
            if self.should_cancel:
                self.update_progress(status='cancelled')
                logger.info(f"Forwarding cancelled for {self.phone}")
            else:
                self.update_progress(status='completed')
                logger.info(f"Forwarding completed for {self.phone}")
        except Exception as e:
            logger.error(f"Error in forward_messages for {self.phone}: {str(e)}")
            self.update_progress(status='failed', error=str(e))
        finally:
            self.is_running = False

    async def _forward_messages_async(self, source_entity_id, destination_entity_id, start_msg_id, last_message_id=None):
        """Async implementation of message forwarding."""
        try:
            # Get the source entity
            source_entity = await self.client.get_entity(source_entity_id)
            
            # Get the destination entity
            destination_entity = await self.client.get_entity(destination_entity_id)
            
            # Get messages from the source
            messages = []
            offset_id = 0
            limit = 100
            total_messages = 0
            
            # If last_message_id is specified, we need to get all messages up to that ID
            end_msg_id = last_message_id if last_message_id else 0
            
            # First, count the total number of messages to forward
            while True:
                history = await self.client.get_messages(
                    source_entity,
                    limit=limit,
                    offset_id=offset_id,
                    min_id=start_msg_id - 1,  # -1 because we want to include start_msg_id
                    max_id=end_msg_id if end_msg_id > 0 else None
                )
                
                if not history:
                    break
                
                total_messages += len(history)
                offset_id = history[-1].id
                
                if len(history) < limit:
                    break
            
            # Update the total count
            self.update_progress(total_messages=total_messages)
            
            # Reset for actual forwarding
            offset_id = 0
            forwarded_count = 0
            
            while True:
                if self.should_cancel:
                    break
                
                history = await self.client.get_messages(
                    source_entity,
                    limit=limit,
                    offset_id=offset_id,
                    min_id=start_msg_id - 1,  # -1 because we want to include start_msg_id
                    max_id=end_msg_id if end_msg_id > 0 else None
                )
                
                if not history:
                    break
                
                for message in history:
                    if self.should_cancel:
                        break
                    
                    try:
                        # Forward the message
                        await self.client.forward_messages(
                            destination_entity,
                            message
                        )
                        
                        # Update progress
                        forwarded_count += 1
                        self.update_progress(
                            forwarded_messages=forwarded_count,
                            last_forwarded_id=message.id
                        )
                        
                        # Avoid flooding
                        await asyncio.sleep(2)
                    except errors.FloodWaitError as e:
                        logger.warning(f"Flood wait error: {e.seconds}s")
                        # Wait the required time
                        await asyncio.sleep(e.seconds)
                        # Retry this message
                        forwarded_count -= 1
                    except Exception as e:
                        logger.error(f"Error forwarding message {message.id}: {str(e)}")
                        # Continue with the next message
                
                offset_id = history[-1].id
                
                if len(history) < limit:
                    break
        except Exception as e:
            logger.error(f"Error in _forward_messages_async: {str(e)}")
            raise

    def cancel_forwarding(self):
        """Cancel the current forwarding operation."""
        self.should_cancel = True
        logger.info(f"Cancelling forwarding for {self.phone}")
