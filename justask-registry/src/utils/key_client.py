"""
Python client for Supabase Edge Functions
Provides secure API key retrieval and usage logging
"""

import requests
import os
from typing import Optional
import json

class KeyClient:
    """Client for accessing API keys through Supabase Edge Functions"""
    
    def __init__(self):
        self.base_url = "https://atilxlecbaqcksnrgzav.supabase.co/functions/v1"
        self.anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF0aWx4bGVjYmFxY2tzbnJnemF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzOTY5MTYsImV4cCI6MjA2Nzk3MjkxNn0.sYRFyQIEzZMlgg5RtHTXDSpvxl-KrJ8E7U3_UroIJog"
        # Get internal API key from environment
        internal_key = os.getenv('INTERNAL_API_KEY')
            
        self.headers = {
            "Authorization": f"Bearer {self.anon_key}",
            "Content-Type": "application/json"
        }
        
        if internal_key:
            self.headers["X-API-Key"] = internal_key
        self.timeout = 10  # seconds
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Retrieve API key for specified provider
        
        Args:
            provider: One of 'openrouter', 'google', 'groq'
            
        Returns:
            API key string if successful, None if failed
        """
        try:
            response = requests.post(
                f"{self.base_url}/get-api-key",
                headers=self.headers,
                json={"provider": provider},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("key")
            else:
                print(f"Failed to get API key for {provider}: {response.status_code}")
                if response.text:
                    print(f"Error: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error getting API key for {provider}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return None
    
    def log_usage(self, provider: str, limit_type: str, usage_count: int = 1) -> bool:
        """
        Log API usage for rate limit tracking
        
        Args:
            provider: One of 'openrouter', 'google', 'groq'  
            limit_type: One of 'rpm', 'rpd', 'tpm', 'tpd', 'ash', 'asd'
            usage_count: Number of requests/tokens used (default: 1)
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/log-usage",
                headers=self.headers,
                json={
                    "provider": provider,
                    "limit_type": limit_type,
                    "usage_count": usage_count
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check for rate limit warnings
                if data.get("warning"):
                    print(f"⚠️  Rate limit warning: {data['warning']}")
                return True
            else:
                print(f"Failed to log usage for {provider}: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Network error logging usage for {provider}: {str(e)}")
            return False
    
    def get_notifications(self) -> Optional[list]:
        """
        Get current notifications
        
        Returns:
            List of notifications if successful, None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/notifications?action=list",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("notifications", [])
            else:
                print(f"Failed to get notifications: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error getting notifications: {str(e)}")
            return None


# Global client instance
_client = None

def get_api_key(provider: str) -> Optional[str]:
    """
    Convenience function to get API key
    
    Args:
        provider: One of 'openrouter', 'google', 'groq'
        
    Returns:
        API key string if successful, None if failed
    """
    global _client
    if _client is None:
        _client = KeyClient()
    
    return _client.get_api_key(provider)

def log_usage(provider: str, limit_type: str, usage_count: int = 1) -> bool:
    """
    Convenience function to log usage
    
    Args:
        provider: One of 'openrouter', 'google', 'groq'
        limit_type: One of 'rpm', 'rpd', 'tpm', 'tpd', 'ash', 'asd' 
        usage_count: Number of requests/tokens used (default: 1)
        
    Returns:
        True if logged successfully, False otherwise
    """
    global _client
    if _client is None:
        _client = KeyClient()
    
    return _client.log_usage(provider, limit_type, usage_count)

def get_notifications() -> Optional[list]:
    """
    Convenience function to get notifications
    
    Returns:
        List of notifications if successful, None if failed
    """
    global _client
    if _client is None:
        _client = KeyClient()
    
    return _client.get_notifications()

# Test function
if __name__ == "__main__":
    print("Testing KeyClient...")
    
    # Test getting an API key
    key = get_api_key("openrouter")
    if key:
        print(f"✅ Retrieved OpenRouter key: {key[:20]}...")
    else:
        print("❌ Failed to retrieve OpenRouter key")
    
    # Test logging usage
    success = log_usage("openrouter", "rpm", 1)
    if success:
        print("✅ Usage logging successful")
    else:
        print("❌ Usage logging failed")
    
    # Test notifications
    notifications = get_notifications()
    if notifications is not None:
        print(f"✅ Retrieved {len(notifications)} notifications")
    else:
        print("❌ Failed to retrieve notifications")