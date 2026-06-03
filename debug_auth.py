# debug_auth.py
import pyotp
import requests
from config import Config

print("="*50)
print("DEBUGGING TOTP AUTHENTICATION")
print("="*50)

# Step 1: Generate TOTP
print(f"\n1. Client Code: {Config.CLIENT_CODE}")
print(f"   PIN: {Config.PIN}")
print(f"   TOTP Secret: {Config.TOTP_SECRET[:10]}...")

totp = pyotp.TOTP(Config.TOTP_SECRET)
current_totp = totp.now()
print(f"\n2. Generated TOTP Code: {current_totp}")

# Step 2: Make API call
url = f"https://auth.dhan.co/app/generateAccessToken?dhanClientId={Config.CLIENT_CODE}&pin={Config.PIN}&totp={current_totp}"
print(f"\n3. Calling: {url.replace(Config.PIN, '******')}")

try:
    response = requests.post(url, timeout=30)
    print(f"\n4. Response Status: {response.status_code}")
    print(f"   Response Body: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if 'accessToken' in data:
            print("\n✅ SUCCESS! Access token received!")
            print(f"   Token: {data['accessToken'][:50]}...")
            print(f"   Expires: {data.get('expiryTime', 'N/A')}")
        else:
            print("\n❌ No accessToken in response")
            print(f"   Response keys: {data.keys()}")
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "="*50)