import os
import json
import logging

logger = logging.getLogger(__name__)

class Storage:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_user_file_path(self, phone):
        """Get the file path for a user's data."""
        return os.path.join(self.data_dir, f"{phone}.json")
    
    def user_exists(self, phone):
        """Check if a user exists in storage."""
        return os.path.exists(self.get_user_file_path(phone))
    
    def create_user(self, phone, api_id, api_hash):
        """Create a new user in storage."""
        user_data = {
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash,
            'sources': {},
            'destinations': {},
            'forwarding_progress': {}
        }
        
        self.save_user_data(phone, user_data)
        
        return user_data
    
    def get_user_data(self, phone):
        """Get a user's data from storage."""
        file_path = self.get_user_file_path(phone)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading user data for {phone}: {str(e)}")
            return None
    
    def save_user_data(self, phone, user_data):
        """Save a user's data to storage."""
        file_path = self.get_user_file_path(phone)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(user_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving user data for {phone}: {str(e)}")
            return False
    
    def update_user(self, phone, updates):
        """Update a user's data in storage."""
        user_data = self.get_user_data(phone)
        
        if not user_data:
            return False
        
        # Update the user data
        for key, value in updates.items():
            user_data[key] = value
        
        # Save the updated data
        return self.save_user_data(phone, user_data)
    
    def add_source(self, phone, source):
        """Add a source to a user's data."""
        user_data = self.get_user_data(phone)
        
        if not user_data:
            return False
        
        # Add the source
        user_data.setdefault('sources', {})[source['id']] = source
        
        # Save the updated data
        return self.save_user_data(phone, user_data)
    
    def add_destination(self, phone, destination):
        """Add a destination to a user's data."""
        user_data = self.get_user_data(phone)
        
        if not user_data:
            return False
        
        # Add the destination
        user_data.setdefault('destinations', {})[destination['id']] = destination
        
        # Save the updated data
        return self.save_user_data(phone, user_data)
    
    def delete_user(self, phone):
        """Delete a user's data from storage."""
        file_path = self.get_user_file_path(phone)
        
        if not os.path.exists(file_path):
            return True
        
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting user data for {phone}: {str(e)}")
            return False
