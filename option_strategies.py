
# option_strategies.py - FIXED VERSION
import pandas as pd
import numpy as np
import re
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from shared_cache import get_shared_cache
from config import Config  # Single config import

@dataclass
class OptionGreeks:
    delta: float = 0.5
    gamma: float = 0.02
    theta: float = -5.0
    vega: float = 10.0
    iv: float = 15.0


def calculate_stop_loss_with_atr(self, premium: float, atr: float):
    """Use ATR for volatility-based stop"""
    atr_stop = premium - (atr * 2)  # 2x ATR stop
    return max(atr_stop, premium * 0.7)  # Don't go below 30% loss


class OptionStrategyAdapter:
    """Adapter to convert equity signals to option trades"""
    
    def __init__(self, tsl):
        self.tsl = tsl
        self.option_chains_cache = {}
        self.cache_time = {}
        self.selected_ce_symbol = None
        self.selected_pe_symbol = None
        
        # Lot sizes for different indices
        self.lot_sizes = {
            'NIFTY': 65,
            'BANKNIFTY': 30,
            'FINNIFTY': 60,
            'SENSEX': 20
        }
    
    def _get_spot_price(self, underlying: str) -> float:
        """Get spot price using built-in method"""
        try:
            # Try to get LTP
            ltp_data = self.tsl.get_ltp_data(names=[underlying])
            if ltp_data and underlying in ltp_data:
                return float(ltp_data[underlying])
        except Exception as e:
            print(f"[SpotPrice] Error: {e}")
        
        # Fallback - get from ATM strike selection
        try:
            CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
                Underlying=underlying,
                Expiry=Config.OPTION_EXPIRY
            )
            return float(atm_strike)
        except:
            pass
        
        # Default fallbacks
        defaults = {
            'NIFTY': 20000,
            'BANKNIFTY': 20000,
            'FINNIFTY': 20000,
            'SENSEX': 20000
        }
        return defaults.get(underlying, 20000)
    


