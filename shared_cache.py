# shared_cache.py - Single cache for all API data to prevent rate limiting
import time
import threading
from typing import Dict, Optional, List, Any
from datetime import datetime

class SharedCache:
    """
    Singleton cache that all modules can use.
    Prevents duplicate API calls and rate limiting.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache = {}
        self._cache_time = {}
        
        # Cache TTLs (seconds)
        self.TTL = {
            'ltp': 5,           # LTP updates every 5 seconds
            'premium': 10,      # Option premium every 10 seconds
            'option_chain': 30, # Option chain every 30 seconds
            'spot': 5,          # Spot price every 5 seconds
            'index': 10,        # Index data every 10 seconds
            'position': 15,     # Positions every 15 seconds
            'balance': 60,      # Balance every minute
        }
        
        print("✅ SharedCache initialized")
    
    def _get_cache_key(self, data_type: str, *args, **kwargs) -> str:
        """Generate cache key"""
        key_parts = [data_type]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)
    
    def _is_valid(self, key: str, data_type: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache_time:
            return False
        age = time.time() - self._cache_time[key]
        return age < self.TTL.get(data_type, 30)
    
    def _set(self, key: str, data: Any, data_type: str):
        """Store data in cache"""
        self._cache[key] = data
        self._cache_time[key] = time.time()
    
    def _get(self, key: str, data_type: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self._is_valid(key, data_type):
            return self._cache.get(key)
        return None
    
    # ============ LTP / Premium Methods ============
    
    def get_ltp(self, symbol: str) -> Optional[float]:
        """Get cached LTP for symbol"""
        key = self._get_cache_key('ltp', symbol)
        return self._get(key, 'ltp')
    
    def set_ltp(self, symbol: str, price: float):
        """Cache LTP for symbol"""
        key = self._get_cache_key('ltp', symbol)
        self._set(key, price, 'ltp')
    
    def get_ltp_batch(self, symbols: List[str]) -> Dict[str, float]:
        """Get cached LTP for multiple symbols"""
        result = {}
        for sym in symbols:
            val = self.get_ltp(sym)
            if val is not None:
                result[sym] = val
        return result
    
    # ============ Option Premium Methods ============
    
    def get_premium(self, option_symbol: str) -> Optional[float]:
        """Get cached option premium"""
        key = self._get_cache_key('premium', option_symbol)
        return self._get(key, 'premium')
    
    def set_premium(self, option_symbol: str, premium: float):
        """Cache option premium"""
        key = self._get_cache_key('premium', option_symbol)
        self._set(key, premium, 'premium')
    
    # ============ Option Chain Methods ============
    
    def get_option_chain(self, underlying: str, expiry: int = 0) -> Optional[Dict]:
        """Get cached option chain data"""
        key = self._get_cache_key('option_chain', underlying, expiry)
        return self._get(key, 'option_chain')
    
    def set_option_chain(self, underlying: str, expiry: int, data: Dict):
        """Cache option chain data"""
        key = self._get_cache_key('option_chain', underlying, expiry)
        self._set(key, data, 'option_chain')
    
    def get_strikes(self, underlying: str) -> Optional[List]:
        """Get cached strikes data"""
        key = self._get_cache_key('strikes', underlying)
        return self._get(key, 'option_chain')
    
    def set_strikes(self, underlying: str, strikes: List):
        """Cache strikes data"""
        key = self._get_cache_key('strikes', underlying)
        self._set(key, strikes, 'option_chain')
    
    # ============ Spot Price Methods ============
    
    def get_spot(self, underlying: str) -> Optional[float]:
        """Get cached spot price"""
        key = self._get_cache_key('spot', underlying)
        return self._get(key, 'spot')
    
    def set_spot(self, underlying: str, price: float):
        """Cache spot price"""
        key = self._get_cache_key('spot', underlying)
        self._set(key, price, 'spot')
    
    # ============ PCR (Put/Call Ratio) Methods ============
    
    def get_pcr(self, underlying: str) -> Optional[float]:
        """Get cached PCR"""
        key = self._get_cache_key('pcr', underlying)
        return self._get(key, 'option_chain')
    
    def set_pcr(self, underlying: str, pcr: float):
        """Cache PCR"""
        key = self._get_cache_key('pcr', underlying)
        self._set(key, pcr, 'option_chain')
    
    # ============ VIX Methods ============
    
    def get_vix(self) -> Optional[float]:
        """Get cached VIX"""
        key = self._get_cache_key('vix')
        return self._get(key, 'index')
    
    def set_vix(self, vix: float):
        """Cache VIX"""
        key = self._get_cache_key('vix')
        self._set(key, vix, 'index')
    
    # ============ Index Data Methods ============
    
    def get_index_data(self, index_name: str) -> Optional[Dict]:
        """Get cached index data"""
        key = self._get_cache_key('index', index_name)
        return self._get(key, 'index')
    
    def set_index_data(self, index_name: str, data: Dict):
        """Cache index data"""
        key = self._get_cache_key('index', index_name)
        self._set(key, data, 'index')
    
    # ============ Balance Methods ============
    
    def get_balance(self) -> Optional[float]:
        """Get cached balance"""
        key = self._get_cache_key('balance')
        return self._get(key, 'balance')
    
    def set_balance(self, balance: float):
        """Cache balance"""
        key = self._get_cache_key('balance')
        self._set(key, balance, 'balance')
    
    # ============ Utility Methods ============
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._cache_time.clear()
        print("🗑️ Cache cleared")
    
    def clear_expired(self):
        """Remove expired cache entries"""
        now = time.time()
        to_remove = []
        for key, ts in self._cache_time.items():
            # Determine data_type from key
            data_type = key.split('|')[0] if '|' in key else 'default'
            ttl = self.TTL.get(data_type, 30)
            if now - ts > ttl:
                to_remove.append(key)
        for key in to_remove:
            del self._cache[key]
            del self._cache_time[key]
        if to_remove:
            print(f"🗑️ Cleared {len(to_remove)} expired cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'total_entries': len(self._cache),
            'keys': list(self._cache.keys())[:10],  # First 10 keys
            'ttl_settings': self.TTL
        }


# Global singleton instance
_shared_cache = None

def get_shared_cache() -> SharedCache:
    """Get or create shared cache instance"""
    global _shared_cache
    if _shared_cache is None:
        _shared_cache = SharedCache()
    return _shared_cache
