import os
import json
import uuid
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from storage import Storage
from forwarder import Forwarder

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.clients = {}  # Maps phone numbers to client instances
        self.storage = Storage()
        self.forwarders = {}  # Maps phone numbers to forwarder instances
        self.active_tasks = {}  # Maps phone numbers to active forwarding tasks
        
        # Create the sessions directory if it doesn't exist
        if not os.path.exists('sessions'):
            os.makedirs('sessions')

    def initialize_bot(self, phone, api_id, api_hash):
        """Initialize a Telegram client for a user."""
        try:
            # Create the client
            client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
            
            # Start the client without connecting
            client.connect()
            
            # Check if the user is already authorized
            if client.is_user_authorized():
                # Save the client instance
                self.clients[phone] = client
                
                # Initialize user data if it doesn't exist
                if not self.storage.user_exists(phone):
                    self.storage.create_user(phone, api_id, api_hash)
                
                # Initialize the forwarder for this user
                self.forwarders[phone] = Forwarder(client, self.storage, phone)
                
                return {"success": True, "needs_code": False}
            else:
                # User is not authorized, send the code
                client.send_code_request(phone)
                
                # Save the client instance
                self.clients[phone] = client
                
                # Initialize user data if it doesn't exist
                if not self.storage.user_exists(phone):
                    self.storage.create_user(phone, api_id, api_hash)
                
                return {"success": True, "needs_code": True}
        except Exception as e:
            logger.error(f"Error initializing bot for {phone}: {str(e)}")
            if phone in self.clients:
                self.clients[phone].disconnect()
                del self.clients[phone]
            raise

    def submit_code(self, phone, code):
        """Submit the verification code."""
        if phone not in self.clients:
            return {"success": False, "error": "Client not initialized"}
        
        client = self.clients[phone]
        
        try:
            # Sign in with the code
            client.sign_in(phone, code)
            
            # Initialize the forwarder for this user
            self.forwarders[phone] = Forwarder(client, self.storage, phone)
            
            return {"success": True}
        except SessionPasswordNeededError:
            # 2FA is enabled
            return {"success": False, "error": "Two-factor authentication is enabled. Please use the official Telegram app for logging in."}
        except Exception as e:
            logger.error(f"Error signing in with code for {phone}: {str(e)}")
            return {"success": False, "error": str(e)}

    def add_source(self, phone, source_link):
        """Add a new source channel/group."""
        if phone not in self.clients:
            return {"success": False, "error": "Client not initialized"}
        
        client = self.clients[phone]
        
        try:
            # Join the source channel/group
            entity = None
            try:
                # Try to resolve the link as a public channel/group
                entity = client.loop.run_until_complete(client.get_entity(source_link))
            except:
                # Try to resolve the link as a private channel/group
                if 'joinchat' in source_link:
                    # Extract the hash from the invite link
                    invite_hash = source_link.split('/')[-1]
                    entity = client.loop.run_until_complete(
                        client(ImportChatInviteRequest(invite_hash))
                    ).chats[0]
                else:
                    # Try to join as a public channel
                    entity = client.loop.run_until_complete(
                        client(JoinChannelRequest(source_link))
                    )
            
            # Get the entity ID and title
            entity_id = entity.id
            entity_title = getattr(entity, 'title', source_link)
            
            # Add the source to storage
            source_id = str(uuid.uuid4())
            self.storage.add_source(phone, {
                'id': source_id,
                'link': source_link,
                'title': entity_title,
                'entity_id': entity_id,
                'last_message_id': None
            })
            
            return {
                "success": True,
                "source": {
                    'id': source_id,
                    'link': source_link,
                    'title': entity_title,
                    'entity_id': entity_id,
                    'last_message_id': None
                }
            }
        except Exception as e:
            logger.error(f"Error adding source for {phone}: {str(e)}")
            return {"success": False, "error": str(e)}

    def add_destination(self, phone, destination_link):
        """Add a new destination channel/group."""
        if phone not in self.clients:
            return {"success": False, "error": "Client not initialized"}
        
        client = self.clients[phone]
        
        try:
            # Join the destination channel/group
            entity = None
            try:
                # Try to resolve the link as a public channel/group
                entity = client.loop.run_until_complete(client.get_entity(destination_link))
            except:
                # Try to resolve the link as a private channel/group
                if 'joinchat' in destination_link:
                    # Extract the hash from the invite link
                    invite_hash = destination_link.split('/')[-1]
                    entity = client.loop.run_until_complete(
                        client(ImportChatInviteRequest(invite_hash))
                    ).chats[0]
                else:
                    # Try to join as a public channel
                    entity = client.loop.run_until_complete(
                        client(JoinChannelRequest(destination_link))
                    )
            
            # Get the entity ID and title
            entity_id = entity.id
            entity_title = getattr(entity, 'title', destination_link)
            
            # Add the destination to storage
            destination_id = str(uuid.uuid4())
            self.storage.add_destination(phone, {
                'id': destination_id,
                'link': destination_link,
                'title': entity_title,
                'entity_id': entity_id
            })
            
            return {
                "success": True,
                "destination": {
                    'id': destination_id,
                    'link': destination_link,
                    'title': entity_title,
                    'entity_id': entity_id
                }
            }
        except Exception as e:
            logger.error(f"Error adding destination for {phone}: {str(e)}")
            return {"success": False, "error": str(e)}

    def set_last_message(self, phone, source_id, last_message_link):
        """Set the last message link for a source."""
        if phone not in self.clients:
            return {"success": False, "error": "Client not initialized"}
        
        client = self.clients[phone]
        
        try:
            # Extract the message ID from the link
            # Format: https://t.me/c/1234567890/123
            parts = last_message_link.rstrip('/').split('/')
            message_id = int(parts[-1])
            
            # Update the source in storage
            sources = self.storage.get_user_data(phone).get('sources', {})
            if source_id not in sources:
                return {"success": False, "error": "Source not found"}
            
            sources[source_id]['last_message_id'] = message_id
            self.storage.update_user(phone, {'sources': sources})
            
            return {"success": True, "message_id": message_id}
        except Exception as e:
            logger.error(f"Error setting last message for {phone}: {str(e)}")
            return {"success": False, "error": str(e)}

    def start_forwarding(self, phone, source_id, destination_id):
        """Start forwarding messages from a source to a destination."""
        if phone not in self.clients or phone not in self.forwarders:
            logger.error(f"Client or forwarder not initialized for {phone}")
            return
        
        try:
            # Get the source and destination data
            user_data = self.storage.get_user_data(phone)
            sources = user_data.get('sources', {})
            destinations = user_data.get('destinations', {})
            
            if source_id not in sources:
                logger.error(f"Source {source_id} not found for {phone}")
                return
            
            if destination_id not in destinations:
                logger.error(f"Destination {destination_id} not found for {phone}")
                return
            
            source = sources[source_id]
            destination = destinations[destination_id]
            
            # Store the active task
            self.active_tasks[phone] = {
                'source_id': source_id,
                'destination_id': destination_id,
                'status': 'running',
                'total_messages': 0,
                'forwarded_messages': 0,
                'last_forwarded_id': None
            }
            
            # Start forwarding
            self.forwarders[phone].forward_messages(
                source['entity_id'],
                destination['entity_id'],
                source_id,
                destination_id,
                source.get('last_message_id')
            )
        except Exception as e:
            logger.error(f"Error starting forwarding for {phone}: {str(e)}")
            if phone in self.active_tasks:
                self.active_tasks[phone]['status'] = 'failed'
                self.active_tasks[phone]['error'] = str(e)

    def cancel_forwarding(self, phone):
        """Cancel an active forwarding task."""
        if phone not in self.forwarders:
            return {"success": False, "error": "Forwarder not initialized"}
        
        try:
            # Cancel the forwarding
            self.forwarders[phone].cancel_forwarding()
            
            # Update the active task
            if phone in self.active_tasks:
                self.active_tasks[phone]['status'] = 'cancelled'
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Error cancelling forwarding for {phone}: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_forwarding_status(self, phone):
        """Get the status of the current forwarding task."""
        if phone not in self.active_tasks:
            return {
                'active': False,
                'status': 'idle',
                'progress': 0
            }
        
        task = self.active_tasks[phone]
        progress = 0
        if task['total_messages'] > 0:
            progress = (task['forwarded_messages'] / task['total_messages']) * 100
        
        return {
            'active': task['status'] == 'running',
            'status': task['status'],
            'source_id': task['source_id'],
            'destination_id': task['destination_id'],
            'total_messages': task['total_messages'],
            'forwarded_messages': task['forwarded_messages'],
            'progress': round(progress, 2),
            'error': task.get('error')
        }

    def get_active_task(self, phone):
        """Get the active task for a user."""
        return self.active_tasks.get(phone)

    def get_user_data(self, phone):
        """Get the user data from storage."""
        return self.storage.get_user_data(phone)

    def logout_user(self, phone):
        """Logout a user and clean up resources."""
        try:
            # Disconnect the client
            if phone in self.clients:
                self.clients[phone].disconnect()
                del self.clients[phone]
            
            # Remove the forwarder
            if phone in self.forwarders:
                del self.forwarders[phone]
            
            # Remove the active task
            if phone in self.active_tasks:
                del self.active_tasks[phone]
            
            return True
        except Exception as e:
            logger.error(f"Error logging out {phone}: {str(e)}")
            return False

    def delete_source(self, phone, source_id):
        """Delete a source."""
        try:
            user_data = self.storage.get_user_data(phone)
            sources = user_data.get('sources', {})
            
            if source_id not in sources:
                return {"success": False, "error": "Source not found"}
            
            # Check if the source is being used in an active task
            if phone in self.active_tasks and self.active_tasks[phone]['source_id'] == source_id:
                return {"success": False, "error": "Cannot delete a source that is being used in an active task"}
            
            # Delete the source
            del sources[source_id]
            self.storage.update_user(phone, {'sources': sources})
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting source for {phone}: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_destination(self, phone, destination_id):
        """Delete a destination."""
        try:
            user_data = self.storage.get_user_data(phone)
            destinations = user_data.get('destinations', {})
            
            if destination_id not in destinations:
                return {"success": False, "error": "Destination not found"}
            
            # Check if the destination is being used in an active task
            if phone in self.active_tasks and self.active_tasks[phone]['destination_id'] == destination_id:
                return {"success": False, "error": "Cannot delete a destination that is being used in an active task"}
            
            # Delete the destination
            del destinations[destination_id]
            self.storage.update_user(phone, {'destinations': destinations})
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting destination for {phone}: {str(e)}")
            return {"success": False, "error": str(e)}
