# auth_service.py - WITH PERSISTENT TOKEN STORAGE
import pyotp
import requests
import time
from typing import Optional
from Dhan_Tradehull_V4 import Tradehull  # FIXED IMPORT
from token_storage import TokenStorage
from dhanhq import dhanhq

# Global token storage instance
_token_storage = None

def get_token_storage(client_code: str) -> TokenStorage:
    """Get or create token storage instance"""
    global _token_storage
    if _token_storage is None or _token_storage.client_code != client_code:
        _token_storage = TokenStorage(client_code)
    return _token_storage


def generate_access_token(client_code: str, pin: str, totp_secret: str, force_new: bool = False) -> Optional[str]:
    """Generate a fresh access token, checking cache first"""
    
    # Check cache first (unless force_new is True)
    if not force_new:
        storage = get_token_storage(client_code)
        cached_token = storage.get_token()
        if cached_token:
            print(f"📦 Using cached token")
            return cached_token
    
    # Rate limiting protection
    time_since_last_gen = getattr(generate_access_token, '_last_gen_time', 0)
    current_time = time.time()
    
    if current_time - time_since_last_gen < 120 and not force_new:
        wait_time = 120 - (current_time - time_since_last_gen)
        print(f"⏳ Rate limit: Please wait {wait_time:.0f} seconds")
        return None
    
    try:
        totp = pyotp.TOTP(totp_secret)
        current_totp = totp.now()
        
        print(f"🔄 Generating NEW access token for {client_code}...")
        print(f"   TOTP Code: {current_totp}")
        
        url = f"https://auth.dhan.co/app/generateAccessToken?dhanClientId={client_code}&pin={pin}&totp={current_totp}"
        
        response = requests.post(url, timeout=30)
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for error message
            if 'message' in data and data.get('status') == 'error':
                print(f"❌ API Error: {data.get('message')}")
                if "once every 2 minutes" in data.get('message', ''):
                    print(f"   Rate limited! Try again in 2 minutes")
                return None
            
            # Look for accessToken (capital T) or access_token
            access_token = data.get('accessToken') or data.get('access_token')
            if access_token:
                # Update last generation time
                generate_access_token._last_gen_time = current_time
                
                # Save to persistent storage (23 hours validity)
                storage = get_token_storage(client_code)
                storage.save_token(access_token, expiry_seconds=82800)
                
                print(f"✅ Access token generated successfully")
                return access_token
            else:
                print(f"❌ No access token in response")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None


def create_tradehull_with_totp(client_code: str, pin: str, totp_secret: str, retries: int = 3) -> Optional[Tradehull]:
    """Create a Tradehull instance using TOTP authentication"""
    
    storage = get_token_storage(client_code)
    
    for attempt in range(retries):
        try:
            force_new = (attempt > 0) or not storage.is_token_valid()
            access_token = generate_access_token(client_code, pin, totp_secret, force_new=force_new)
            
            if not access_token:
                print(f"⚠️ No token available, waiting before retry...")
                time.sleep(5)
                continue
            
            print(f"🔐 Creating Tradehull instance...")
            tsl = Tradehull(client_code, access_token)
            
            if not hasattr(tsl, 'dhan_client_id'):
                tsl.dhan_client_id = client_code
            
            print(f"✅ Authentication successful!")
            return tsl
                    
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(5)
    
    print(f"❌ Failed to authenticate {client_code} after {retries} attempts")
    return None


def get_token_status(client_code: str) -> dict:
    """Get status of stored token"""
    storage = get_token_storage(client_code)
    return storage.get_token_info() or {'has_token': False}
