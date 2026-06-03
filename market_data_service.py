# market_data_service.py - Market Data Service for Live Indices
import requests
from config import Config

class MarketDataService:
    def __init__(self, tsl):
        self.tsl = tsl
    
    def get_index_prices(self):
        """Get live index prices for NIFTY, BANKNIFTY, FINNIFTY, SENSEX, VIX"""
        
        # All indices with their security IDs
        indices_config = {
            "NIFTY 50": {"security_id": "13", "exchange": "IDX_I"},
            "BANKNIFTY": {"security_id": "25", "exchange": "IDX_I"},
            "FINNIFTY": {"security_id": "27", "exchange": "IDX_I"},
            "SENSEX": {"security_id": "51", "exchange": "IDX_I"},
            "INDIA VIX": {"security_id": "105", "exchange": "IDX_I"}
        }
        
        results = {}
        
        # Try to get token from tsl
        token = None
        if hasattr(self.tsl, 'token_id'):
            token = self.tsl.token_id
        elif hasattr(self.tsl, 'access_token'):
            token = self.tsl.access_token
        
        if not token:
            return self._get_mock_data()
        
        try:
            url = "https://api.dhan.co/v2/marketfeed/ohlc"
            headers = {
                "access-token": token,
                "client-id": Config.CLIENT_CODE,
                "Content-Type": "application/json"
            }
            
            # Batch request for all indices
            payload = {"IDX_I": [13, 25, 27, 51, 105]}
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                idx_data = data.get("data", {}).get("IDX_I", {})
                
                for sec_id, sec_data in idx_data.items():
                    # Map security ID to name
                    name_map = {
                        "13": "NIFTY 50",
                        "25": "BANKNIFTY",
                        "27": "FINNIFTY",
                        "51": "SENSEX",
                        "105": "INDIA VIX"
                    }
                    name = name_map.get(sec_id, sec_id)
                    
                    ltp = sec_data.get("last_price", 0)
                    prev_close = sec_data.get("ohlc", {}).get("close", ltp)
                    change = ltp - prev_close if prev_close else 0
                    change_percent = (change / prev_close * 100) if prev_close else 0
                    
                    results[name] = {
                        "ltp": ltp,
                        "change": change,
                        "change_percent": change_percent,
                        "open": sec_data.get("ohlc", {}).get("open", 0),
                        "high": sec_data.get("ohlc", {}).get("high", 0),
                        "low": sec_data.get("ohlc", {}).get("low", 0)
                    }
                
                return results
            else:
                print(f"Market API error: {response.status_code}")
                return self._get_mock_data()
                
        except Exception as e:
            print(f"Market API exception: {e}")
            return self._get_mock_data()
    
    def _get_mock_data(self):
        """Return mock data when no token available"""
        return {
            "NIFTY 50": {"ltp": 20000.50, "change": 120.30, "change_percent": 0.49},
            "BANKNIFTY": {"ltp": 50000.00, "change": 350.75, "change_percent": 0.68},
            "FINNIFTY": {"ltp": 20000.25, "change": 150.50, "change_percent": 0.69},
            "SENSEX": {"ltp": 80000.00, "change": 250.00, "change_percent": 0.31}
        }
    
    def _get_default_index_data(self, name):
        """Return default data for an index"""
        defaults = {
            "NIFTY 50": {"ltp": 24500, "change": 0, "change_percent": 0},
            "BANKNIFTY": {"ltp": 52100, "change": 0, "change_percent": 0},
            "FINNIFTY": {"ltp": 21800, "change": 0, "change_percent": 0},
            "SENSEX": {"ltp": 80500, "change": 0, "change_percent": 0}
        }
        return defaults.get(name, {"ltp": 0, "change": 0, "change_percent": 0})
