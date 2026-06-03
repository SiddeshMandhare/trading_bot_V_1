# debug_dhan_api.py
import json
from auth_service import create_tradehull_with_totp
from config import Config

print("=" * 70)
print("DHAN API DEBUG - Finding correct option chain parameters")
print("=" * 70)

try:
    tsl = create_tradehull_with_totp(Config.CLIENT_CODE, Config.PIN, Config.TOTP_SECRET)
    
    if tsl:
        print("\n✅ Connected to Dhan successfully!")
        
        # Get token for direct REST calls
        token = None
        for attr in ("token_id", "access_token", "_access_token"):
            token = getattr(tsl, attr, None)
            if token:
                break
        
        print(f"\n📋 Token found: {token[:30]}..." if token else "❌ No token found")
        
        # Method 1: Try with different expiry values
        print("\n" + "=" * 50)
        print("METHOD 1: Testing tsl.get_option_chain() with different parameters")
        print("=" * 50)
        
        test_params = [
            {"Underlying": "NIFTY", "exchange": "INDEX", "expiry": 0, "num_strikes": 10},
            {"Underlying": "NIFTY", "exchange": "INDEX", "expiry": 1, "num_strikes": 10},
            {"Underlying": "NIFTY", "exchange": "INDEX", "expiry": 2, "num_strikes": 10},
            {"Underlying": "NIFTY", "exchange": "NSE", "expiry": 0, "num_strikes": 10},
            {"Underlying": "NIFTY", "exchange": "NFO", "expiry": 0, "num_strikes": 10},
        ]
        
        for params in test_params:
            print(f"\n🔍 Testing: {params}")
            try:
                result = tsl.get_option_chain(**params)
                print(f"   Return type: {type(result)}")
                
                if result is None:
                    print("   ❌ Result: None")
                elif isinstance(result, tuple):
                    print(f"   ✅ Tuple with {len(result)} elements")
                    for i, item in enumerate(result):
                        print(f"      Item {i}: type={type(item)}")
                        if hasattr(item, 'shape'):
                            print(f"         shape: {item.shape}")
                            if hasattr(item, 'columns'):
                                print(f"         columns: {list(item.columns)[:5]}...")
                elif hasattr(result, 'shape'):
                    print(f"   ✅ DataFrame shape: {result.shape}")
                    print(f"   Columns: {list(result.columns)}")
                    if not result.empty:
                        print(f"   First row: {result.iloc[0].to_dict()}")
                else:
                    print(f"   Value: {result}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Method 2: Check available expiries first
        print("\n" + "=" * 50)
        print("METHOD 2: Getting available expiries first")
        print("=" * 50)
        
        try:
            expiries = tsl.get_expiry_list(Underlying="NIFTY", exchange="INDEX")
            print(f"📅 Available expiries: {expiries}")
            
            if expiries:
                # Use first expiry from list
                first_expiry = expiries[0]
                print(f"\n🔍 Trying with expiry='{first_expiry}'")
                result = tsl.get_option_chain(
                    Underlying="NIFTY",
                    exchange="INDEX",
                    expiry=first_expiry,
                    num_strikes=10
                )
                print(f"   Return type: {type(result)}")
                if result is not None:
                    print(f"   ✅ Got data!")
        except Exception as e:
            print(f"❌ Error getting expiries: {e}")
        
        # Method 3: Direct REST API call
        print("\n" + "=" * 50)
        print("METHOD 3: Direct REST API call (most reliable)")
        print("=" * 50)
        
        if token:
            import requests
            
            # Try to get option chain via REST
            url = "https://api.dhan.co/v2/optionchain"
            
            # Dhan's option chain endpoint requires these parameters
            params = {
                "exchange_segment": "NSE_FNO",
                "symbol": "NIFTY",
                "expiry_code": "NEAREST",  # or specific date
                "instrument_type": "OPTIDX"
            }
            
            headers = {
                "access-token": token,
                "client-id": Config.CLIENT_CODE,
                "Content-Type": "application/json"
            }
            
            try:
                print(f"\n🔍 Calling REST API: {url}")
                print(f"   Params: {params}")
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                print(f"   Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"   ✅ Got response!")
                    print(f"   Keys: {list(data.keys()) if data else 'None'}")
                else:
                    print(f"   Response: {resp.text[:200]}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Method 4: Check if we need to use different symbol format
        print("\n" + "=" * 50)
        print("METHOD 4: Trying different symbol formats")
        print("=" * 50)
        
        symbol_variants = ["NIFTY", "NIFTY 50", "NIFTY-I", "NIFTYIDX"]
        for sym in symbol_variants:
            try:
                print(f"\n🔍 Trying symbol: '{sym}'")
                result = tsl.get_option_chain(
                    Underlying=sym,
                    exchange="INDEX",
                    expiry=0,
                    num_strikes=5
                )
                if result is not None:
                    print(f"   ✅ SUCCESS with symbol '{sym}'!")
                    break
                else:
                    print(f"   ❌ Failed")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
    else:
        print("❌ Failed to connect to Dhan")
        
except Exception as e:
    print(f"❌ Connection error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)