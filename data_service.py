# data_service.py
import pandas as pd
import requests
from typing import Optional
from config import Config

class DataService:
    def __init__(self, tsl):
        self.tsl = tsl
    
##    def get_symbol_data(self, symbol: str, retries: int = 3) -> Optional[pd.DataFrame]:
##        """Fetch historical data with retries"""
##        print(f"📈 Fetching data for {symbol}...")
##        exchange_options = self._get_exchange_options(symbol)
##        
##        for attempt in range(retries):
##            for exchange in exchange_options:
##                try:
##                    chart = self.tsl.get_historical_data(
##                        tradingsymbol=symbol, exchange=exchange, timeframe=Config.TIMEFRAME
##                    )
##                    print (chart)
##                    if self._validate_data(chart):
##                        return chart
##                except Exception:
##                    continue
##        return None


    def get_symbol_data(self, symbol: str, retries: int = 3) -> Optional[pd.DataFrame]:
        """Fetch historical data with retries"""
        print(f"📈 Fetching data for {symbol}...")
        MAX_CANDLES = 500
        
        # For indexes, use correct symbol names
        if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']:
            exchange_options = ["INDEX"]
            print(f"   🔍 Detected INDEX symbol: {symbol}")
        else:
            exchange_options = ["NSE", "BSE", "NFO"]
            print(f"   🔍 Detected EQUITY symbol: {symbol}")
        
        for attempt in range(retries):
            for exchange in exchange_options:
                try:
                    print(f"   📡 Attempt {attempt+1}, exchange={exchange}, timeframe={Config.TIMEFRAME}")
                    
                    chart = self.tsl.get_historical_data(
                        tradingsymbol=symbol,
                        exchange=exchange, 
                        timeframe=Config.TIMEFRAME
                    )
                    
                    print(f"   📊 Raw data type: {type(chart)}")
                    
                    if chart is None:
                        print(f"   ⚠️ No data returned for {symbol} on {exchange}")
                        continue
                        
                    if isinstance(chart, pd.DataFrame):
                        print(f"   📊 DataFrame shape: {chart.shape}")
                        if not chart.empty:
                            print(f"   📊 Last close: ₹{chart['close'].iloc[-1]:.2f}")
                            print(f"   📊 Date range: {chart['timestamp'].iloc[0]} to {chart['timestamp'].iloc[-1]}")
                    
                    if self._validate_data(chart):
                        # ============ ADD THESE 3 LINES HERE ============
                        # Limit to last MAX_CANDLES to prevent memory leak
                        if len(chart) > MAX_CANDLES:
                            chart = chart.tail(MAX_CANDLES)
                            print(f"   📊 Trimmed to last {MAX_CANDLES} candles (was {len(chart) + (chart.shape[0] - MAX_CANDLES)})")
                        # ================================================
                        
                        print(f"   ✅ Data validated for {symbol}")
                        return chart
                    else:
                        print(f"   ⚠️ Data validation failed for {symbol} on {exchange}")

                        
                except Exception as e:
                    print(f"   ❌ Attempt {attempt+1}, exchange {exchange} failed: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        print(f"❌ Failed to get data for {symbol} after {retries} attempts")
        return None
    
    
##    def get_current_price(self, symbol: str) -> Optional[float]:
##        """Get current LTP with error handling - FIXED for indices"""
##        try:
##            # Try direct API call for indices
##            token = None
##            if hasattr(self.tsl, 'token_id'):
##                token = self.tsl.token_id
##            elif hasattr(self.tsl, 'access_token'):
##                token = self.tsl.access_token
##                
##            if token:
##                # Map symbols to security IDs
##                security_ids = {
##                    "NIFTY": "13",
##                    "BANKNIFTY": "25",
##                    "FINNIFTY": "27",
##                    "SENSEX": "51"
##                }
##                
##                if symbol in security_ids:
##                    url = "https://api.dhan.co/v2/marketfeed/ohlc"
##                    payload = {"IDX_I": [int(security_ids[symbol])]}
##                    headers = {
##                        "access-token": token,
##                        "client-id": Config.CLIENT_CODE,
##                        "Content-Type": "application/json"
##                    }
##                    response = requests.post(url, json=payload, headers=headers, timeout=5)
##                    if response.status_code == 200:
##                        data = response.json()
##                        sec_data = data.get("data", {}).get("IDX_I", {}).get(security_ids[symbol], {})
##                        ltp = sec_data.get("last_price", 0)
##                        if ltp > 0:
##                            return float(ltp)
##            
##            # Fallback to tsl method
##            ltp_data = self.tsl.get_ltp_data(names=[symbol])
##            if ltp_data and symbol in ltp_data:
##                return ltp_data[symbol]
##            
##            # Return default values
##            defaults = {
##                "NIFTY": 20000,
##                "BANKNIFTY": 20000,
##                "FINNIFTY": 20000,
##                "SENSEX": 20000
##            }
##            return defaults.get(symbol, None)
##            
##        except Exception as e:
##            print(f"⚠️ LTP error for {symbol}: {e}")
##            defaults = {
##                "NIFTY": 20000,
##                "BANKNIFTY": 20000,
##                "FINNIFTY": 20000,
##                "SENSEX": 20000
##            }
##            return defaults.get(symbol, None)

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current LTP using reliable method"""
        return self.get_reliable_ltp(symbol)


    
    def _get_exchange_options(self, symbol: str) -> list:
        """Get exchange options based on symbol type"""
        symbol = str(symbol).upper()
        
        # For indices, use INDEX exchange first
        if symbol in Config.FNO_WATCHLIST:
            return ["INDEX", "NSE", "BSE"]
        
        # For equities
        if symbol in Config.EQUITY_WATCHLIST:
            return ["NSE", "BSE", "NFO"]
        
        # Default
        return ["NSE", "BSE", "NFO", "INDEX"]
    
    def _validate_data(self, chart) -> bool:
        if not isinstance(chart, pd.DataFrame) or len(chart) < 20:
            return False
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in chart.columns for col in required_cols)



    # data_service.py - Add this method
    def get_reliable_ltp(self, symbol: str) -> Optional[float]:
        """Get LTP using reliable method - bypasses the bug in get_ltp_data"""
        try:
            # Method 1: Use get_ohlc_data which works reliably
            ohlc_data = self.tsl.get_ohlc_data(names=[symbol])
            if ohlc_data and symbol in ohlc_data:
                data = ohlc_data[symbol]
                if isinstance(data, dict) and 'last_price' in data:
                    return float(data['last_price'])
            
            # Method 2: Try get_ltp_data directly
            ltp_data = self.tsl.get_ltp_data(names=[symbol])
            if ltp_data and symbol in ltp_data:
                return float(ltp_data[symbol])
            
            # Method 3: Direct API call for indices
            token = None
            if hasattr(self.tsl, 'token_id'):
                token = self.tsl.token_id
            elif hasattr(self.tsl, 'access_token'):
                token = self.tsl.access_token
                
            if token:
                security_ids = {
                    "NIFTY": "13",
                    "BANKNIFTY": "25", 
                    "FINNIFTY": "27",
                    "SENSEX": "51"
                }
                if symbol in security_ids:
                    import requests
                    url = "https://api.dhan.co/v2/marketfeed/ohlc"
                    payload = {"IDX_I": [int(security_ids[symbol])]}
                    headers = {
                        "access-token": token,
                        "client-id": Config.CLIENT_CODE,
                        "Content-Type": "application/json"
                    }
                    response = requests.post(url, json=payload, headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        sec_data = data.get("data", {}).get("IDX_I", {}).get(security_ids[symbol], {})
                        ltp = sec_data.get("last_price", 0)
                        if ltp > 0:
                            return float(ltp)
            
            # Return default values for indices
            defaults = {
                "NIFTY": 20000,
                "BANKNIFTY": 20000,
                "FINNIFTY": 20000,
                "SENSEX": 20000
            }
            return defaults.get(symbol, None)
            
        except Exception as e:
            print(f"⚠️ Reliable LTP error for {symbol}: {e}")
            return None
    



    