##    def get_option_chain_direct(self, underlying: str, expiry_date: str = None) -> Optional[Tuple[float, pd.DataFrame]]:
##        """
##        Fetch option chain DIRECTLY from Dhan API v2
##        This bypasses the buggy ATM_Strike_Selection and OTM_Strike_Selection methods
##        
##        Args:
##            underlying: 'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX'
##            expiry_date: 'YYYY-MM-DD' format. If None, fetches the nearest expiry
##        
##        Returns:
##            (atm_strike, DataFrame) or (None, None) if failed
##        """
##        import requests
##        from datetime import datetime, timedelta
##        
##        # Security IDs for indices (from Dhan Annexure)
##        SECURITY_IDS = {
##            'NIFTY': 13,
##            'BANKNIFTY': 25,
##            'FINNIFTY': 27,
##            'SENSEX': 51
##        }
##        
##        # Exchange segments
##        EXCHANGE_SEGMENTS = {
##            'NIFTY': 'IDX_I',
##            'BANKNIFTY': 'IDX_I',
##            'FINNIFTY': 'IDX_I',
##            'SENSEX': 'IDX_I'
##        }
##        
##        security_id = SECURITY_IDS.get(underlying)
##        exchange_seg = EXCHANGE_SEGMENTS.get(underlying)
##        
##        if not security_id:
##            print(f"[OptionChain] Unknown underlying: {underlying}")
##            return None, None
##        
##        # Get expiry date if not provided (find next Thursday)
##        if expiry_date is None:
##            today = datetime.now()
##            # Find next Thursday (options expire on Thursday)
##            days_until_thursday = (3 - today.weekday()) % 7
##            if days_until_thursday == 0:
##                days_until_thursday = 7
##            expiry_date = (today + timedelta(days=days_until_thursday)).strftime('%Y-%m-%d')
##            print(f"[OptionChain] Using nearest expiry: {expiry_date}")
##        
##        # Get token
##        token = None
##        if hasattr(self.tsl, 'token_id'):
##            token = self.tsl.token_id
##        elif hasattr(self.tsl, 'access_token'):
##            token = self.tsl.access_token
##        
##        if not token:
##            print("[OptionChain] No access token available")
##            return None, None
##        
##        # Build request
##        url = "https://api.dhan.co/v2/optionchain"
##        headers = {
##            "accept": "application/json",
##            "access-token": token,
##            "client-id": Config.CLIENT_CODE,
##            "Content-Type": "application/json"
##        }
##        
##        payload = {
##            "UnderlyingScrip": security_id,
##            "UnderlyingSeg": exchange_seg,
##            "Expiry": expiry_date
##        }
##        
##        print(f"[OptionChain] Calling Dhan API: {url}")
##        print(f"[OptionChain] Payload: {payload}")
##        
##        try:
##            response = requests.post(url, headers=headers, json=payload, timeout=15)
##            print(f"[OptionChain] Response Status: {response.status_code}")
##            
##            if response.status_code == 200:
##                data = response.json()
##                
##                if data.get('status') == 'success':
##                    result_data = data.get('data', {})
##                    spot_price = result_data.get('last_price', 0)
##                    oc_data = result_data.get('oc', {})
##                    
##                    if not oc_data:
##                        print("[OptionChain] No option chain data received")
##                        return None, None
##                    
##                    # Parse the response into a DataFrame
##                    rows = []
##                    strikes = []
##                    
##                    for strike_str, strike_data in oc_data.items():
##                        strike = float(strike_str)
##                        strikes.append(strike)
##                        
##                        ce_data = strike_data.get('ce', {})
##                        pe_data = strike_data.get('pe', {})
##                        
##                        # Extract CE data
##                        ce_ltp = ce_data.get('last_price', 0)
##                        ce_oi = ce_data.get('oi', 0)
##                        ce_oi_change = ce_data.get('oi', 0) - ce_data.get('previous_oi', 0)
##                        ce_iv = ce_data.get('implied_volatility', 0)
##                        ce_delta = ce_data.get('greeks', {}).get('delta', 0)
##                        ce_theta = ce_data.get('greeks', {}).get('theta', 0)
##                        ce_gamma = ce_data.get('greeks', {}).get('gamma', 0)
##                        ce_vega = ce_data.get('greeks', {}).get('vega', 0)
##                        
##                        # Extract PE data
##                        pe_ltp = pe_data.get('last_price', 0)
##                        pe_oi = pe_data.get('oi', 0)
##                        pe_oi_change = pe_data.get('oi', 0) - pe_data.get('previous_oi', 0)
##                        pe_iv = pe_data.get('implied_volatility', 0)
##                        pe_delta = pe_data.get('greeks', {}).get('delta', 0)
##                        pe_theta = pe_data.get('greeks', {}).get('theta', 0)
##                        pe_gamma = pe_data.get('greeks', {}).get('gamma', 0)
##                        pe_vega = pe_data.get('greeks', {}).get('vega', 0)
##                        
##                        rows.append({
##                            'Strike Price': strike,
##                            'CE LTP': ce_ltp,
##                            'CE OI': ce_oi,
##                            'CE Chg in OI': ce_oi_change,
##                            'CE IV': ce_iv,
##                            'CE Delta': ce_delta,
##                            'CE Theta': ce_theta,
##                            'CE Gamma': ce_gamma,
##                            'CE Vega': ce_vega,
##                            'PE LTP': pe_ltp,
##                            'PE OI': pe_oi,
##                            'PE Chg in OI': pe_oi_change,
##                            'PE IV': pe_iv,
##                            'PE Delta': pe_delta,
##                            'PE Theta': pe_theta,
##                            'PE Gamma': pe_gamma,
##                            'PE Vega': pe_vega,
##                        })
##                    
##                    if not rows:
##                        print("[OptionChain] No rows parsed")
##                        return None, None
##                    
##                    df = pd.DataFrame(rows)
##                    df = df.sort_values('Strike Price')
##                    
##                    # Get ATM strike (closest to spot price)
##                    if spot_price > 0:
##                        atm_strike = min(df['Strike Price'], key=lambda x: abs(x - spot_price))
##                    else:
##                        atm_strike = df.iloc[len(df)//2]['Strike Price']
##                    
##                    print(f"[OptionChain] ✅ Success! Got {len(df)} strikes, Spot: {spot_price}, ATM: {atm_strike}")
##                    
##                    # Store selected symbols for later use
##                    # Find the CE and PE symbols for ATM strike
##                    atm_row = df[df['Strike Price'] == atm_strike].iloc[0]
##                    
##                    # Construct symbol names (you may need to adjust format)
##                    # Format: "NIFTY 02 JUN 23900 CALL"
##                    expiry_obj = datetime.strptime(expiry_date, '%Y-%m-%d')
##                    expiry_str = expiry_obj.strftime("%d %b").upper().replace(" ", " ")
##                    
##                    self.selected_ce_symbol = f"{underlying} {expiry_str} {int(atm_strike)} CALL"
##                    self.selected_pe_symbol = f"{underlying} {expiry_str} {int(atm_strike)} PUT"
##                    
##                    # For OTM strikes
##                    step = 50 if underlying != 'BANKNIFTY' else 100
##                    otm_count = Config.OPTION_OTM_COUNT
##                    
##                    ce_otm_strike = atm_strike + (otm_count * step)
##                    pe_otm_strike = atm_strike - (otm_count * step)
##                    
##                    self.selected_ce_symbol = f"{underlying} {expiry_str} {int(ce_otm_strike)} CALL"
##                    self.selected_pe_symbol = f"{underlying} {expiry_str} {int(pe_otm_strike)} PUT"
##                    
##                    print(f"[OptionChain] Selected CE: {self.selected_ce_symbol}")
##                    print(f"[OptionChain] Selected PE: {self.selected_pe_symbol}")
##                    
##                    return atm_strike, df
##                else:
##                    print(f"[OptionChain] API returned status: {data.get('status')}")
##                    return None, None
##            else:
##                print(f"[OptionChain] HTTP Error: {response.status_code}")
##                print(f"[OptionChain] Response: {response.text}")
##                return None, None
##                
##        except Exception as e:
##            print(f"[OptionChain] Exception: {e}")
##            import traceback
##            traceback.print_exc()
##            return None, None



    def get_option_chain_direct(self, underlying: str, expiry_index: int = 0) -> Optional[Tuple[float, pd.DataFrame]]:
        """
        Fetch option chain DIRECTLY from Dhan API v2
        Uses expiry_index: 0 = current/near, 1 = next, 2 = far
        """
        import requests
        from datetime import datetime
        
        SECURITY_IDS = {
            'NIFTY': 13,
            'BANKNIFTY': 25,
            'FINNIFTY': 27,
            'SENSEX': 51
        }
        
        security_id = SECURITY_IDS.get(underlying)
        if not security_id:
            print(f"[OptionChain] Unknown underlying: {underlying}")
            return None, None
        
        # First, get available expiries
        expiries = self.get_available_expiries(underlying)
        if not expiries:
            print("[OptionChain] No expiries found")
            return None, None
        
        # Select expiry based on index
        if expiry_index >= len(expiries):
            expiry_index = 0
        expiry_date = expiries[expiry_index]
        print(f"[OptionChain] Using expiry {expiry_index}: {expiry_date}")
        
        # Get token
        token = None
        if hasattr(self.tsl, 'token_id'):
            token = self.tsl.token_id
        elif hasattr(self.tsl, 'access_token'):
            token = self.tsl.access_token
        
        if not token:
            print("[OptionChain] No access token available")
            return None, None
        
        # ============ CORRECT URL ============
        url = "https://api.dhan.co/v2/optionchain"
        # ====================================
        
        headers = {
            "accept": "application/json",
            "access-token": token,
            "client-id": Config.CLIENT_CODE,
            "Content-Type": "application/json"
        }
        
        payload = {
            "UnderlyingScrip": security_id,
            "UnderlyingSeg": "IDX_I",
            "Expiry": expiry_date
        }
        
        print(f"[OptionChain] Calling API for {underlying}")
        print(f"[OptionChain] URL: {url}")
        print(f"[OptionChain] Payload: {payload}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            print(f"[OptionChain] Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    result_data = data.get('data', {})
                    spot_price = result_data.get('last_price', 0)
                    oc_data = result_data.get('oc', {})
                    
                    if not oc_data:
                        print("[OptionChain] No option chain data")
                        return None, None
                    
                    # Parse into DataFrame
                    rows = []
                    for strike_str, strike_data in oc_data.items():
                        strike = float(strike_str)
                        
                        ce_data = strike_data.get('ce', {})
                        pe_data = strike_data.get('pe', {})
                        
                        rows.append({
                            'Strike Price': strike,
                            'CE LTP': ce_data.get('last_price', 0),
                            'CE OI': ce_data.get('oi', 0),
                            'CE Chg in OI': ce_data.get('oi', 0) - ce_data.get('previous_oi', 0),
                            'CE IV': ce_data.get('implied_volatility', 0),
                            'CE Delta': ce_data.get('greeks', {}).get('delta', 0),
                            'CE Theta': ce_data.get('greeks', {}).get('theta', 0),
                            'CE Gamma': ce_data.get('greeks', {}).get('gamma', 0),
                            'CE Vega': ce_data.get('greeks', {}).get('vega', 0),
                            'PE LTP': pe_data.get('last_price', 0),
                            'PE OI': pe_data.get('oi', 0),
                            'PE Chg in OI': pe_data.get('oi', 0) - pe_data.get('previous_oi', 0),
                            'PE IV': pe_data.get('implied_volatility', 0),
                            'PE Delta': pe_data.get('greeks', {}).get('delta', 0),
                            'PE Theta': pe_data.get('greeks', {}).get('theta', 0),
                            'PE Gamma': pe_data.get('greeks', {}).get('gamma', 0),
                            'PE Vega': pe_data.get('greeks', {}).get('vega', 0),
                        })
                    
                    if not rows:
                        return None, None
                    
                    df = pd.DataFrame(rows)
                    df = df.sort_values('Strike Price')
                    
                    # Get ATM strike (closest to spot)
                    if spot_price > 0:
                        atm_strike = min(df['Strike Price'], key=lambda x: abs(x - spot_price))
                    else:
                        atm_strike = df.iloc[len(df)//2]['Strike Price']
                    
                    print(f"[OptionChain] ✅ Got {len(df)} strikes, Spot: {spot_price}, ATM: {atm_strike}")
                    
                    # Store selected symbols using OTM count
                    step = 50 if underlying != 'BANKNIFTY' else 100
                    otm_count = Config.OPTION_OTM_COUNT
                    
                    # Format expiry for symbol
                    expiry_obj = datetime.strptime(expiry_date, '%Y-%m-%d')
                    expiry_str = expiry_obj.strftime("%d %b").upper()
                    
                    ce_otm_strike = int(atm_strike + (otm_count * step))
                    pe_otm_strike = int(atm_strike - (otm_count * step))
                    
                    self.selected_ce_symbol = f"{underlying} {expiry_str} {ce_otm_strike} CALL"
                    self.selected_pe_symbol = f"{underlying} {expiry_str} {pe_otm_strike} PUT"
                    
                    print(f"[OptionChain] Selected CE: {self.selected_ce_symbol}")
                    print(f"[OptionChain] Selected PE: {self.selected_pe_symbol}")
                    
                    return atm_strike, df
                else:
                    print(f"[OptionChain] API error: {data}")
                    return None, None
            else:
                print(f"[OptionChain] HTTP {response.status_code}: {response.text}")
                return None, None
                
        except Exception as e:
            print(f"[OptionChain] Exception: {e}")
            import traceback
            traceback.print_exc()
            return None, None


    


##    def get_option_chain(self, underlying: str, expiry_index: int = 0, num_strikes: int = 20):
##        """
##        Get option chain using built-in Dhan methods with REAL premiums
##        """
##        # ============ ADD THIS MAPPING ============
##        # Dhan API expects different names for some indices
##        api_underlying_map = {
##            'NIFTY': 'NIFTY',
##            'BANKNIFTY': 'BANKNIFTY',  # This works
##            'FINNIFTY': 'FINNIFTY',    # This works  
##            'SENSEX': 'SENSEX'         # This works
##        }
##        api_name = api_underlying_map.get(underlying, underlying)
##        # ==========================================
##        
##
##        cache = get_shared_cache()
##        
##        # Check cache first
##        cached_chain = cache.get_option_chain(underlying, expiry_index)
##        if cached_chain and cached_chain.get('success'):
##            print(f"[OptionChain] Using CACHED data for {underlying}")
##            atm_strike = cached_chain.get('atm_strike')
##            df = self._cached_strikes_to_dataframe(cached_chain.get('strikes', []))
##            if df is not None:
##                return atm_strike, df
##        
##        try:
##            print(f"[OptionChain] Fetching for {underlying} with expiry_index={expiry_index}")
##            
##            # Try with requested expiry
##            CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
##                Underlying=underlying,
##                Expiry=expiry_index
##            )
##            
##            # If failed, try expiry 1
##            if atm_strike == 0 or CE_symbol is None:
##                print(f"[OptionChain] Expiry {expiry_index} failed, trying expiry 1")
##                CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
##                    Underlying=underlying,
##                    Expiry=1
##                )
##            
##            # If still failed, try expiry 2
##            if atm_strike == 0 or CE_symbol is None:
##                print(f"[OptionChain] Expiry 1 failed, trying expiry 2")
##                CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
##                    Underlying=underlying,
##                    Expiry=2
##                )
##            
##            if atm_strike == 0 or CE_symbol is None:
##                print(f"[OptionChain] ERROR: Could not get ATM strike for {underlying}")
##                return None, None
##            
##            print(f"[OptionChain] ATM: {atm_strike}, CE: {CE_symbol}, PE: {PE_symbol}")
##            
##            # Get spot price
##            spot_price = self._get_spot_price(underlying)
##            if spot_price == 0:
##                spot_price = atm_strike
##            
##            # Get OTM strikes
##            otm_count = Config.OPTION_OTM_COUNT
##            ce_otm_symbol = CE_symbol
##            pe_otm_symbol = PE_symbol
##            ce_otm_strike = atm_strike
##            pe_otm_strike = atm_strike
##            
##            if otm_count > 0:
##                try:
##                    CE_OTM, PE_OTM, ce_strike, pe_strike = self.tsl.OTM_Strike_Selection(
##                        Underlying=underlying,
##                        Expiry=expiry_index,
##                        OTM_count=otm_count
##                    )
##                    ce_otm_symbol = CE_OTM
##                    pe_otm_symbol = PE_OTM
##                    ce_otm_strike = ce_strike
##                    pe_otm_strike = pe_strike
##                    self.selected_ce_symbol = CE_OTM
##                    self.selected_pe_symbol = PE_OTM
##                    print(f"[OptionChain] OTM {otm_count}: CE={CE_OTM}@{ce_strike}, PE={PE_OTM}@{pe_strike}")
##                except Exception as e:
##                    print(f"[OptionChain] OTM failed: {e}, using ATM")
##                    self.selected_ce_symbol = CE_symbol
##                    self.selected_pe_symbol = PE_symbol
##            else:
##                self.selected_ce_symbol = CE_symbol
##                self.selected_pe_symbol = PE_symbol
##
##
##            # ============ GET REAL PREMIUMS FROM OPTION CHAIN DATA ============
##            ce_premium = 0
##            pe_premium = 0
##            
##            # Use the DataFrame we already have from the API call
##            # The DataFrame is stored in `oc_df` variable (from line ~120-130)
##            # But we need to access it - let me check the scope
##            # Actually, we have `oc_df` from the API response
##            
##            # Since we already have `oc_df` from the API, use it directly
##            if oc_df is not None and not oc_df.empty:
##                try:
##                    # Find the row with our selected strike
##                    if 'Strike Price' in oc_df.columns:
##                        # For CE premium
##                        ce_rows = oc_df[oc_df['Strike Price'] == ce_otm_strike]
##                        if not ce_rows.empty and 'CE LTP' in oc_df.columns:
##                            ce_premium = ce_rows['CE LTP'].iloc[0]
##                            print(f"[OptionChain] REAL CE premium from chain: ₹{ce_premium}")
##                        
##                        # For PE premium
##                        pe_rows = oc_df[oc_df['Strike Price'] == pe_otm_strike]
##                        if not pe_rows.empty and 'PE LTP' in oc_df.columns:
##                            pe_premium = pe_rows['PE LTP'].iloc[0]
##                            print(f"[OptionChain] REAL PE premium from chain: ₹{pe_premium}")
##                except Exception as e:
##                    print(f"[OptionChain] Error extracting premiums from chain: {e}")
##            
##            # SECOND: If chain didn't work, try API
##            if ce_premium == 0 or pe_premium == 0:
##                try:
##                    symbols_to_fetch = []
##                    if self.selected_ce_symbol and ce_premium == 0:
##                        symbols_to_fetch.append(self.selected_ce_symbol)
##                    if self.selected_pe_symbol and pe_premium == 0:
##                        symbols_to_fetch.append(self.selected_pe_symbol)
##                    
##                    if symbols_to_fetch:
##                        ltp_data = self.tsl.get_ltp_data(names=symbols_to_fetch)
##                        if ltp_data:
##                            if ce_premium == 0:
##                                ce_premium = ltp_data.get(self.selected_ce_symbol, 0)
##                            if pe_premium == 0:
##                                pe_premium = ltp_data.get(self.selected_pe_symbol, 0)
##                            print(f"[OptionChain] Premiums from API - CE: ₹{ce_premium}, PE: ₹{pe_premium}")
##                except Exception as e:
##                    print(f"[OptionChain] API premium fetch error: {e}")
##            
##            # THIRD: If still 0, calculate based on distance from spot (LAST RESORT)
##            if ce_premium == 0 and self.selected_ce_symbol:
##                print(f"[OptionChain] WARNING: Could not get real CE premium, using estimate")
##                distance = abs(ce_otm_strike - spot_price) / spot_price
##                ce_premium = max(10, round(spot_price * distance * 0.3, 2))
##                print(f"[OptionChain] Estimated CE premium: ₹{ce_premium}")
##
##            if pe_premium == 0 and self.selected_pe_symbol:
##                print(f"[OptionChain] WARNING: Could not get real PE premium, using estimate")
##                distance = abs(pe_otm_strike - spot_price) / spot_price
##                pe_premium = max(10, round(spot_price * distance * 0.3, 2))
##                print(f"[OptionChain] Estimated PE premium: ₹{pe_premium}")
##
##
##                
##            
####            # ============ GET REAL PREMIUMS FOR THE SELECTED STRIKES ============
####            ce_premium = 0
####            pe_premium = 0
####            
####            # Try to get premiums for the selected option symbols
####            try:
####                symbols_to_fetch = []
####                if self.selected_ce_symbol:
####                    symbols_to_fetch.append(self.selected_ce_symbol)
####                if self.selected_pe_symbol:
####                    symbols_to_fetch.append(self.selected_pe_symbol)
####                
####                if symbols_to_fetch:
####                    ltp_data = self.tsl.get_ltp_data(names=symbols_to_fetch)
####                    if ltp_data:
####                        ce_premium = ltp_data.get(self.selected_ce_symbol, 0)
####                        pe_premium = ltp_data.get(self.selected_pe_symbol, 0)
####                        print(f"[OptionChain] REAL PREMIUMS - CE: ₹{ce_premium}, PE: ₹{pe_premium}")
####            except Exception as e:
####                print(f"[OptionChain] Could not fetch premiums: {e}")
####            
####            # If premium is still 0, calculate based on distance from spot
####            if ce_premium == 0 and self.selected_ce_symbol:
####                print(f"[OptionChain] WARNING: Could not get real CE premium, calculating estimate")
####                distance = abs(ce_otm_strike - spot_price) / spot_price
####                ce_premium = max(10, round(spot_price * distance * 0.5, 2))
####                print(f"[OptionChain] Calculated CE premium: ₹{ce_premium} (ESTIMATE)")
####
####            if pe_premium == 0 and self.selected_pe_symbol:
####                print(f"[OptionChain] WARNING: Could not get real PE premium, calculating estimate")
####                distance = abs(pe_otm_strike - spot_price) / spot_price
####                pe_premium = max(10, round(spot_price * distance * 0.5, 2))
####                print(f"[OptionChain] Calculated PE premium: ₹{pe_premium} (ESTIMATE)")
##            
##            # Build DataFrame with REAL premiums
##            step = 50
##            if underlying == 'BANKNIFTY':
##                step = 100
##            elif underlying == 'SENSEX':
##                step = 100
##            
##            data = []
##            strikes_list = []
##            
##            for i in range(-num_strikes, num_strikes + 1):
##                strike = atm_strike + (i * step)
##                
##                # Determine if this strike is our selected strike
##                is_selected_ce = (strike == ce_otm_strike)
##                is_selected_pe = (strike == pe_otm_strike)
##                
##                # Set premium values (only for selected strikes, others can be approximated)
##                ce_ltp = ce_premium if is_selected_ce else max(1, ce_premium * (1 - abs(i) * 0.1)) if ce_premium > 0 else 0
##                pe_ltp = pe_premium if is_selected_pe else max(1, pe_premium * (1 - abs(i) * 0.1)) if pe_premium > 0 else 0
##                
##                strikes_list.append({
##                    'strike': strike,
##                    'ce': {
##                        'ltp': ce_ltp,
##                        'oi': 0, 'oi_change': 0, 'iv': 14.2,
##                        'delta': 0.5, 'theta': -10, 'gamma': 0.003, 'vega': 10,
##                        'signal': '⚪ NEUTRAL'
##                    },
##                    'pe': {
##                        'ltp': pe_ltp,
##                        'oi': 0, 'oi_change': 0, 'iv': 14.2,
##                        'delta': -0.5, 'theta': -10, 'gamma': 0.003, 'vega': 10,
##                        'signal': '⚪ NEUTRAL'
##                    }
##                })
##                
##                data.append({
##                    'Strike Price': strike,
##                    'CE LTP': ce_ltp,
##                    'CE OI': 0, 'CE Chg in OI': 0,
##                    'CE IV': 14.2, 'CE Delta': 0.5, 'CE Theta': -10,
##                    'CE Gamma': 0.003, 'CE Vega': 10,
##                    'PE LTP': pe_ltp,
##                    'PE OI': 0, 'PE Chg in OI': 0,
##                    'PE IV': 14.2, 'PE Delta': -0.5, 'PE Theta': -10,
##                    'PE Gamma': 0.003, 'PE Vega': 10,
##                })
##            
##            df = pd.DataFrame(data)
##            
##            # Cache the result
##            cache.set_option_chain(underlying, expiry_index, {
##                'success': True,
##                'atm_strike': atm_strike,
##                'spot_price': spot_price,
##                'strikes': strikes_list
##            })
##            
##            return atm_strike, df
##            
##        except Exception as e:
##            print(f"[OptionChain] Error: {e}")
##            import traceback
##            traceback.print_exc()
##            return None, None
##    


    def get_option_chain(self, underlying: str, expiry_index: int = 0, num_strikes: int = 20):
        """
        Get option chain using DIRECT Dhan API call
        expiry_index: 0 = current/near, 1 = next, 2 = far
        """
        cache = get_shared_cache()
        
        # Check cache first
        cached_chain = cache.get_option_chain(underlying, expiry_index)
        if cached_chain and cached_chain.get('success'):
            print(f"[OptionChain] Using CACHED data for {underlying}")
            atm_strike = cached_chain.get('atm_strike')
            df = self._cached_strikes_to_dataframe(cached_chain.get('strikes', []))
            if df is not None:
                return atm_strike, df
        
        # Fetch directly from API with expiry_index
        result = self.get_option_chain_direct(underlying, expiry_index)
        
        if result and result[0] is not None:
            atm_strike, df = result
            
            # Limit to num_strikes around ATM
            step = 50 if underlying != 'BANKNIFTY' else 100
            min_strike = atm_strike - (num_strikes * step)
            max_strike = atm_strike + (num_strikes * step)
            df_filtered = df[(df['Strike Price'] >= min_strike) & (df['Strike Price'] <= max_strike)]
            
            return atm_strike, df_filtered
        
        return None, None


    def get_available_expiries(self, underlying: str) -> List[str]:
        """
        Get available expiry dates for an underlying from Dhan API
        Returns list of dates in 'YYYY-MM-DD' format
        """
        import requests
        
        SECURITY_IDS = {
            'NIFTY': 13,
            'BANKNIFTY': 25,
            'FINNIFTY': 27,
            'SENSEX': 51
        }
        
        security_id = SECURITY_IDS.get(underlying)
        if not security_id:
            print(f"[Expiry] Unknown underlying: {underlying}")
            return []
        
        # Get token
        token = None
        if hasattr(self.tsl, 'token_id'):
            token = self.tsl.token_id
        elif hasattr(self.tsl, 'access_token'):
            token = self.tsl.access_token
        
        if not token:
            print("[Expiry] No access token")
            return []
        
        # ============ FIXED URL ============
        url = "https://api.dhan.co/v2/optionchain/expirylist"
        # ==================================
        
        headers = {
            "accept": "application/json",
            "access-token": token,
            "client-id": Config.CLIENT_CODE,
            "Content-Type": "application/json"
        }
        
        payload = {
            "UnderlyingScrip": security_id,
            "UnderlyingSeg": "IDX_I"
        }
        
        print(f"[Expiry] Calling: {url}")
        print(f"[Expiry] Payload: {payload}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            print(f"[Expiry] Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[Expiry] Response data: {data}")
                
                if data.get('status') == 'success':
                    expiries = data.get('data', [])
                    print(f"[Expiry] Got {len(expiries)} expiries: {expiries[:3]}...")
                    return expiries
                else:
                    print(f"[Expiry] API error: {data}")
            else:
                print(f"[Expiry] HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"[Expiry] Exception: {e}")
            import traceback
            traceback.print_exc()
        
        return []


##
##    def get_option_chain(self, underlying: str, expiry_index: int = 0, num_strikes: int = 20):
##        """
##        Get option chain using built-in Dhan methods with REAL premiums
##        """
##        cache = get_shared_cache()
##        
##        # Check cache first
##        cached_chain = cache.get_option_chain(underlying, expiry_index)
##        if cached_chain and cached_chain.get('success'):
##            print(f"[OptionChain] Using CACHED data for {underlying}")
##            atm_strike = cached_chain.get('atm_strike')
##            df = self._cached_strikes_to_dataframe(cached_chain.get('strikes', []))
##            if df is not None:
##                return atm_strike, df
##        
##        try:
##            print(f"[OptionChain] Fetching for {underlying} with expiry_index={expiry_index}")
##            
##            # Try with requested expiry
##            CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
##                Underlying=underlying,
##                Expiry=expiry_index
##            )
##            
##            # If failed, try expiry 1
##            if atm_strike == 0 or CE_symbol is None:
##                print(f"[OptionChain] Expiry {expiry_index} failed, trying expiry 1")
##                CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
##                    Underlying=underlying,
##                    Expiry=1
##                )
##            
##            # If still failed, try expiry 2
##            if atm_strike == 0 or CE_symbol is None:
##                print(f"[OptionChain] Expiry 1 failed, trying expiry 2")
##                CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
##                    Underlying=underlying,
##                    Expiry=2
##                )
##            
##            if atm_strike == 0 or CE_symbol is None:
##                print(f"[OptionChain] ERROR: Could not get ATM strike for {underlying}")
##                return None, None
##            
##            print(f"[OptionChain] ATM: {atm_strike}, CE: {CE_symbol}, PE: {PE_symbol}")
##            
##            # Get spot price
##            spot_price = self._get_spot_price(underlying)
##            if spot_price == 0:
##                spot_price = atm_strike
##            
##            # Get OTM strikes
##            otm_count = Config.OPTION_OTM_COUNT
##            ce_otm_symbol = CE_symbol
##            pe_otm_symbol = PE_symbol
##            ce_otm_strike = atm_strike
##            pe_otm_strike = atm_strike
##            
##            # Initialize oc_df as None
##            oc_df = None
##            
##            if otm_count > 0:
##                try:
##                    CE_OTM, PE_OTM, ce_strike, pe_strike = self.tsl.OTM_Strike_Selection(
##                        Underlying=underlying,
##                        Expiry=expiry_index,
##                        OTM_count=otm_count
##                    )
##                    ce_otm_symbol = CE_OTM
##                    pe_otm_symbol = PE_OTM
##                    ce_otm_strike = ce_strike
##                    pe_otm_strike = pe_strike
##                    self.selected_ce_symbol = CE_OTM
##                    self.selected_pe_symbol = PE_OTM
##                    print(f"[OptionChain] OTM {otm_count}: CE={CE_OTM}@{ce_strike}, PE={PE_OTM}@{pe_strike}")
##                except Exception as e:
##                    print(f"[OptionChain] OTM failed: {e}, using ATM")
##                    self.selected_ce_symbol = CE_symbol
##                    self.selected_pe_symbol = PE_symbol
##            else:
##                self.selected_ce_symbol = CE_symbol
##                self.selected_pe_symbol = PE_symbol
##            
##            # ============ GET REAL PREMIUMS ============
##            ce_premium = 0
##            pe_premium = 0
##            
##            # Try to get option chain data from API to get real premiums
##            try:
##                api_result = self.tsl.get_option_chain(
##                    Underlying=underlying,
##                    exchange="INDEX",
##                    expiry=expiry_index,
##                    num_strikes=num_strikes * 2
##                )
##                
##                if api_result and isinstance(api_result, tuple) and len(api_result) == 2:
##                    oc_df = api_result[1]  # This is the DataFrame with real data
##                    
##                    if oc_df is not None and not oc_df.empty:
##                        # ============ ADD THESE DEBUG PRINTS ============
##                        print(f"\n{'='*60}")
##                        print(f"[DEBUG] UNDERLYING: {underlying}")
##                        print(f"[DEBUG] pe_otm_strike = {pe_otm_strike}")
##                        print(f"[DEBUG] ce_otm_strike = {ce_otm_strike}")
##                        print(f"[DEBUG] oc_df columns: {list(oc_df.columns)}")
##                        
##                        # Show first few strikes
##                        if 'Strike Price' in oc_df.columns:
##                            strikes = oc_df['Strike Price'].tolist()[:15]
##                            print(f"[DEBUG] Available strikes: {strikes}")
##                        print(f"{'='*60}\n")
##                        # ================================================
##                        
##                        # Find the row with our selected strike
##                        if 'Strike Price' in oc_df.columns:
##                            # For PE premium (PUT)
##                            pe_rows = oc_df[oc_df['Strike Price'] == pe_otm_strike]
##                            if not pe_rows.empty and 'PE LTP' in oc_df.columns:
##                                pe_premium = pe_rows['PE LTP'].iloc[0]
##                                print(f"[OptionChain] REAL PE premium from chain: ₹{pe_premium}")
##                            else:
##                                print(f"[DEBUG] No matching PE row for strike {pe_otm_strike}")
##                            
##                            # For CE premium (CALL)
##                            ce_rows = oc_df[oc_df['Strike Price'] == ce_otm_strike]
##                            if not ce_rows.empty and 'CE LTP' in oc_df.columns:
##                                ce_premium = ce_rows['CE LTP'].iloc[0]
##                                print(f"[OptionChain] REAL CE premium from chain: ₹{ce_premium}")
##                            else:
##                                print(f"[DEBUG] No matching CE row for strike {ce_otm_strike}")
##            except Exception as e:
##                print(f"[OptionChain] Could not fetch option chain for premiums: {e}")
##                import traceback
##                traceback.print_exc()
##            
##            # If still 0, try API directly
##            if ce_premium == 0 and self.selected_ce_symbol:
##                try:
##                    ltp_data = self.tsl.get_ltp_data(names=[self.selected_ce_symbol])
##                    if ltp_data:
##                        ce_premium = ltp_data.get(self.selected_ce_symbol, 0)
##                        print(f"[OptionChain] CE premium from API: ₹{ce_premium}")
##                except Exception as e:
##                    print(f"[OptionChain] CE API error: {e}")
##            
##            if pe_premium == 0 and self.selected_pe_symbol:
##                try:
##                    ltp_data = self.tsl.get_ltp_data(names=[self.selected_pe_symbol])
##                    if ltp_data:
##                        pe_premium = ltp_data.get(self.selected_pe_symbol, 0)
##                        print(f"[OptionChain] PE premium from API: ₹{pe_premium}")
##                except Exception as e:
##                    print(f"[OptionChain] PE API error: {e}")
##            
##            # If still 0, calculate estimate
##            if ce_premium == 0 and self.selected_ce_symbol:
##                distance = abs(ce_otm_strike - spot_price) / spot_price
##                ce_premium = max(10, round(spot_price * distance * 0.3, 2))
##                print(f"[OptionChain] Estimated CE premium: ₹{ce_premium}")
##            
##            if pe_premium == 0 and self.selected_pe_symbol:
##                distance = abs(pe_otm_strike - spot_price) / spot_price
##                pe_premium = max(10, round(spot_price * distance * 0.3, 2))
##                print(f"[OptionChain] Estimated PE premium: ₹{pe_premium}")
##            
##            # Build DataFrame
##            step = 100  # SENSEX step is 100
##            data = []
##            strikes_list = []
##            
##            for i in range(-num_strikes, num_strikes + 1):
##                strike = atm_strike + (i * step)
##                
##                is_selected_ce = (strike == ce_otm_strike)
##                is_selected_pe = (strike == pe_otm_strike)
##                
##                ce_ltp = ce_premium if is_selected_ce else max(1, ce_premium * (1 - abs(i) * 0.1)) if ce_premium > 0 else 0
##                pe_ltp = pe_premium if is_selected_pe else max(1, pe_premium * (1 - abs(i) * 0.1)) if pe_premium > 0 else 0
##                
##                strikes_list.append({
##                    'strike': strike,
##                    'ce': {'ltp': ce_ltp, 'oi': 0, 'oi_change': 0, 'iv': 14.2, 'delta': 0.5, 'theta': -10, 'gamma': 0.003, 'vega': 10, 'signal': '⚪ NEUTRAL'},
##                    'pe': {'ltp': pe_ltp, 'oi': 0, 'oi_change': 0, 'iv': 14.2, 'delta': -0.5, 'theta': -10, 'gamma': 0.003, 'vega': 10, 'signal': '⚪ NEUTRAL'}
##                })
##                
##                data.append({
##                    'Strike Price': strike,
##                    'CE LTP': ce_ltp, 'CE OI': 0, 'CE Chg in OI': 0,
##                    'CE IV': 14.2, 'CE Delta': 0.5, 'CE Theta': -10,
##                    'CE Gamma': 0.003, 'CE Vega': 10,
##                    'PE LTP': pe_ltp, 'PE OI': 0, 'PE Chg in OI': 0,
##                    'PE IV': 14.2, 'PE Delta': -0.5, 'PE Theta': -10,
##                    'PE Gamma': 0.003, 'PE Vega': 10,
##                })
##            
##            df = pd.DataFrame(data)
##            
##            # Cache the result
##            cache.set_option_chain(underlying, expiry_index, {
##                'success': True,
##                'atm_strike': atm_strike,
##                'spot_price': spot_price,
##                'strikes': strikes_list
##            })
##            
##            return atm_strike, df
##            
##        except Exception as e:
##            print(f"[OptionChain] Error: {e}")
##            import traceback
##            traceback.print_exc()
##            return None, None






    
    
    def select_optimal_strike(self, df: pd.DataFrame, atm_strike: float, 
                          direction: str, otm_count: int = 1, 
                          underlying: str = None) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        """Return pre-selected option symbol from get_option_chain"""
        
        # Determine correct step size based on underlying
        if underlying:
            if underlying == 'SENSEX' or underlying == 'BANKNIFTY':
                step = 100
            else:  # NIFTY, FINNIFTY
                step = 50
        else:
            # Fallback to checking symbol string
            ce_symbol = getattr(self, 'selected_ce_symbol', '')
            if 'SENSEX' in str(ce_symbol) or 'BANKNIFTY' in str(ce_symbol):
                step = 100
            else:
                step = 50
        
        print(f"[StrikeSelection] Underlying: {underlying}, Step: {step}")
        
        if direction == 'CALL':
            symbol = self.selected_ce_symbol
            strike = atm_strike + (otm_count * step)
        else:
            symbol = self.selected_pe_symbol
            strike = atm_strike - (otm_count * step)
        
        print(f"[StrikeSelection] Using {direction} symbol: {symbol} at strike {strike}")
        return symbol, strike, step
    
    def get_lot_size(self, underlying: str) -> int:
        """Get lot size for underlying"""
        return self.lot_sizes.get(underlying, 50)



    def _cached_strikes_to_dataframe(self, strikes_data: list):
        """Convert cached strikes to DataFrame"""
        import pandas as pd
        
        if not strikes_data:
            return None
        
        data = []
        for s in strikes_data:
            row = {
                'Strike Price': s['strike'],
                'CE LTP': s['ce']['ltp'],
                'CE OI': 0, 'CE Chg in OI': 0,
                'CE IV': s['ce']['iv'],
                'CE Delta': s['ce']['delta'],
                'CE Theta': s['ce']['theta'],
                'CE Gamma': s['ce']['gamma'],
                'CE Vega': s['ce']['vega'],
                'PE LTP': s['pe']['ltp'],
                'PE OI': 0, 'PE Chg in OI': 0,
                'PE IV': s['pe']['iv'],
                'PE Delta': s['pe']['delta'],
                'PE Theta': s['pe']['theta'],
                'PE Gamma': s['pe']['gamma'],
                'PE Vega': s['pe']['vega'],
            }
            data.append(row)
        
        return pd.DataFrame(data)






class OptionTradeManager:
    """Manage option trades with proper Greeks and risk management"""
    
    def __init__(self, tsl):
        self.tsl = tsl
        self.active_option_positions = {}
        self.trailing_stops = {}
    
    
    
    def calculate_stop_loss(self, premium: float, entry_price: float, 
                        option_type: str, greeks: Dict) -> Dict:
        """Calculate stop loss - ADAPTIVE for option volatility"""
        
        entry_premium = entry_price
        
        # 1. Percentage stop (wider for options)
        if 'CE' in str(option_type) or 'PE' in str(option_type):
            sl_multiplier = 0.30  # 30% for options (more volatile)
        else:
            sl_multiplier = Config.OPTION_SL_MULTIPLIER
        
        percentage_sl = entry_premium * (1 - sl_multiplier)
        
        # 2. Dynamic fixed rupee stop based on premium
        if entry_premium < 30:
            fixed_rupee_stop = 5
        elif entry_premium < 100:
            fixed_rupee_stop = 10
        else:
            fixed_rupee_stop = 20
        
        fixed_sl = entry_premium - fixed_rupee_stop
        
        # 3. Greeks-based stop (if delta available)
        delta_stop = None
        if greeks and greeks.get('delta'):
            # Lower delta = more OTM = wider stop
            delta_abs = abs(greeks.get('delta', 0.5))
            if delta_abs < 0.3:
                delta_stop = entry_premium * 0.6  # 40% loss for deep OTM
            elif delta_abs < 0.5:
                delta_stop = entry_premium * 0.7  # 30% loss
            else:
                delta_stop = entry_premium * 0.8  # 20% loss for ITM
        
        # Choose the tightest stop (highest price = smallest loss)
        candidates = [percentage_sl, fixed_sl]
        if delta_stop:
            candidates.append(delta_stop)
        
        stop_loss = max(candidates)
        loss_amount = entry_premium - stop_loss
        loss_percent = (loss_amount / entry_premium) * 100
        
        print(f"\n📊 OPTION STOP LOSS:")
        print(f"   Entry: ₹{entry_premium:.2f}")
        print(f"   Percentage Stop ({(1-sl_multiplier)*100:.0f}%): ₹{percentage_sl:.2f}")
        print(f"   Fixed Stop (₹{fixed_rupee_stop}): ₹{fixed_sl:.2f}")
        if delta_stop:
            print(f"   Delta-based Stop: ₹{delta_stop:.2f}")
        print(f"   → SELECTED: ₹{stop_loss:.2f} (Max Loss: ₹{loss_amount:.2f}, {loss_percent:.1f}%)")
        
        return {
            'price_sl': round(stop_loss, 2),
            'loss_percent': round(loss_percent, 1),
            'loss_amount': round(loss_amount, 2),
            'stop_type': 'ADAPTIVE'
        }
    
    def calculate_targets(self, premium: float, greeks: Dict, 
                          option_type: str, current_spot: float = 0,
                          stop_loss: float = None) -> Dict:
        """Calculate profit targets"""
        
        target_multiplier = Config.OPTION_TARGET_MULTIPLIER
        stretch_multiplier = Config.OPTION_STRETCH_TARGET_MULTIPLIER
        
        target_1 = premium * target_multiplier
        target_2 = premium * stretch_multiplier
        moon_target = premium * 8
        
        profit_percent_1 = (target_1 - premium) / premium * 100
        profit_percent_2 = (target_2 - premium) / premium * 100
        
        print(f"\n🎯 TARGETS:")
        print(f"   Target 1: ₹{target_1:.2f} ({profit_percent_1:.0f}%)")
        print(f"   Target 2: ₹{target_2:.2f} ({profit_percent_2:.0f}%)")
        
        return {
            'target_1': round(target_1, 2),
            'target_2': round(target_2, 2),
            'moon_target': round(moon_target, 2),
            'profit_percent_1': round(profit_percent_1, 1),
            'profit_percent_2': round(profit_percent_2, 1),
            'risk_reward_ratio': 0
        }
    
    def calculate_option_greeks(self, symbol: str, underlying_price: float, 
                                 strike: float, option_type: str) -> OptionGreeks:
        """Calculate option Greeks"""
        # Return defaults for now (Dhan API has greeks in option chain)
        return OptionGreeks()
    
    def check_stop_loss(self, position: Dict, current_premium: float, 
                        current_spot: float, entry_spot: float) -> Tuple[bool, str]:
        """Check if stop loss is hit"""
        stop_loss = position.get('sl', 0)
        
        if stop_loss == 0:
            return False, ""
        
        if current_premium <= stop_loss:
            return True, f"STOP LOSS HIT"
        
        return False, ""
    
    def check_targets(self, position: Dict, current_premium: float, 
                      current_spot: float) -> Tuple[bool, str, float]:
        """Check if targets are hit"""
        target = position.get('target', float('inf'))
        
        if current_premium >= target:
            return True, f"TARGET HIT", current_premium
        
        return False, "", 0
    
    def update_trailing_stop(self, symbol: str, current_premium: float,
                              entry_premium: float, delta: float) -> Optional[float]:
        """Update trailing stop"""
        if symbol not in self.trailing_stops:
            self.trailing_stops[symbol] = {
                'highest': entry_premium,
                'current_sl': entry_premium * 0.7
            }
        
        tracker = self.trailing_stops[symbol]
        
        if current_premium > tracker['highest']:
            tracker['highest'] = current_premium
        
        new_sl = tracker['highest'] * 0.85
        
        if new_sl > tracker['current_sl']:
            tracker['current_sl'] = new_sl
            return new_sl
        
        return None


class OptionSignalProcessor:
    """Convert equity trading signals to option trades"""
    
    def __init__(self, tsl, trade_execution):
        self.tsl = tsl
        self.execution = trade_execution
        self.adapter = OptionStrategyAdapter(tsl)
        self.manager = OptionTradeManager(tsl)
        self.processed_signals = {}
    
    def get_spot_price(self, underlying: str) -> float:
        """Get current spot price"""
        try:
            ltp_data = self.tsl.get_ltp_data(names=[underlying])
            if ltp_data and underlying in ltp_data:
                return float(ltp_data[underlying])
        except:
            pass
        return 0

    
    def get_premium(self, option_symbol: str, option_df: pd.DataFrame = None, strike: float = None, option_type: str = None) -> float:
        """Get current option premium - PRIORITIZE option chain data"""
        
        # METHOD 1: Get from option chain DataFrame (BEST - WORKS!)
        if option_df is not None and strike is not None:
            try:
                # Find the row with matching strike
                matching = option_df[option_df['Strike Price'] == strike]
                if not matching.empty:
                    row = matching.iloc[0]
                    if option_type == 'PUT':
                        premium = row.get('PE LTP', 0)
                    else:
                        premium = row.get('CE LTP', 0)
                    
                    if premium and premium > 0:
                        print(f"[Premium] From option chain: ₹{premium:.2f}")
                        return float(premium)
            except Exception as e:
                print(f"[Premium] Option chain lookup error: {e}")
        
        # METHOD 2: Try API (usually fails for options)
        if option_symbol:
            try:
                ltp_data = self.tsl.get_ltp_data(names=[option_symbol])
                if ltp_data and option_symbol in ltp_data:
                    premium = float(ltp_data[option_symbol])
                    if premium > 0:
                        print(f"[Premium] From API: ₹{premium:.2f}")
                        return premium
            except Exception as e:
                print(f"[Premium] API error: {e}")
        
        return 0
    
    def process_signal_for_option(self, signal_data: Dict, chart: pd.DataFrame, 
                                   symbol: str, current_time: datetime) -> Optional[Dict]:
        """Process a trading signal and convert to option trade"""

        # ============ ADD THIS CHECK ============
        # Check if we already have an open position for this symbol
        if symbol in self.execution.orderbook:
            print(f"⚠️ Already have an open position for {symbol}, skipping")
            return None
        # =======================================
    
        
        print(f"\n{'='*60}")
        print(f"🔍 OPTION SIGNAL PROCESSING")
        print(f"   Symbol: {symbol}")
        print(f"{'='*60}")
        
        # Check if option trading is enabled
        if not Config.OPTION_TRADING_ENABLED:
            print("❌ Option trading disabled")
            return None
        
        # Check if we should trade options for this symbol
        if symbol not in Config.OPTION_SYMBOLS:
            print(f"❌ {symbol} not in OPTION_SYMBOLS")
            return None
        
        # Determine direction
        direction = 'CALL' if signal_data.get('buy_call') else 'PUT' if signal_data.get('buy_put') else None
        
        if not direction:
            print("❌ No valid direction")
            return None
        
        print(f"📊 Direction: {direction}")
        
        # Get spot price
        spot_price = self.get_spot_price(symbol)
        if spot_price == 0:
            print(f"⚠️ Cannot get spot price for {symbol}")
            return None
        
        print(f"📍 Spot: ₹{spot_price:,.2f}")
        
        # Get option chain
        expiry_index = Config.OPTION_EXPIRY
        atm_strike, option_df = self.adapter.get_option_chain(symbol, expiry_index)
        
        if option_df is None or option_df.empty:
            print(f"⚠️ No option chain for {symbol}")
            return None
        
        # Select strike
        otm_count = Config.OPTION_OTM_COUNT
        option_symbol, strike, step = self.adapter.select_optimal_strike(
            option_df, atm_strike, direction, otm_count,symbol
        )
        
        if not option_symbol:
            print(f"❌ No option symbol found")
            return None
        
        print(f"✅ Option: {option_symbol} @ strike {strike}")
        
        # Get premium (pass option_df, strike, and direction)
        premium = self.get_premium(option_symbol, option_df, strike, direction)
        if premium == 0:
            print(f"⚠️ Cannot get premium for {option_symbol}")
            # Use estimated premium
            premium = max(10, (abs(spot_price - strike) / 100) * 10)
            print(f"   Using estimated: ₹{premium:.2f}")
        
        # Calculate position size
        capital = self.execution.get_available_capital()
        risk_amount = capital * Config.OPTION_RISK_PER_TRADE_PERCENT
        
        lot_size = self.adapter.get_lot_size(symbol)
        max_lots = int(risk_amount / (premium * lot_size))
        lots = min(max_lots, Config.OPTION_MAX_LOTS_PER_TRADE)
        
        # FIX: If max_lots is 0 but premium is affordable, still allow 1 lot
        if lots == 0 and capital > (premium * lot_size):
            lots = 1
            print(f"[Position] Forcing 1 lot - capital can afford it")
                
        quantity = lots * lot_size

        # Add this debug
        print(f"[Position Sizing] Capital: ₹{capital}, Risk: {Config.OPTION_RISK_PER_TRADE_PERCENT*100}%, Risk Amount: ₹{risk_amount}")
        print(f"[Position Sizing] Premium: ₹{premium}, Lot Size: {lot_size}, Max Lots: {max_lots}, Selected Lots: {lots}, Quantity: {quantity}")

        if lots == 0:
            print(f"❌ Risk amount too low")
            return None
        
        # Calculate SL and targets
        sl_data = self.manager.calculate_stop_loss(premium, premium, direction, {})
        target_data = self.manager.calculate_targets(premium, {}, direction, spot_price)
        
        print(f"\n📊 TRADE DETAILS:")
        print(f"   Lots: {lots} (Qty: {quantity})")
        print(f"   Premium: ₹{premium:.2f}")
        print(f"   Stop Loss: ₹{sl_data['price_sl']:.2f}")
        print(f"   Target: ₹{target_data['target_1']:.2f}")
        
        # Place order
        order = self._place_option_order(
            option_symbol=option_symbol,
            lots=lots,
            quantity=quantity,
            premium=premium,
            stop_loss=sl_data['price_sl'],
            target=target_data['target_1'],
            target_2=target_data['target_2'],
            underlying=symbol,
            strike=strike,
            option_type=direction,
            spot_price=spot_price,
            strategy=signal_data.get('triggering_strategy', 'UNKNOWN')
        )
        
        # ============ ADD THIS BLOCK ============
        if order:
            # Add to orderbook immediately to prevent duplicate orders
            self.execution.orderbook[symbol] = order
            print(f"📝 Added {symbol} to orderbook")
            return order
        # ========================================
        
        return None



    def _place_option_order(self, option_symbol: str, lots: int, quantity: int,
                        premium: float, stop_loss: float, target: float, target_2: float,
                        underlying: str, strike: float, option_type: str,
                        spot_price: float, strategy: str) -> Optional[Dict]:
        """Place the actual option order using direct API method"""
        
        try:
            # Calculate ATR points for option
            atr_points = premium * Config.ATR_MULTIPLIER
            
            # ENSURE stop_loss is not 0
            if stop_loss == 0:
                stop_loss = premium * 0.7  # 30% stop as fallback
                print(f"⚠️ Stop loss was 0, using fallback: ₹{stop_loss}")
            
            # ============ FIX: PASS stop_loss and target to place_super_order ============
            # But wait - your current place_super_order doesn't accept these parameters!
            # You need to MODIFY trade_execution.py's place_super_order method
            
            super_order_id = self.execution.place_super_order(
                name=option_symbol,
                action='BUY',
                qty=quantity,
                entry_price=premium,
                atr_points=atr_points,
                strategy_name=strategy,
                chart=None,
                stop_loss_price=stop_loss,  # ← ADD THIS
                target_price=target          # ← ADD THIS
            )
            # ============================================================================
            
            if super_order_id:
                current_time = datetime.now(Config.IST)
                
                order = {
                    'name': option_symbol,
                    'option_type': option_type,
                    'underlying': underlying,
                    'strike': strike,
                    'lots': lots,
                    'qty': quantity,
                    'entry_price': premium,
                    'sl': stop_loss,
                    'target': target,
                    'target_2': target_2,
                    'strategy': strategy,
                    'super_order_id': super_order_id,
                    'entry_time': current_time.strftime('%H:%M:%S'),
                    'date': str(current_time.date()),
                    'position_type': 'LONG',
                    'buy_sell': 'BUY',
                    'entry_spot': spot_price,
                    'status': 'open'
                }
                
                print(f"\n✅ OPTION ORDER PLACED! ID: {super_order_id}")
                return order
            
            return None
            
        except Exception as e:
            print(f"❌ Option order failed: {e}")
            import traceback
            traceback.print_exc()
            return None



    
##    def _place_option_order(self, option_symbol: str, lots: int, quantity: int,
##                        premium: float, stop_loss: float, target: float, target_2: float,
##                        underlying: str, strike: float, option_type: str,
##                        spot_price: float, strategy: str) -> Optional[Dict]:
##        """Place the actual option order using direct API method"""
##        
##        try:
##            # Calculate ATR points for option (use premium-based approximation)
##            atr_points = premium * config.ATR_MULTIPLIER  # 20% of premium as ATR for options
##
##            # ENSURE stop_loss is not 0
##            if stop_loss == 0:
##                stop_loss = premium * 0.7  # 30% stop as fallback
##                print(f"⚠️ Stop loss was 0, using fallback: ₹{stop_loss}")
##            
##            # Call execution.place_super_order with CORRECT parameter names
##            super_order_id = self.execution.place_super_order(
##                name=option_symbol,           # ← CHANGED from tradingsymbol
##                action='BUY',                 # ← CHANGED from transaction_type
##                qty=quantity,                 # ← CHANGED from quantity
##                entry_price=premium,          # ← ADDED (was missing)
##                atr_points=atr_points,        # ← ADDED (was missing)
##                strategy_name=strategy,       # ← ADDED (was missing)
##                chart=None                    # ← ADDED (was missing)
##            )
##            
##            if super_order_id:
##                current_time = datetime.now(Config.IST)
##                
##                order = {
##                    'name': option_symbol,
##                    'option_type': option_type,
##                    'underlying': underlying,
##                    'strike': strike,
##                    'lots': lots,
##                    'qty': quantity,
##                    'entry_price': premium,
##                    'sl': stop_loss,
##                    'target': target,
##                    'target_2': target_2,
##                    'strategy': strategy,
##                    'super_order_id': super_order_id,
##                    'entry_time': current_time.strftime('%H:%M:%S'),
##                    'date': str(current_time.date()),
##                    'position_type': 'LONG',
##                    'buy_sell': 'BUY',
##                    'entry_spot': spot_price,
##                    'status': 'open'
##                }
##                
##                print(f"\n✅ OPTION ORDER PLACED! ID: {super_order_id}")
##                return order
##            
##            return None
##            
##        except Exception as e:
##            print(f"❌ Option order failed: {e}")
##            import traceback
##            traceback.print_exc()
##            return None


##
##    def _place_option_order(self, option_symbol: str, lots: int, quantity: int,
##                        premium: float, stop_loss: float, target: float, target_2: float,
##                        underlying: str, strike: float, option_type: str,
##                        spot_price: float, strategy: str) -> Optional[Dict]:
##        """Place the actual option order using direct API method"""
##        
##        try:
##            # Calculate ATR points for option (use premium-based approximation)
##            atr_points = premium * 0.2  # 20% of premium as ATR for options
##            
##            # Call execution.place_super_order with CORRECT parameter names
##            super_order_id = self.execution.place_super_order(
##                name=option_symbol,           # ← CHANGED from tradingsymbol
##                action='BUY',                 # ← CHANGED from transaction_type
##                qty=quantity,                 # ← CHANGED from quantity
##                entry_price=premium,          # ← ADDED (was missing)
##                atr_points=atr_points,        # ← ADDED (was missing)
##                strategy_name=strategy,       # ← ADDED (was missing)
##                chart=None                    # ← ADDED (was missing)
##            )
##            
##            if super_order_id:
##                current_time = datetime.now(Config.IST)
##                
##                order = {
##                    'name': option_symbol,
##                    'option_type': option_type,
##                    'underlying': underlying,
##                    'strike': strike,
##                    'lots': lots,
##                    'qty': quantity,
##                    'entry_price': premium,
##                    'sl': stop_loss,
##                    'target': target,
##                    'target_2': target_2,
##                    'strategy': strategy,
##                    'super_order_id': super_order_id,
##                    'entry_time': current_time.strftime('%H:%M:%S'),
##                    'date': str(current_time.date()),
##                    'position_type': 'LONG',
##                    'buy_sell': 'BUY',
##                    'entry_spot': spot_price,
##                    'status': 'open'
##                }
##                
##                print(f"\n✅ OPTION ORDER PLACED! ID: {super_order_id}")
##                return order
##            
##            return None
##            
##        except Exception as e:
##            print(f"❌ Option order failed: {e}")
##            import traceback
##            traceback.print_exc()
##            return None


    


































########################################################################################################################

### option_strategies.py
##import pandas as pd
##import numpy as np
##import re
##from typing import Dict, Any, Tuple, Optional, List
##from datetime import datetime, timedelta
##from dataclasses import dataclass
##from config import Config  # Single config import
##
##@dataclass
##class OptionGreeks:
##    delta: float = 0.5
##    gamma: float = 0.02
##    theta: float = -5.0
##    vega: float = 10.0
##    iv: float = 15.0
##
##class OptionStrategyAdapter:
##    """Adapter to convert equity signals to option trades"""
##    
##    def __init__(self, tsl):
##        self.tsl = tsl
##        self.option_chains_cache = {}
##        self.cache_time = {}
##        self.selected_ce_symbol = None
##        self.selected_pe_symbol = None
##               
##        # Lot sizes for different indices
##        self.lot_sizes = {
##            'NIFTY': 65,
##            'BANKNIFTY': 30,
##            'FINNIFTY': 60,
##            'SENSEX': 20
##        }
##        
##        # Step sizes
##        self.step_sizes = {
##            'NIFTY': 50,
##            'BANKNIFTY': 100,
##            'FINNIFTY': 50,
##            'SENSEX': 100
##        }
##
##
##    def get_option_chain(self, underlying: str, expiry_index: int = 0, num_strikes: int = 20):
##        """
##        Get option chain - simplified using built-in methods
##        """
##        try:
##            from config import Config
##            
##            # Get ATM strike first (to get spot price reference)
##            CE_symbol, PE_symbol, atm_strike = self.tsl.ATM_Strike_Selection(
##                Underlying=underlying,
##                Expiry=expiry_index
##            )
##            
##            # Get spot price from LTP
##            spot_price = self._get_spot_price(underlying)
##            if spot_price == 0:
##                spot_price = atm_strike
##            
##            # Get OTM strikes for the requested count
##            CE_OTM, PE_OTM, ce_strike, pe_strike = self.tsl.OTM_Strike_Selection(
##                Underlying=underlying,
##                Expiry=expiry_index,
##                OTM_count=Config.OPTION_OTM_COUNT
##            )
##            
##            # Build a simple DataFrame for compatibility
##            data = []
##            for i in range(-num_strikes, num_strikes + 1):
##                strike = atm_strike + (i * 50)
##                data.append({
##                    'Strike Price': strike,
##                    'CE LTP': 0, 'CE OI': 0, 'CE Chg in OI': 0,
##                    'CE IV': 14.2, 'CE Delta': 0.5, 'CE Theta': -10,
##                    'CE Gamma': 0.003, 'CE Vega': 10,
##                    'PE LTP': 0, 'PE OI': 0, 'PE Chg in OI': 0,
##                    'PE IV': 14.2, 'PE Delta': -0.5, 'PE Theta': -10,
##                    'PE Gamma': 0.003, 'PE Vega': 10,
##                })
##            
##            df = pd.DataFrame(data)
##            
##            # Store the option symbols for later use
##            self.selected_ce_symbol = CE_OTM if Config.OPTION_OTM_COUNT > 0 else CE_symbol
##            self.selected_pe_symbol = PE_OTM if Config.OPTION_OTM_COUNT > 0 else PE_symbol
##            
##            print(f"[OptionChain] ATM: {atm_strike}, Selected CE: {self.selected_ce_symbol}, Selected PE: {self.selected_pe_symbol}")
##            
##            return atm_strike, df
##            
##        except Exception as e:
##            print(f"[OptionChain] Error: {e}")
##            import traceback
##            traceback.print_exc()
##            return None, None
##
##        
##
####    def get_option_chain(self, underlying: str, expiry_index: int = 0, num_strikes: int = 20):
####        """
####        Get option chain using OptionChainService (which has fallback to synthetic data)
####        This will work even when market is closed!
####        """
####        cache_key = f"{underlying}_{expiry_index}"
####        now = datetime.now().timestamp()
####        
####        # Check cache
####        if cache_key in self.option_chains_cache:
####            cache_age = now - self.cache_time.get(cache_key, 0)
####            from config import Config
####            if cache_age < getattr(option_config, 'OPTION_CHAIN_CACHE_SECONDS', 30):
####                return self.option_chains_cache[cache_key]
####        
####        try:
####            # Use the OptionChainService which handles fallback
####            result = self.chain_service.get_option_chain(
####                underlying=underlying,
####                expiry_index=expiry_index,
####                num_strikes=num_strikes
####            )
####            
####            if result and result.get('success'):
####                # Convert to the format expected by the rest of the code
####                atm_strike = result['atm_strike']
####                
####                # Convert strikes data to DataFrame format
####                data = []
####                for s in result['strikes']:
####                    row = {
####                        'Strike Price': s['strike'],
####                        'CE LTP': s['ce']['ltp'],
####                        'CE OI': s['ce']['oi'],
####                        'CE Chg in OI': s['ce']['oi_change'],
####                        'CE IV': s['ce']['iv'],
####                        'CE Delta': s['ce']['delta'],
####                        'CE Theta': s['ce']['theta'],
####                        'CE Gamma': s['ce']['gamma'],
####                        'CE Vega': s['ce']['vega'],
####                        'PE LTP': s['pe']['ltp'],
####                        'PE OI': s['pe']['oi'],
####                        'PE Chg in OI': s['pe']['oi_change'],
####                        'PE IV': s['pe']['iv'],
####                        'PE Delta': s['pe']['delta'],
####                        'PE Theta': s['pe']['theta'],
####                        'PE Gamma': s['pe']['gamma'],
####                        'PE Vega': s['pe']['vega'],
####                    }
####                    data.append(row)
####                
####                df = pd.DataFrame(data)
####                
####                # Cache the result
####                self.option_chains_cache[cache_key] = (atm_strike, df)
####                self.cache_time[cache_key] = now
####                
####                print(f"[OptionChain] ✅ Got data from OptionChainService (Live: {result.get('live', False)})")
####                return atm_strike, df
####            else:
####                print(f"[OptionChain] ❌ No data from OptionChainService")
####                return None, None
####                
####        except Exception as e:
####            print(f"[OptionChain] Error: {e}")
####            import traceback
####            traceback.print_exc()
####            return None, None
##
##
##    def _cached_strikes_to_dataframe(self, strikes_data: list):
##        """Convert cached strikes to DataFrame"""
##        import pandas as pd
##        
##        if not strikes_data:
##            return None
##        
##        data = []
##        for s in strikes_data:
##            row = {
##                'Strike Price': s['strike'],
##                'CE LTP': s['ce']['ltp'],
##                'CE OI': s['ce']['oi'],
##                'CE Chg in OI': s['ce']['oi_change'],
##                'CE IV': s['ce']['iv'],
##                'CE Delta': s['ce']['delta'],
##                'CE Theta': s['ce']['theta'],
##                'CE Gamma': s['ce']['gamma'],
##                'CE Vega': s['ce']['vega'],
##                'PE LTP': s['pe']['ltp'],
##                'PE OI': s['pe']['oi'],
##                'PE Chg in OI': s['pe']['oi_change'],
##                'PE IV': s['pe']['iv'],
##                'PE Delta': s['pe']['delta'],
##                'PE Theta': s['pe']['theta'],
##                'PE Gamma': s['pe']['gamma'],
##                'PE Vega': s['pe']['vega'],
##            }
##            data.append(row)
##        
##        return pd.DataFrame(data)
##
##    
##    def select_optimal_strike(self, df: pd.DataFrame, atm_strike: float, 
##                          direction: str, otm_count: int = 1) -> Tuple[Optional[str], Optional[float], Optional[float]]:
##    """Return pre-selected option symbol from get_option_chain"""
##    
##    if direction == 'CALL':
##        symbol = getattr(self, 'selected_ce_symbol', None)
##        strike = atm_strike + (otm_count * 50)
##    else:
##        symbol = getattr(self, 'selected_pe_symbol', None)
##        strike = atm_strike - (otm_count * 50)
##    
##    print(f"[StrikeSelection] Using {direction} symbol: {symbol} at strike {strike}")
##    return symbol, strike, 50
##
##
##class OptionTradeManager:
##    """Manage option trades with proper Greeks and risk management"""
##    
##    def __init__(self, tsl):
##        self.tsl = tsl
##        self.active_option_positions = {}
##        self.trailing_stops = {}
##        
##    def calculate_option_premium(self, symbol: str) -> float:
##        """Get current option premium"""
##        try:
##            ltp_data = self.tsl.get_ltp_data(names=[symbol])
##            return ltp_data.get(symbol, 0)
##        except:
##            return 0
##    
##
##    def calculate_stop_loss(self, premium: float, entry_price: float, 
##                        option_type: str, greeks: Dict) -> Dict:
##        """
##        Calculate stop loss with multiple strategies
##        Takes the TIGHTEST stop (highest price = smallest loss)
##        
##        Strategies:
##        1. Percentage-based stop (e.g., 20% loss - TIGHTER than 30%)
##        2. Time-based/Theta stop (10% loss from theta - TIGHTER)
##        3. Fixed rupee stop (e.g., ₹5/₹10 max loss)
##        
##        Returns:
##            Dict with stop loss details
##        """
##        from config import Config
##        
##        entry_premium = entry_price
##        
##        # ============ STRATEGY 1: Tighter Percentage stop (20% instead of 30%) ============
##        sl_multiplier = getattr(option_config, 'OPTION_SL_MULTIPLIER', 0.2)  # 20% loss max
##        percentage_sl_price = entry_premium * (1 - sl_multiplier)
##        percentage_loss = entry_premium - percentage_sl_price
##        
##        # ============ STRATEGY 2: Tighter Theta stop (10% loss) ============
##        theta_stop_threshold = getattr(option_config, 'OPTION_THETA_STOP_PERCENT', 0.10)  # 10% loss from theta
##        time_stop_premium = entry_premium * (1 - theta_stop_threshold)
##        time_loss = entry_premium - time_stop_premium
##        
##        # ============ STRATEGY 3: Fixed rupee stop (₹5, ₹10, or ₹15) ============
##        fixed_rupee_stop = getattr(option_config, 'OPTION_FIXED_STOP_RUPEE', 5.0)  # ₹5 max loss
##        fixed_rupee_sl_price = entry_premium - fixed_rupee_stop
##        fixed_rupee_loss = fixed_rupee_stop
##        
##        # ============ Choose the TIGHTEST stop (highest price = smallest loss) ============
##        candidates = [
##            (percentage_sl_price, f"PERCENTAGE ({sl_multiplier*100:.0f}%)", percentage_loss),
##            (time_stop_premium, f"THETA ({theta_stop_threshold*100:.0f}%)", time_loss),
##            (fixed_rupee_sl_price, f"FIXED_RUPEE (₹{fixed_rupee_stop})", fixed_rupee_loss)
##        ]
##        
##        # Sort by stop price (highest first = smallest loss)
##        candidates.sort(key=lambda x: x[0], reverse=True)
##        stop_loss, stop_type, actual_loss = candidates[0]
##        
##        # ============ Ensure we never lose more than ₹10 or 15% ============
##        max_allowed_loss = min(fixed_rupee_stop * 2, entry_premium * 0.15)
##        if actual_loss > max_allowed_loss:
##            stop_loss = entry_premium - max_allowed_loss
##            stop_type = f"MAX_LOSS_CAP (₹{max_allowed_loss:.2f})"
##            actual_loss = max_allowed_loss
##        
##        # ============ Calculate loss percentage ============
##        loss_percent = (entry_premium - stop_loss) / entry_premium * 100
##        
##        # ============ Detailed Logging ============
##        print(f"\n{'='*60}")
##        print(f"📊 OPTION STOP LOSS (SMALLEST LOSS STRATEGY)")
##        print(f"{'='*60}")
##        print(f"   Entry Premium: ₹{entry_premium:.2f}")
##        print(f"{'-'*40}")
##        print(f"   📉 PERCENTAGE Stop ({sl_multiplier*100:.0f}% loss):")
##        print(f"      Stop: ₹{percentage_sl_price:.2f} | Loss: ₹{percentage_loss:.2f}")
##        print(f"   ⏰ THETA Stop ({theta_stop_threshold*100:.0f}% loss):")
##        print(f"      Stop: ₹{time_stop_premium:.2f} | Loss: ₹{time_loss:.2f}")
##        print(f"   💰 FIXED RUPEE Stop (₹{fixed_rupee_stop} loss):")
##        print(f"      Stop: ₹{fixed_rupee_sl_price:.2f} | Loss: ₹{fixed_rupee_loss:.2f}")
##        print(f"{'-'*40}")
##        print(f"   ✅ TIGHTEST STOP: {stop_type}")
##        print(f"      Stop Price: ₹{stop_loss:.2f}")
##        print(f"      Max Loss: ₹{actual_loss:.2f} ({loss_percent:.1f}%)")
##        print(f"{'='*60}\n")
##        
##        return {
##            'price_sl': round(stop_loss, 2),
##            'loss_percent': round(loss_percent, 1),
##            'loss_amount': round(actual_loss, 2),
##            'stop_type': stop_type,
##            'delta_threshold': Config.MIN_DELTA_FOR_ENTRY
##        }
##
##    # def calculate_stop_loss(self, premium: float, entry_price: float, 
##    #                     option_type: str, greeks: Dict) -> Dict:
##    #     """
##    #     Calculate stop loss with multiple strategies
##        
##    #     Returns:
##    #         Dict with stop loss details
##    #     """
##    #     from config import Config
##        
##    #     entry_premium = entry_price
##        
##    #     # Strategy 1: Percentage-based stop (e.g., 30%)
##    #     sl_multiplier = Config.OPTION_SL_MULTIPLIER
##    #     percentage_sl_price = entry_premium * (1 - sl_multiplier)
##    #     percentage_loss = entry_premium - percentage_sl_price
##        
##    #     # Strategy 2: Time-based stop (theta protection)
##    #     theta_stop_threshold = 0.15  # 15% loss from theta
##    #     time_stop_premium = entry_premium * (1 - theta_stop_threshold)
##        
##    #     # Strategy 3: Fixed rupee stop (NEW)
##    #     # Add to Config.py: OPTION_FIXED_STOP_RUPEE = 10.0
##    #     fixed_rupee_stop = getattr(option_config, 'OPTION_FIXED_STOP_RUPEE', 10.0)
##    #     fixed_rupee_sl_price = entry_premium - fixed_rupee_stop
##        
##    #     # Choose the BEST stop loss (highest price = smallest loss)
##    #     # Among: percentage, time-based, and fixed rupee
##    #     candidates = [percentage_sl_price, time_stop_premium, fixed_rupee_sl_price]
##    #     stop_loss = max(candidates)  # Highest price gives smallest loss
##        
##    #     # Ensure minimum 10% loss (safety net)
##    #     min_sl = entry_premium * 0.9
##    #     stop_loss = min(stop_loss, min_sl)
##        
##    #     # Also ensure we don't lose more than fixed rupee amount
##    #     # This is the KEY - whichever is LESS loss
##    #     actual_loss = entry_premium - stop_loss
##    #     if actual_loss > fixed_rupee_stop:
##    #         # If calculated loss exceeds fixed rupee, use fixed rupee
##    #         stop_loss = entry_premium - fixed_rupee_stop
##    #         stop_type = "FIXED_RUPEE"
##    #         loss_amount = fixed_rupee_stop
##    #     else:
##    #         # Use the calculated stop
##    #         stop_type = "DYNAMIC"
##    #         loss_amount = actual_loss
##        
##    #     # Calculate loss percentage
##    #     loss_percent = (entry_premium - stop_loss) / entry_premium * 100
##        
##    #     print(f"\n📊 STOP LOSS CALCULATION:")
##    #     print(f"   Entry Premium: ₹{entry_premium:.2f}")
##    #     print(f"   Percentage Stop ({(1-sl_multiplier)*100:.0f}%): ₹{percentage_sl_price:.2f} (Loss: ₹{percentage_loss:.2f})")
##    #     print(f"   Fixed Rupee Stop (₹{fixed_rupee_stop}): ₹{fixed_rupee_sl_price:.2f}")
##    #     print(f"   Time-based Stop: ₹{time_stop_premium:.2f}")
##    #     print(f"   → SELECTED: {stop_type} stop at ₹{stop_loss:.2f} (Max Loss: ₹{loss_amount:.2f})")
##        
##    #     return {
##    #         'percentage_sl': round(percentage_sl_price, 2),
##    #         'price_sl': round(stop_loss, 2),
##    #         'loss_percent': round(loss_percent, 1),
##    #         'loss_amount': round(loss_amount, 2),
##    #         'stop_type': stop_type,
##    #         'delta_threshold': Config.MIN_DELTA_FOR_ENTRY
##    #     }
##        
##    
##    # def calculate_targets(self, premium: float, greeks: Dict, 
##    #                       option_type: str, current_spot: float = 0) -> Dict:
##    #     """
##    #     Calculate profit targets
##        
##    #     Returns:
##    #         Dict with target details
##    #     """
##    #     from config import Config
##        
##    #     entry_premium = premium
##    #     target_multiplier = Config.OPTION_TARGET_MULTIPLIER
##        
##    #     # Target 1: Fixed percentage
##    #     target_1 = entry_premium * target_multiplier
##        
##    #     # Target 2: Stretch target (2x target multiplier)
##    #     target_2 = entry_premium * (target_multiplier * 2)
##        
##    #     return {
##    #         'target_1': round(target_1, 2),
##    #         'target_2': round(target_2, 2),
##    #         'profit_percent_1': round((target_1 - entry_premium) / entry_premium * 100, 1),
##    #         'profit_percent_2': round((target_2 - entry_premium) / entry_premium * 100, 1)
##    #     }
##
##
##    def calculate_targets(self, premium: float, greeks: Dict, 
##                      option_type: str, current_spot: float = 0,
##                      stop_loss: float = None) -> Dict:
##        """
##        Calculate profit targets with HIGHER profit potential
##        
##        Args:
##            premium: Entry premium
##            greeks: Option Greeks
##            option_type: 'CALL' or 'PUT'
##            current_spot: Current spot price
##            stop_loss: Stop loss price (from calculate_stop_loss)
##        
##        Returns:
##            Dict with target details
##        """
##        from config import Config
##        
##        entry_premium = premium
##        
##        # ============ AGGRESSIVE TARGETS ============
##        target_multiplier = getattr(option_config, 'OPTION_TARGET_MULTIPLIER', 3.0)
##        stretch_multiplier = getattr(option_config, 'OPTION_STRETCH_TARGET_MULTIPLIER', 5.0)
##        
##        target_1 = entry_premium * target_multiplier
##        target_2 = entry_premium * stretch_multiplier
##        moon_target = entry_premium * 8
##        
##        profit_percent_1 = (target_1 - entry_premium) / entry_premium * 100
##        profit_percent_2 = (target_2 - entry_premium) / entry_premium * 100
##        
##        # Calculate risk/reward ratio if stop_loss is provided
##        risk_reward_ratio = 0
##        if stop_loss and stop_loss > 0:
##            risk = entry_premium - stop_loss
##            reward = target_1 - entry_premium
##            if risk > 0:
##                risk_reward_ratio = round(reward / risk, 1)
##        
##        print(f"\n{'='*60}")
##        print(f"🎯 OPTION TARGETS (MAXIMIZE PROFITS)")
##        print(f"{'='*60}")
##        print(f"   Entry Premium: ₹{entry_premium:.2f}")
##        if stop_loss:
##            print(f"   Stop Loss: ₹{stop_loss:.2f} (Risk: ₹{entry_premium - stop_loss:.2f})")
##            print(f"   Risk/Reward: 1:{risk_reward_ratio}")
##        print(f"   Target 1 (Book 50%): ₹{target_1:.2f} ({profit_percent_1:.0f}% profit)")
##        print(f"   Target 2 (Book 30%): ₹{target_2:.2f} ({profit_percent_2:.0f}% profit)")
##        print(f"   Moon Target (Trail): ₹{moon_target:.2f} ({(moon_target/entry_premium-1)*100:.0f}% profit)")
##        print(f"{'='*60}\n")
##        
##        return {
##            'target_1': round(target_1, 2),
##            'target_2': round(target_2, 2),
##            'moon_target': round(moon_target, 2),
##            'profit_percent_1': round(profit_percent_1, 1),
##            'profit_percent_2': round(profit_percent_2, 1),
##            'risk_reward_ratio': risk_reward_ratio
##        }
##        
##    def calculate_option_greeks(self, symbol: str, underlying_price: float, 
##                                 strike: float, option_type: str) -> OptionGreeks:
##        """Calculate option Greeks for risk assessment"""
##        try:
##            # Parse expiry from symbol
##            expiry_days = self._get_days_to_expiry(symbol)
##            
##            # Try to get Greeks from Dhan
##            result = self.tsl.get_option_greek(
##                strike=int(strike),
##                expiry=max(1, expiry_days),
##                asset=self._extract_underlying(symbol),
##                interest_rate=0.05,
##                flag="all_val",
##                scrip_type=option_type
##            )
##            
##            if result and isinstance(result, dict):
##                return OptionGreeks(
##                    delta=float(result.get('callDelta', 0.5)),
##                    gamma=float(result.get('gamma', 0.02)),
##                    theta=float(result.get('callTheta', -5.0)),
##                    vega=float(result.get('vega', 10.0)),
##                    iv=float(result.get('implied_volatility', 15.0))
##                )
##        except Exception as e:
##            print(f"Greeks calculation error: {e}")
##        
##        # Return sensible defaults
##        return OptionGreeks()
##    
##    def _get_days_to_expiry(self, option_symbol: str) -> int:
##        """Calculate days to expiry from option symbol"""
##        try:
##            # Parse option symbol format: NIFTY24JAN24500CE
##            date_match = re.search(r'(\d{2})([A-Z]{3})(\d{2})', option_symbol)
##            if date_match:
##                day = int(date_match.group(1))
##                month_str = date_match.group(2)
##                year = 2000 + int(date_match.group(3))
##                
##                month_map = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
##                            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
##                month = month_map.get(month_str, 1)
##                
##                expiry_date = datetime(year, month, day)
##                days = (expiry_date - datetime.now()).days
##                return max(1, days)
##        except:
##            pass
##        return 30
##    
##    def _extract_underlying(self, option_symbol: str) -> str:
##        """Extract underlying from option symbol"""
##        if 'NIFTY' in option_symbol:
##            return 'NIFTY'
##        elif 'BANKNIFTY' in option_symbol:
##            return 'BANKNIFTY'
##        elif 'FINNIFTY' in option_symbol:
##            return 'FINNIFTY'
##        elif 'SENSEX' in option_symbol:
##            return 'SENSEX'
##        return 'NIFTY'
##    
##    def check_stop_loss(self, position: Dict, current_premium: float, 
##                        current_spot: float, entry_spot: float) -> Tuple[bool, str]:
##        """
##        REAL-TIME STOP LOSS MONITORING
##        
##        Returns: (hit, reason)
##        """
##        entry_premium = position.get('entry_price', 0)
##        stop_loss = position.get('sl', 0)
##        
##        if stop_loss == 0:
##            return False, ""
##        
##        # Check 1: Premium-based stop loss
##        if current_premium <= stop_loss:
##            return True, f"STOP LOSS HIT: Premium fell from ₹{entry_premium:.2f} to ₹{current_premium:.2f}"
##        
##        # Check 2: Percentage drop (rapid movement)
##        loss_percent = (entry_premium - current_premium) / entry_premium * 100
##        if loss_percent >= 40:
##            return True, f"RAPID DROP: {loss_percent:.0f}% loss"
##        
##        # Check 3: Underlying-based stop (more accurate)
##        option_type = position.get('option_type', 'CALL')
##        
##        if entry_spot and current_spot and entry_spot > 0:
##            if option_type == 'CALL':
##                # CALL option should benefit from rising underlying
##                # Stop if underlying falls significantly
##                spot_drop_percent = (entry_spot - current_spot) / entry_spot * 100
##                if spot_drop_percent >= 1.5:
##                    return True, f"UNDERLYING DROP: {spot_drop_percent:.1f}%"
##            else:
##                # PUT option should benefit from falling underlying
##                # Stop if underlying rises significantly
##                spot_rise_percent = (current_spot - entry_spot) / entry_spot * 100
##                if spot_rise_percent >= 1.5:
##                    return True, f"UNDERLYING RISE: {spot_rise_percent:.1f}%"
##        
##        # Check 4: Time-based exit
##        holding_minutes = position.get('holding_minutes', 0)
##        from config import Config
##        if holding_minutes > Config.OPTION_MAX_HOLDING_HOURS * 60:
##            return True, f"MAX HOLDING TIME: {Config.OPTION_MAX_HOLDING_HOURS} hours exceeded"
##        
##        return False, ""
##    
##    def check_targets(self, position: Dict, current_premium: float, 
##                      current_spot: float) -> Tuple[bool, str, float]:
##        """
##        REAL-TIME TARGET MONITORING
##        
##        Returns: (hit, reason, exit_price)
##        """
##        entry_premium = position.get('entry_price', 0)
##        target_1 = position.get('target', entry_premium * 1.5)
##        target_2 = position.get('target_2', entry_premium * 2.0)
##        
##        # Update highest premium for tracking
##        highest = position.get('highest_premium', entry_premium)
##        if current_premium > highest:
##            position['highest_premium'] = current_premium
##            highest = current_premium
##        
##        # Target 1 hit - partial profit booking
##        if current_premium >= target_1 and not position.get('partial_booked', False):
##            position['partial_booked'] = True
##            position['partial_exit_price'] = current_premium
##            from config import Config
##            position['remaining_lots'] = position.get('lots', 1) // 2
##            print(f"🎯 PARTIAL BOOKING: {position['remaining_lots']} lots remaining at ₹{current_premium:.2f}")
##            
##            # Return partial exit (will close half position)
##            return True, f"TARGET 1 HIT: Booked 50% profit at ₹{current_premium:.2f}", current_premium
##        
##        # Target 2 hit - full exit
##        if current_premium >= target_2:
##            return True, f"TARGET 2 HIT: {(current_premium/entry_premium-1)*100:.0f}% profit", current_premium
##        
##        return False, "", 0
##    
##    def update_trailing_stop(self, symbol: str, current_premium: float,
##                              entry_premium: float, delta: float) -> Optional[float]:
##        """
##        Calculate new trailing stop loss
##        
##        Returns: New stop loss price or None if no change
##        """
##        # Initialize tracking
##        if symbol not in self.trailing_stops:
##            self.trailing_stops[symbol] = {
##                'highest': entry_premium,
##                'current_sl': entry_premium * 0.7  # Initial 30% stop
##            }
##        
##        tracker = self.trailing_stops[symbol]
##        
##        # Update highest premium
##        if current_premium > tracker['highest']:
##            tracker['highest'] = current_premium
##        
##        peak = tracker['highest']
##        
##        # Calculate trailing stop based on delta
##        if delta > 0.6:
##            # ITM option - tighter trail (15%)
##            trail_percent = 0.15
##        elif delta > 0.4:
##            # Near ATM - medium trail (20%)
##            trail_percent = 0.20
##        else:
##            # OTM option - wider trail (30%)
##            trail_percent = 0.30
##        
##        # Profit-based adjustment
##        profit_percent = (current_premium - entry_premium) / entry_premium * 100
##        if profit_percent > 100:
##            trail_percent = 0.15  # Tighter for high profits
##        
##        new_trail_stop = peak * (1 - trail_percent)
##        
##        # Only move stop loss UP (protect profits)
##        if new_trail_stop > tracker['current_sl']:
##            tracker['current_sl'] = new_trail_stop
##            return new_trail_stop
##        
##        return None
##    
##    def get_trailing_stop(self, symbol: str) -> float:
##        """Get current trailing stop for symbol"""
##        if symbol in self.trailing_stops:
##            return self.trailing_stops[symbol]['current_sl']
##        return 0
##
##
##class OptionSignalProcessor:
##    """Convert equity trading signals to option trades"""
##    
##    def __init__(self, tsl, trade_execution):
##        self.tsl = tsl
##        self.execution = trade_execution
##        self.adapter = OptionStrategyAdapter(tsl)
##        self.manager = OptionTradeManager(tsl)
##        
##        # Underlying mapping
##        self.underlying_map = {
##            'NIFTY': 'NIFTY',
##            'BANKNIFTY': 'BANKNIFTY', 
##            'FINNIFTY': 'FINNIFTY',
##            'SENSEX': 'SENSEX'
##        }
##        
##        # Track processed signals to avoid duplicates
##        self.processed_signals = {}
##    
##    def get_spot_price(self, underlying: str) -> float:
##        """Get current spot price of underlying"""
##        try:
##            ltp_data = self.tsl.get_ltp_data(names=[underlying])
##            return ltp_data.get(underlying, 0)
##        except:
##            return 0
##    
##    def get_premium(self, option_symbol: str) -> float:
##        """Get current option premium - with fallback for testing"""
##        try:
##            ltp_data = self.tsl.get_ltp_data(names=[option_symbol])
##            if ltp_data and option_symbol in ltp_data:
##                return float(ltp_data[option_symbol])
##        except Exception as e:
##            print(f"⚠️ Could not get premium for {option_symbol}: {e}")
##        
##        # For testing when market is closed, return a simulated premium
##        # Extract strike from option symbol (e.g., NIFTY24MAY23800CE -> 23800)
##        import re
##        match = re.search(r'(\d{5})', option_symbol)
##        if match:
##            strike = int(match.group(1))
##            # Simulate premium based on distance from spot
##            spot = self.get_spot_price(self._extract_underlying(option_symbol))
##            if spot > 0:
##                if 'CE' in option_symbol:
##                    premium = max(5, (spot - strike) / 100 * 10) if strike < spot else max(5, 30 - (strike - spot) / 100 * 5)
##                else:
##                    premium = max(5, (strike - spot) / 100 * 10) if strike > spot else max(5, 30 - (spot - strike) / 100 * 5)
##                return round(premium, 2)
##        
##        return 0
##    
##    def can_trade_option(self, symbol: str, current_time: datetime) -> bool:
##        """Check if we can trade this option (cooldown)"""
##        
##        # Check cooldown
##        if symbol in self.processed_signals:
##            last_time = self.processed_signals[symbol]
##            minutes_passed = (current_time - last_time).total_seconds() / 60
##            if minutes_passed < 5:  # 5 minute cooldown
##                return False
##        
##        return True
##    
##    def record_trade(self, symbol: str, current_time: datetime):
##        """Record that we traded this option"""
##        self.processed_signals[symbol] = current_time
##    
##    def process_signal_for_option(self, signal_data: Dict, chart: pd.DataFrame, 
##                                   symbol: str, current_time: datetime) -> Optional[Dict]:
##        """
##        Process a trading signal and convert to option trade
##        """
##        from config import Config
##
##        # ============ ADD THIS DEBUG ============
##        print(f"\n🔍 OPTION PROCESSOR DEBUG:")
##        print(f"   Symbol: {symbol}")
##        print(f"   Signal Data: {signal_data}")
##        print(f"   Option Config Enabled: {Config.OPTION_TRADING_ENABLED}")
##        print(f"   In OPTION_SYMBOLS: {symbol in Config.OPTION_SYMBOLS}")
##        # ========================================
##        
##        # Check if option trading is enabled
##        if not Config.OPTION_TRADING_ENABLED:
##            print("❌ Option trading disabled in config")
##            return None
##        
##        # Check if we should trade options for this symbol
##        if symbol not in Config.OPTION_SYMBOLS:
##            print(f"❌ {symbol} not in OPTION_SYMBOLS: {Config.OPTION_SYMBOLS}")
##            return None
##
##        
##        
##        # Check cooldown
##        if not self.can_trade_option(symbol, current_time):
##            return None
##        
##        # Determine direction
##        direction = 'CALL' if signal_data.get('buy_call') else 'PUT' if signal_data.get('buy_put') else None
##        
##        if not direction:
##            return None
##        
##        underlying = symbol
##        
##        # Get current spot price
##        spot_price = self.get_spot_price(underlying)
##        if spot_price == 0:
##            print(f"⚠️ Cannot get spot price for {underlying}")
##            return None
##        
##        # Get option chain
##        expiry_index = Config.OPTION_EXPIRY
##        atm_strike, option_df = self.adapter.get_option_chain(underlying, expiry_index)
##        
##        if option_df is None or option_df.empty:
##            print(f"⚠️ No option chain for {underlying}")
##            return None
##        
##        # Select strike
##        otm_count = Config.OPTION_OTM_COUNT
##        option_symbol, strike, step = self.adapter.select_optimal_strike(
##            option_df, atm_strike, direction, otm_count
##        )
##        
##        if not option_symbol:
##            print(f"⚠️ No option symbol found for {underlying} {direction}")
##            return None
##        
##        # Get current premium
##        premium = self.get_premium(option_symbol)
##        if premium == 0:
##            print(f"⚠️ Cannot get premium for {option_symbol}")
##            return None
##        
##        # Calculate Greeks
##        greeks = self.manager.calculate_option_greeks(
##            option_symbol, spot_price, strike, direction
##        )
##        
##        # Greeks-based filters
##        # if greeks.delta < Config.MIN_DELTA_FOR_ENTRY:
##        #     print(f"❌ Delta too low: {greeks.delta:.2f} < {Config.MIN_DELTA_FOR_ENTRY}")
##        #     return None
##
##        if direction == 'CALL':
##            # For CALL options, delta should be between 0.3 and 0.7
##            if greeks.delta < 0.3 or greeks.delta > 0.7:
##                print(f"❌ Delta out of optimal range: {greeks.delta:.2f}")
##                return None
##        else:  # PUT
##            # For PUT options, delta should be between -0.7 and -0.3
##            if greeks.delta > -0.3 or greeks.delta < -0.7:
##                print(f"❌ Delta out of optimal range: {greeks.delta:.2f}")
##                return None
##        
##        if greeks.theta < Config.MAX_THETA_PER_DAY:
##            print(f"❌ Theta too negative: {greeks.theta:.2f}")
##            return None
##        
##        if greeks.iv < Config.MIN_IV_PERCENT or greeks.iv > Config.MAX_IV_PERCENT:
##            print(f"❌ IV out of range: {greeks.iv:.1f}%")
##            return None
##        
##        # Calculate position size
##        capital = self.execution.get_available_capital()
##        risk_amount = capital * Config.OPTION_RISK_PER_TRADE_PERCENT
##        
##        lot_size = self.adapter.get_lot_size(underlying)
##        max_lots_possible = int(risk_amount / (premium * lot_size))
##        lots = min(max_lots_possible, Config.OPTION_MAX_LOTS_PER_TRADE)
##        
##        if lots == 0:
##            print(f"⚠️ Risk amount too low for even 1 lot")
##            return None
##        
##        quantity = lots * lot_size
##        
##        # Calculate stop loss and targets
##        sl_data = self.manager.calculate_stop_loss(premium, premium, direction, 
##                                                    {'delta': greeks.delta, 'iv': greeks.iv})
##        target_data = self.manager.calculate_targets(premium, {'delta': greeks.delta}, direction, spot_price,stop_loss=sl_data['price_sl'])
##        
##        stop_loss = sl_data['price_sl']
##        target = target_data['target_1']
##        target_2 = target_data['target_2']
##        
##        print(f"\n{'='*60}")
##        print(f"🎯 OPTION TRADE SIGNAL")
##        print(f"{'='*60}")
##        print(f"   Underlying: {underlying} @ ₹{spot_price:,.2f}")
##        print(f"   Signal: {'CALL (Bullish)' if direction == 'CALL' else 'PUT (Bearish)'}")
##        print(f"   Option: {option_symbol}")
##        print(f"   Strike: {strike} ({otm_count} OTM)")
##        print(f"   Premium: ₹{premium:.2f}")
##        print(f"   Lots: {lots} (Qty: {quantity})")
##        print(f"   Total Risk: ₹{premium * quantity:.2f} ({Config.OPTION_RISK_PER_TRADE_PERCENT*100}% of capital)")
##        print(f"\n📊 GREEKS:")
##        print(f"   Delta: {greeks.delta:.3f} | Gamma: {greeks.gamma:.5f}")
##        print(f"   Theta: {greeks.theta:.2f} | Vega: {greeks.vega:.2f} | IV: {greeks.iv:.1f}%")
##        print(f"\n📉 RISK MANAGEMENT:")
##        print(f"   Stop Loss: ₹{stop_loss:.2f} ({sl_data['loss_percent']:.1f}% loss)")
##        print(f"   Target 1: ₹{target:.2f} ({target_data['profit_percent_1']:.1f}% profit)")
##        print(f"   Target 2: ₹{target_2:.2f} ({target_data['profit_percent_2']:.1f}% profit)")
##        print(f"{'='*60}")
##        
##        # Place order
##        order = self.place_option_order(
##            option_symbol=option_symbol,
##            action='BUY',
##            lots=lots,
##            quantity=quantity,
##            premium=premium,
##            stop_loss=stop_loss,
##            target=target,
##            target_2=target_2,
##            underlying=underlying,
##            strike=strike,
##            option_type=direction,
##            greeks={
##                'delta': greeks.delta,
##                'gamma': greeks.gamma,
##                'theta': greeks.theta,
##                'vega': greeks.vega,
##                'iv': greeks.iv
##            },
##            entry_spot=spot_price,
##            strategy=signal_data.get('triggering_strategy', 'OPTION_SIGNAL')
##        )
##        
##        if order:
##            self.record_trade(symbol, current_time)
##            
##            # Send Telegram alert
##            if Config.OPTION_ALERTS_ENABLED:
##                alert_msg = f"""🎯 OPTION TRADE ENTRY
##📊 {underlying} {direction} {strike}
##💵 Premium: ₹{premium:.2f}
##📦 Lots: {lots}
##🎯 Target: ₹{target:.2f} ({target_data['profit_percent_1']:.0f}%)
##🛑 Stop: ₹{stop_loss:.2f} ({sl_data['loss_percent']:.0f}%)
##📈 Delta: {greeks.delta:.2f} | IV: {greeks.iv:.0f}%"""
##                
##                if hasattr(self.execution, 'send_alert'):
##                    self.execution.send_alert(alert_msg)
##            
##            return order
##        
##        return None
##
##
##
##    def debug_option_calculation(self, underlying: str, spot_price: float, 
##                              option_symbol: str, strike: float, 
##                              premium: float, greeks: Dict, 
##                              otm_count: int, lots: int, quantity: int,
##                              sl_data: Dict, target_data: Dict):
##        """Detailed debug output for option calculations"""
##        
##        print("\n" + "="*80)
##        print(f"🎯 OPTION TRADE DEBUG - {underlying}")
##        print("="*80)
##        
##        # Market Data
##        print(f"\n📊 MARKET DATA:")
##        print(f"   Underlying: {underlying}")
##        print(f"   Spot Price: ₹{spot_price:,.2f}")
##        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
##        
##        # Option Selection
##        print(f"\n🔍 OPTION SELECTION:")
##        print(f"   Option Symbol: {option_symbol}")
##        print(f"   Strike Price: {strike}")
##        print(f"   OTM Count: {otm_count}")
##        print(f"   Option Type: {'CALL' if 'CE' in option_symbol else 'PUT'}")
##        
##        # Premium & Pricing
##        print(f"\n💰 PRICING:")
##        print(f"   Entry Premium: ₹{premium:.2f}")
##        print(f"   Lot Size: {self.adapter.get_lot_size(underlying)}")
##        print(f"   Lots: {lots}")
##        print(f"   Total Quantity: {quantity}")
##        print(f"   Total Premium Value: ₹{premium * quantity:.2f}")
##        
##        # Greeks
##        print(f"\n📈 GREEKS:")
##        print(f"   Delta: {greeks.get('delta', 0):.4f} {'✓ (0.3-0.7 optimal)' if 0.3 <= abs(greeks.get('delta', 0)) <= 0.7 else '⚠️ (outside optimal range)'}")
##        print(f"   Gamma: {greeks.get('gamma', 0):.6f}")
##        print(f"   Theta: {greeks.get('theta', 0):.2f} {'⚠️ (high decay)' if greeks.get('theta', 0) < -10 else '✓'}")
##        print(f"   Vega: {greeks.get('vega', 0):.2f}")
##        print(f"   IV: {greeks.get('iv', 0):.1f}% {'✓' if 12 <= greeks.get('iv', 0) <= 40 else '⚠️'}")
##        
##        # Risk Management
##        print(f"\n🛑 RISK MANAGEMENT:")
##        print(f"   Stop Loss Price: ₹{sl_data.get('price_sl', 0):.2f}")
##        print(f"   Stop Loss Type: {sl_data.get('stop_type', 'N/A')}")
##        print(f"   Max Loss: ₹{sl_data.get('loss_amount', 0):.2f} ({sl_data.get('loss_percent', 0):.1f}%)")
##        print(f"   Capital at Risk: {sl_data.get('loss_percent', 0):.1f}% of balance")
##        
##        # Profit Targets
##        print(f"\n🎯 PROFIT TARGETS:")
##        print(f"   Target 1 (Book 50%): ₹{target_data.get('target_1', 0):.2f} ({target_data.get('profit_percent_1', 0):.0f}% profit)")
##        print(f"   Target 2 (Book 30%): ₹{target_data.get('target_2', 0):.2f} ({target_data.get('profit_percent_2', 0):.0f}% profit)")
##        print(f"   Moon Target (Trail): ₹{target_data.get('moon_target', 0):.2f}")
##        print(f"   Risk/Reward Ratio: 1:{target_data.get('risk_reward_ratio', 0)}")
##        
##        # Position Details
##        print(f"\n📦 POSITION DETAILS:")
##        print(f"   Margin Required: ₹{premium * quantity * 0.2:.2f}")
##        print(f"   Available Balance: ₹{self.execution.get_available_capital():,.2f}")
##        print(f"   Balance After Trade: ₹{self.execution.get_available_capital() - (premium * quantity * 0.2):,.2f}")
##        
##        print("="*80 + "\n")
##
##
##
##    def process_signal_for_option(self, signal_data: Dict, chart: pd.DataFrame, 
##                               symbol: str, current_time: datetime) -> Optional[Dict]:
##        """
##        Process a trading signal and convert to option trade - WITH FULL DEBUG
##        """
##        
##        print(f"\n{'='*60}")
##        print(f"🔍 OPTION SIGNAL PROCESSING STARTED")
##        print(f"   Symbol: {symbol}")
##        print(f"   Time: {current_time.strftime('%H:%M:%S')}")
##        print(f"{'='*60}")
##        
##        # Check if option trading is enabled
##        from config import Config
##        if not Config.OPTION_TRADING_ENABLED:
##            print("❌ Option trading is DISABLED in config")
##            return None
##        
##        # Check if we should trade options for this symbol
##        if symbol not in Config.OPTION_SYMBOLS:
##            print(f"❌ {symbol} not in OPTION_SYMBOLS: {Config.OPTION_SYMBOLS}")
##            return None
##        
##        # Determine direction
##        direction = 'CALL' if signal_data.get('buy_call') else 'PUT' if signal_data.get('buy_put') else None
##        
##        print(f"📊 Signal Direction: {direction}")
##        print(f"   Triggering Strategy: {signal_data.get('triggering_strategy', 'Unknown')}")
##        
##        if not direction:
##            print("❌ No valid direction (neither CALL nor PUT)")
##            return None
##        
##        underlying = symbol
##        
##        # Get current spot price
##        spot_price = self.get_spot_price(underlying)
##        print(f"📍 Spot Price: ₹{spot_price:,.2f}")
##        
##        if spot_price == 0:
##            print("❌ Cannot get spot price")
##            return None
##        
##        # Get option chain
##        expiry_index = Config.OPTION_EXPIRY
##        print(f"📅 Fetching option chain (Expiry Index: {expiry_index})...")
##        
##        atm_strike, option_df = self.adapter.get_option_chain(underlying, expiry_index)
##        
##        if option_df is None or option_df.empty:
##            print("❌ No option chain data available")
##            return None
##        
##        print(f"✅ Option chain loaded. ATM Strike: {atm_strike}")
##        print(f"   DataFrame shape: {option_df.shape}")
##        
##        # Select strike
##        otm_count = Config.OPTION_OTM_COUNT
##        print(f"🎯 Selecting strike (OTM Count: {otm_count})...")
##        
##        option_symbol, strike, step = self.adapter.select_optimal_strike(
##            option_df, atm_strike, direction, otm_count
##        )
##        
##        if not option_symbol:
##            print(f"❌ No option symbol found for {underlying} {direction}")
##            return None
##        
##        print(f"✅ Selected Option: {option_symbol}")
##        print(f"   Strike: {strike} | Step: {step}")
##        
##        # Get current premium
##        premium = self.get_premium(option_symbol)
##        print(f"💰 Current Premium: ₹{premium:.2f}")
##        
##        if premium == 0:
##            print("❌ Cannot get premium for option")
##            return None
##        
##        # Calculate Greeks
##        print(f"📊 Calculating Greeks...")
##        greeks = self.manager.calculate_option_greeks(
##            option_symbol, spot_price, strike, direction
##        )
##        
##        print(f"   Delta: {greeks.delta:.4f}")
##        print(f"   Gamma: {greeks.gamma:.6f}")
##        print(f"   Theta: {greeks.theta:.2f}")
##        print(f"   Vega: {greeks.vega:.2f}")
##        print(f"   IV: {greeks.iv:.1f}%")
##        
##        # Greeks-based filters
##        if direction == 'CALL':
##            if greeks.delta < 0.3 or greeks.delta > 0.7:
##                print(f"❌ Delta out of optimal range for CALL: {greeks.delta:.2f} (should be 0.3-0.7)")
##                return None
##        else:
##            if greeks.delta > -0.3 or greeks.delta < -0.7:
##                print(f"❌ Delta out of optimal range for PUT: {greeks.delta:.2f} (should be -0.7 to -0.3)")
##                return None
##        
##        print("✅ Delta filter passed")
##        
##        if greeks.theta < Config.MAX_THETA_PER_DAY:
##            print(f"❌ Theta too negative: {greeks.theta:.2f} < {Config.MAX_THETA_PER_DAY}")
##            return None
##        
##        print("✅ Theta filter passed")
##        
##        if greeks.iv < Config.MIN_IV_PERCENT or greeks.iv > Config.MAX_IV_PERCENT:
##            print(f"❌ IV out of range: {greeks.iv:.1f}% (should be {Config.MIN_IV_PERCENT}-{Config.MAX_IV_PERCENT}%)")
##            return None
##        
##        print("✅ IV filter passed")
##        
##        # Calculate position size
##        capital = self.execution.get_available_capital()
##        risk_amount = capital * Config.OPTION_RISK_PER_TRADE_PERCENT
##        
##        lot_size = self.adapter.get_lot_size(underlying)
##        max_lots_possible = int(risk_amount / (premium * lot_size))
##        lots = min(max_lots_possible, Config.OPTION_MAX_LOTS_PER_TRADE)
##        
##        print(f"\n📦 POSITION SIZING:")
##        print(f"   Available Capital: ₹{capital:,.2f}")
##        print(f"   Risk Amount ({(Config.OPTION_RISK_PER_TRADE_PERCENT*100)}%): ₹{risk_amount:.2f}")
##        print(f"   Lot Size: {lot_size}")
##        print(f"   Premium per Lot: ₹{premium * lot_size:.2f}")
##        print(f"   Max Lots Possible: {max_lots_possible}")
##        print(f"   Selected Lots: {lots} (Max allowed: {Config.OPTION_MAX_LOTS_PER_TRADE})")
##        
##        if lots == 0:
##            print("❌ Risk amount too low for even 1 lot")
##            return None
##        
##        quantity = lots * lot_size
##        
##        # Calculate stop loss and targets
##        print(f"\n📉 CALCULATING STOP LOSS...")
##        sl_data = self.manager.calculate_stop_loss(premium, premium, direction, 
##                                                    {'delta': greeks.delta, 'iv': greeks.iv})
##        
##        print(f"\n🎯 CALCULATING TARGETS...")
##        target_data = self.manager.calculate_targets(premium, {'delta': greeks.delta}, direction, spot_price, stop_loss=sl_data['price_sl'])
##        
##        stop_loss = sl_data['price_sl']
##        target = target_data['target_1']
##        target_2 = target_data['target_2']
##        
##        # Call the debug method
##        self.debug_option_calculation(
##            underlying, spot_price, option_symbol, strike, premium, 
##            {'delta': greeks.delta, 'gamma': greeks.gamma, 'theta': greeks.theta, 
##             'vega': greeks.vega, 'iv': greeks.iv},
##            otm_count, lots, quantity, sl_data, target_data
##        )
##        
##        # Place order
##        print(f"\n🚀 PLACING OPTION ORDER...")
##        order = self.place_option_order(
##            option_symbol=option_symbol,
##            action='BUY',
##            lots=lots,
##            quantity=quantity,
##            premium=premium,
##            stop_loss=stop_loss,
##            target=target,
##            target_2=target_2,
##            underlying=underlying,
##            strike=strike,
##            option_type=direction,
##            greeks={
##                'delta': greeks.delta,
##                'gamma': greeks.gamma,
##                'theta': greeks.theta,
##                'vega': greeks.vega,
##                'iv': greeks.iv
##            },
##            entry_spot=spot_price,
##            strategy=signal_data.get('triggering_strategy', 'OPTION_SIGNAL')
##        )
##        
##        if order:
##            print(f"\n✅ OPTION ORDER PLACED SUCCESSFULLY!")
##            print(f"   Order ID: {order.get('super_order_id', 'N/A')}")
##            print(f"   Check Dhan platform for order status")
##            
##            # Send Telegram alert
##            if Config.OPTION_ALERTS_ENABLED:
##                alert_msg = f"""🎯 OPTION TRADE ENTRY
##    📊 {underlying} {direction} {strike}
##    💵 Premium: ₹{premium:.2f}
##    📦 Lots: {lots}
##    🎯 Target: ₹{target:.2f} ({target_data['profit_percent_1']:.0f}%)
##    🛑 Stop: ₹{stop_loss:.2f} ({sl_data['loss_percent']:.0f}%)
##    📈 Delta: {greeks.delta:.2f} | IV: {greeks.iv:.0f}%"""
##                
##                if hasattr(self.execution, 'send_alert'):
##                    self.execution.send_alert(alert_msg)
##            
##            return order
##        
##        print("❌ Order placement failed")
##        return None
##
##
##
##    def monitor_option_position(self, symbol: str):
##        """Monitor open option position with detailed logging"""
##        if symbol not in self.orderbook:
##            return
##        
##        position = self.orderbook[symbol]
##        
##        # Skip if not an option position
##        if 'option_type' not in position:
##            # Handle equity position
##            self.monitor_open_positions(symbol)
##            return
##        
##        # Get current data
##        if not self.option_processor:
##            return
##        
##        current_premium = self.option_processor.get_premium(position['name'])
##        if current_premium == 0:
##            return
##        
##        current_spot = self.option_processor.get_spot_price(position.get('underlying', 'NIFTY'))
##        entry_spot = position.get('entry_spot', current_spot)
##        entry_premium = position.get('entry_price', 0)
##        
##        # Calculate P&L
##        if position.get('option_type') == 'CALL':
##            pnl = (current_premium - entry_premium) * position.get('qty', 0)
##            pnl_percent = ((current_premium - entry_premium) / entry_premium * 100) if entry_premium > 0 else 0
##        else:
##            pnl = (entry_premium - current_premium) * position.get('qty', 0)
##            pnl_percent = ((entry_premium - current_premium) / entry_premium * 100) if entry_premium > 0 else 0
##        
##        # Calculate holding time
##        holding_minutes = 0
##        if 'entry_time' in position and position.get('date'):
##            try:
##                entry_datetime_str = f"{position['date']} {position['entry_time']}"
##                entry_datetime = datetime.strptime(entry_datetime_str, '%Y-%m-%d %H:%M:%S')
##                if Config.IST:
##                    entry_datetime = Config.IST.localize(entry_datetime)
##                holding_minutes = (Config.get_current_time() - entry_datetime).total_seconds() / 60
##                position['holding_minutes'] = holding_minutes
##            except Exception as e:
##                print(f"Time calculation error: {e}")
##        
##        # Detailed position monitoring
##        print(f"\n{'='*60}")
##        print(f"📊 OPTION POSITION MONITORING - {position.get('name')}")
##        print(f"{'='*60}")
##        print(f"   Underlying: {position.get('underlying')} @ ₹{current_spot:,.2f}")
##        print(f"   Option Type: {position.get('option_type')}")
##        print(f"   Strike: {position.get('strike')}")
##        print(f"   Entry Premium: ₹{entry_premium:.2f}")
##        print(f"   Current Premium: ₹{current_premium:.2f}")
##        print(f"   Change: ₹{current_premium - entry_premium:+.2f} ({pnl_percent:+.1f}%)")
##        print(f"   P&L: ₹{pnl:+,.2f}")
##        print(f"   Holding Time: {holding_minutes:.0f} minutes")
##        print(f"   Stop Loss: ₹{position.get('sl', 0):.2f}")
##        print(f"   Target 1: ₹{position.get('target', 0):.2f}")
##        print(f"   Target 2: ₹{position.get('target_2', 0):.2f}")
##        
##        # Greeks if available
##        if 'greeks' in position:
##            g = position['greeks']
##            print(f"   Delta: {g.get('delta', 0):.4f} | Theta: {g.get('theta', 0):.2f}")
##            print(f"   Gamma: {g.get('gamma', 0):.6f} | Vega: {g.get('vega', 0):.2f}")
##        
##        print(f"{'='*60}\n")
##        
##        # Check stop loss
##        stop_hit, stop_reason = self.option_processor.manager.check_stop_loss(
##            position, current_premium, current_spot, entry_spot
##        )
##        
##        if stop_hit:
##            print(f"🔴 STOP LOSS TRIGGERED: {stop_reason}")
##            self._close_option_position(symbol, current_premium, stop_reason)
##            return
##        
##        # Check targets
##        target_hit, target_reason, exit_price = self.option_processor.manager.check_targets(
##            position, current_premium, current_spot
##        )
##        
##        if target_hit:
##            print(f"🟢 TARGET HIT: {target_reason}")
##            if position.get('partial_booked', False):
##                print(f"   Partial booking already done. Closing remaining...")
##            self._close_option_position(symbol, exit_price, target_reason)
##            return
##        
##        # Update trailing stop
##        current_delta = position.get('greeks', {}).get('delta', 0.5)
##        new_sl = self.option_processor.manager.update_trailing_stop(
##            position['name'], current_premium, position['entry_price'], current_delta
##        )
##        
##        if new_sl and new_sl > position.get('sl', 0):
##            position['sl'] = new_sl
##            print(f"📈 TRAILING STOP UPDATED: New SL ₹{new_sl:.2f}")
##        
##
##
##    
##    
##    def place_option_order(self, option_symbol: str, action: str, lots: int, quantity: int,
##                           premium: float, stop_loss: float, target: float, target_2: float,
##                           underlying: str, strike: float, option_type: str,
##                           greeks: Dict, entry_spot: float, strategy: str) -> Optional[Dict]:
##        """Place the actual option order"""
##        
##        try:
##            # Use Dhan's super order for bracket orders
##            super_order_id = self.tsl.place_super_order(
##                tradingsymbol=option_symbol,
##                exchange='NFO',
##                transaction_type=action,
##                quantity=quantity,
##                order_type='MARKET',
##                trade_type='MIS',
##                price=0,
##                target_price=target,
##                stop_loss_price=stop_loss,
##                trailing_jump=0
##            )
##            
##            if super_order_id:
##                from config import Config
##                current_time = datetime.now(Config.IST)
##                
##                order = {
##                    'name': option_symbol,
##                    'option_type': option_type,
##                    'underlying': underlying,
##                    'strike': strike,
##                    'lots': lots,
##                    'qty': quantity,
##                    'entry_price': premium,
##                    'sl': stop_loss,
##                    'target': target,
##                    'target_2': target_2,
##                    'strategy': strategy,
##                    'super_order_id': super_order_id,
##                    'entry_time': current_time.strftime('%H:%M:%S'),
##                    'date': str(current_time.date()),
##                    'position_type': 'LONG',
##                    'buy_sell': action,
##                    'greeks': greeks,
##                    'entry_spot': entry_spot,
##                    'highest_premium': premium,
##                    'partial_booked': False,
##                    'order_type': 'OPTION_SUPER',
##                    'status': 'open'
##                }
##                
##                print(f"\n✅ OPTION ORDER PLACED!")
##                print(f"   Order ID: {super_order_id}")
##                print(f"   Monitor in dashboard")
##                
##                return order
##            
##            return None
##            
##        except Exception as e:
##            print(f"❌ Option order failed: {e}")
##            import traceback
##            traceback.print_exc()
##            return None
