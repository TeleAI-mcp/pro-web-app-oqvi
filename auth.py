"""
Authentication module for Pro Web App Oqvi.
"""

class AuthManager:
    """Handles authentication and authorization."""
    
    def __init__(self):
        self.users = {}
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        if username in self.users:
            return self.users[username] == password
        return False
    
    def register(self, username: str, password: str) -> bool:
        """Register a new user."""
        if username not in self.users:
            self.users[username] = password
            return True
        return False