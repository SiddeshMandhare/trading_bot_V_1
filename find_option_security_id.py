# find_option_security_id.py
from auth_service import create_tradehull_with_totp
from config import Config
import pandas as pd

tsl = create_tradehull_with_totp(Config.CLIENT_CODE, Config.PIN, Config.TOTP_SECRET)

# Search for SENSEX options in instrument file
if hasattr(tsl, 'instrument_df') and tsl.instrument_df is not None:
    df = tsl.instrument_df
    
    # Search for SENSEX options
    sensex_options = df[df['SEM_CUSTOM_SYMBOL'].str.contains('SENSEX.*PUT|SENSEX.*CALL', na=False)]
    
    print(f"Found {len(sensex_options)} SENSEX options")
    print("\nFirst 10 SENSEX options:")
    print(sensex_options[['SEM_CUSTOM_SYMBOL', 'SEM_SMST_SECURITY_ID', 'SEM_STRIKE_PRICE', 
                          'SEM_OPTION_TYPE', 'SEM_EXPIRY_DATE']].head(10).to_string())
    
    # Look specifically for 76000 PUT
    target_options = sensex_options[sensex_options['SEM_CUSTOM_SYMBOL'].str.contains('75000.*PUT', na=False)]
    print("\n\n75000 PUT options:")
    print(target_options[['SEM_CUSTOM_SYMBOL', 'SEM_SMST_SECURITY_ID', 'SEM_EXPIRY_DATE']].to_string())
else:
    print("No instrument file available")
