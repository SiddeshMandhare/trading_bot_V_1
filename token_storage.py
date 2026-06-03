# token_storage.py
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict

class TokenStorage:
    """Persistent token storage with file-based caching"""
    
    def __init__(self, client_code: str, storage_file: str = "token_cache.json"):
        self.client_code = client_code
        self.storage_file = storage_file
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        """Create storage file if it doesn't exist"""
        if not os.path.exists(self.storage_file):
            self._save_token_data({})
    
    def _load_token_data(self) -> Dict:
        """Load token data from file"""
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_token_data(self, data: Dict):
        """Save token data to file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save token cache: {e}")
    
    def get_token(self) -> Optional[str]:
        """Get valid token from storage if it exists and hasn't expired"""
        data = self._load_token_data()
        
        client_data = data.get(self.client_code, {})
        token = client_data.get('access_token')
        expires_at = client_data.get('expires_at', 0)
        generated_at = client_data.get('generated_at', 0)
        
        current_time = time.time()
        
        # Check if token exists and hasn't expired
        if token and expires_at > current_time:
            expires_in = expires_at - current_time
            print(f"📦 Found cached token for {self.client_code}")
            print(f"   Valid for: {expires_in/60:.1f} minutes ({expires_in:.0f} seconds)")
            print(f"   Generated at: {datetime.fromtimestamp(generated_at).strftime('%H:%M:%S')}")
            print(f"   Expires at: {datetime.fromtimestamp(expires_at).strftime('%H:%M:%S')}")
            return token
        
        if token and expires_at <= current_time:
            print(f"⚠️ Cached token expired at {datetime.fromtimestamp(expires_at).strftime('%H:%M:%S')}")
        
        return None
    
    def save_token(self, access_token: str, expiry_seconds: int = 82800) -> bool:
        """
        Save token to storage
        expiry_seconds: Token validity in seconds (default 23 hours = 82800s, less than 24h)
        """
        current_time = time.time()
        expires_at = current_time + expiry_seconds
        
        data = self._load_token_data()
        
        data[self.client_code] = {
            'access_token': access_token,
            'expires_at': expires_at,
            'generated_at': current_time,
            'expires_in_seconds': expiry_seconds,
            'cached_at': datetime.now().isoformat()
        }
        
        self._save_token_data(data)
        print(f"💾 Token saved to cache (valid until {datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')})")
        return True
    
    def clear_token(self):
        """Clear stored token for this client"""
        data = self._load_token_data()
        if self.client_code in data:
            del data[self.client_code]
            self._save_token_data(data)
            print(f"🗑️ Cleared cached token for {self.client_code}")
    
    def get_token_info(self) -> Optional[Dict]:
        """Get information about the stored token"""
        data = self._load_token_data()
        client_data = data.get(self.client_code, {})
        
        if not client_data:
            return None
        
        current_time = time.time()
        expires_at = client_data.get('expires_at', 0)
        
        return {
            'has_token': bool(client_data.get('access_token')),
            'expires_at': datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S') if expires_at else None,
            'is_valid': expires_at > current_time if expires_at else False,
            'expires_in_seconds': max(0, expires_at - current_time) if expires_at else 0,
            'generated_at': datetime.fromtimestamp(client_data.get('generated_at', 0)).strftime('%Y-%m-%d %H:%M:%S') if client_data.get('generated_at') else None
        }
    
    def is_token_valid(self) -> bool:
        """Check if stored token is still valid"""
        token_info = self.get_token_info()
        return token_info and token_info['is_valid'] if token_info else False