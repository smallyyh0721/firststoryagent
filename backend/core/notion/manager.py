"""
Singleton Notion Client Manager with Retry Logic
"""

import os
import time
from typing import Optional
from notion_client import Client, APIResponseError
from dotenv import load_dotenv

load_dotenv()


class NotionClientManager:
    """Singleton manager for Notion client with retry logic"""
    
    _instance = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> Client:
        """Get or create Notion client"""
        if self._client is None:
            self._create_client()
        return self._client
    
    def _create_client(self):
        """Create a new Notion client"""
        token = os.getenv("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN must be set in environment")
        
        # Create client
        self._client = Client(auth=token)
    
    def reset_client(self):
        """Reset the client (useful after connection errors)"""
        self._client = None
        self._create_client()
    
    def retry_request(self, func, max_retries: int = 3, initial_delay: float = 1.0):
        """
        Retry a request with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        import httpx
        import socket
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except (APIResponseError, ConnectionError, OSError, httpx.ConnectError, httpx.TimeoutException, socket.error) as e:
                last_exception = e
                
                if attempt < max_retries - 1:
                    # Reset client connection for certain errors
                    if isinstance(e, (ConnectionError, OSError, httpx.ConnectError, socket.error)):
                        print("Resetting Notion client connection...")
                        self.reset_client()
                    
                    # Exponential backoff: 1s, 2s, 4s, ...
                    delay = initial_delay * (2 ** attempt)
                    print(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    print(f"All {max_retries} retry attempts failed")
                    raise
            except Exception as e:
                # Don't retry non-transient errors
                raise
        
        if last_exception:
            raise last_exception


# Global singleton instance
notion_manager = NotionClientManager()