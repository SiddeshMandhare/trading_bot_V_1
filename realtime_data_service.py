# realtime_data_service.py - Smart Real-time Data Service with Caching
import threading
import time
import json
import sqlite3
import datetime
from typing import Dict, Optional, List
from collections import defaultdict
from dataclasses import dataclass, asdict
from functools import wraps

# Try to import Dhan WebSocket if available
try:
    from dhanhq import DhanContext, FullDepth
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("⚠️ WebSocket not available, using polling mode")

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    ltp: float
    open: float
    high: float
    low: float
    prev_close: float
    change: float
    change_percent: float
    volume: int
    timestamp: str
    bid_price: float
    ask_price: float
    bid_qty: int
    ask_qty: int

class RealtimeDataService:
    """
    Smart Real-time Data Service with:
    - Intelligent caching (5-30 second TTL based on data type)
    - Batch API calls (reduce multiple calls)
    - WebSocket support for instant updates
    - Rate limit protection
    - Persistent storage for historical data
    """
    
    def __init__(self, tsl, config):
        self.tsl = tsl
        self.config = config
        self.cache = {}
        self.cache_timestamps = {}
        self.lock = threading.Lock()
        self.call_count = defaultdict(int)
        self.last_reset_time = time.time()
        
        # Cache TTLs (seconds)
        self.TTL = {
            'ltp': 5,           # LTP updates every 5 seconds
            'quote': 10,        # Full quote every 10 seconds
            'ohlc': 30,         # OHLC every 30 seconds
            'index': 10,        # Index data every 10 seconds
            'positions': 15,    # Positions every 15 seconds
            'balance': 60,      # Balance every minute
        }
        
        # WebSocket connection
        self.ws_connected = False
        self.ws_callbacks = []
        
        print("🚀 RealtimeDataService initialized")
        print(f"   Cache TTLs: {self.TTL}")
        
    def _check_rate_limit(self, call_type: str) -> bool:
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Reset counters every minute
        if current_time - self.last_reset_time > 60:
            self.call_count.clear()
            self.last_reset_time = current_time
        
        # Rate limits per minute
        limits = {
            'ltp': 300,      # 300 LTP calls per minute
            'quote': 100,    # 100 quote calls per minute  
            'ohlc': 50,      # 50 OHLC calls per minute
            'index': 100,    # 100 index calls per minute
        }
        
        limit = limits.get(call_type, 50)
        if self.call_count[call_type] >= limit:
            print(f"⚠️ Rate limit reached for {call_type}: {limit}/min")
            return False
        
        self.call_count[call_type] += 1
        return True
    
    def _is_cache_valid(self, key: str, data_type: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache_timestamps:
            return False
        
        age = time.time() - self.cache_timestamps[key]
        ttl = self.TTL.get(data_type, 10)
        return age < ttl
    
    def _get_cached(self, key: str, data_type: str) -> Optional[any]:
        """Get data from cache if valid"""
        with self.lock:
            if self._is_cache_valid(key, data_type):
                return self.cache.get(key)
        return None
    
    def _set_cache(self, key: str, data: any, data_type: str):
        """Store data in cache"""
        with self.lock:
            self.cache[key] = data
            self.cache_timestamps[key] = time.time()
    
    # ============ PUBLIC METHODS ============
    
    def get_ltp_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get LTP for multiple symbols in ONE API call
        Much more efficient than calling individually
        """
        cache_key = f"ltp_batch_{','.join(sorted(symbols))}"
        cached_data = self._get_cached(cache_key, 'ltp')
        if cached_data:
            return cached_data
        
        if not self._check_rate_limit('ltp'):
            return {}
        
        try:
            # Use batch API if available
            ltp_data = self.tsl.get_ltp_data(names=symbols)
            
            # Cache results
            self._set_cache(cache_key, ltp_data, 'ltp')
            return ltp_data
            
        except Exception as e:
            print(f"❌ Batch LTP error: {e}")
            return {}
    
    def get_all_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """
        Get complete market data for all watchlist symbols
        Single API call with 10-30 second cache
        """
        cache_key = f"market_data_{','.join(sorted(symbols))}"
        cached_data = self._get_cached(cache_key, 'quote')
        if cached_data:
            return cached_data
        
        if not self._check_rate_limit('quote'):
            return {}
        
        result = {}
        
        try:
            # Get batch LTP first
            ltp_batch = self.get_ltp_batch(symbols)
            
            # Try to get quote data for better info
            try:
                quote_data = self.tsl.get_quote_data(symbols)
            except:
                quote_data = {}
            
            for symbol in symbols:
                ltp = ltp_batch.get(symbol, 0)
                quote = quote_data.get(symbol, {})
                
                result[symbol] = MarketData(
                    symbol=symbol,
                    ltp=ltp,
                    open=quote.get('open', 0),
                    high=quote.get('high', 0),
                    low=quote.get('low', 0),
                    prev_close=quote.get('prev_close', ltp),
                    change=ltp - quote.get('prev_close', ltp),
                    change_percent=((ltp - quote.get('prev_close', ltp)) / (quote.get('prev_close', ltp) or 1)) * 100,
                    volume=quote.get('volume', 0),
                    timestamp=datetime.datetime.now().isoformat(),
                    bid_price=quote.get('bid_price', 0),
                    ask_price=quote.get('ask_price', 0),
                    bid_qty=quote.get('bid_qty', 0),
                    ask_qty=quote.get('ask_qty', 0)
                )
            
            self._set_cache(cache_key, result, 'quote')
            return result
            
        except Exception as e:
            print(f"❌ Market data error: {e}")
            return {s: self._get_empty_market_data(s) for s in symbols}
    
    def get_index_data(self) -> Dict[str, MarketData]:
        """Get index data (NIFTY, BANKNIFTY, etc.)"""
        cache_key = "index_data"
        cached_data = self._get_cached(cache_key, 'index')
        if cached_data:
            return cached_data
        
        if not self._check_rate_limit('index'):
            return {}
        
        indices = {
            "NIFTY 50": {"security_id": "13", "exchange": "IDX_I"},
            "BANKNIFTY": {"security_id": "25", "exchange": "IDX_I"},
            "FINNIFTY": {"security_id": "27", "exchange": "IDX_I"},
            "SENSEX": {"security_id": "51", "exchange": "IDX_I"}
        }
        
        result = {}
        
        try:
            # Batch request for all indices
            token = getattr(self.tsl, 'token_id', None) or getattr(self.tsl, 'access_token', None)
            
            if token:
                import requests
                url = "https://api.dhan.co/v2/marketfeed/ohlc"
                payload = {}
                
                for name, info in indices.items():
                    exchange = info["exchange"]
                    if exchange not in payload:
                        payload[exchange] = []
                    payload[exchange].append(int(info["security_id"]))
                
                headers = {
                    "access-token": token,
                    "client-id": self.config.CLIENT_CODE
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for name, info in indices.items():
                        sec_data = data.get("data", {}).get(info["exchange"], {}).get(info["security_id"], {})
                        ltp = sec_data.get("last_price", 0)
                        prev_close = sec_data.get("ohlc", {}).get("close", ltp)
                        
                        result[name] = MarketData(
                            symbol=name,
                            ltp=ltp,
                            open=sec_data.get("ohlc", {}).get("open", 0),
                            high=sec_data.get("ohlc", {}).get("high", 0),
                            low=sec_data.get("ohlc", {}).get("low", 0),
                            prev_close=prev_close,
                            change=ltp - prev_close,
                            change_percent=((ltp - prev_close) / (prev_close or 1)) * 100,
                            volume=0,
                            timestamp=datetime.datetime.now().isoformat(),
                            bid_price=0,
                            ask_price=0,
                            bid_qty=0,
                            ask_qty=0
                        )
            else:
                # Fallback to sample data
                for name in indices:
                    result[name] = self._get_empty_market_data(name)
                    
        except Exception as e:
            print(f"❌ Index data error: {e}")
            for name in indices:
                result[name] = self._get_empty_market_data(name)
        
        self._set_cache(cache_key, result, 'index')
        return result
    
    def get_account_summary(self) -> Dict:
        """Get account balance and positions summary"""
        cache_key = "account_summary"
        cached_data = self._get_cached(cache_key, 'balance')
        if cached_data:
            return cached_data
        
        result = {
            'balance': 0,
            'available': 0,
            'open_positions': 0,
            'positions_value': 0,
            'total_pnl': 0,
            'margin_used': 0,
            'last_updated': datetime.datetime.now().isoformat()
        }
        
        try:
            balance = self.tsl.get_balance()
            result['balance'] = balance or self.config.BASE_CAPITAL
            result['available'] = balance or self.config.BASE_CAPITAL
            
            # Get positions
            try:
                positions = self.tsl.get_positions()
                if isinstance(positions, list):
                    result['open_positions'] = len(positions)
                    result['positions_value'] = sum(p.get('netValue', 0) for p in positions)
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ Balance fetch error: {e}")
            result['balance'] = self.config.BASE_CAPITAL
            result['available'] = self.config.BASE_CAPITAL
        
        self._set_cache(cache_key, result, 'balance')
        return result
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get recent trades from database"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT trade_id, symbol, entry_price, exit_price, quantity, pnl, 
                       strategy, status, entry_time, exit_time, position_type
                FROM trades 
                ORDER BY trade_id DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            trades = []
            for row in rows:
                trades.append({
                    'trade_id': row[0],
                    'symbol': row[1],
                    'entry_price': row[2],
                    'exit_price': row[3] or 0,
                    'quantity': row[4],
                    'pnl': row[5] or 0,
                    'strategy': row[6],
                    'status': row[7] or 'closed',
                    'entry_time': row[8],
                    'exit_time': row[9],
                    'position_type': row[10] or 'LONG'
                })
            
            return trades
            
        except Exception as e:
            print(f"❌ Trade history error: {e}")
            return []
    
    def get_portfolio_stats(self) -> Dict:
        """Calculate portfolio statistics"""
        trades = self.get_trade_history(limit=500)
        
        closed_trades = [t for t in trades if t['status'] == 'closed' and t['pnl'] != 0]
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'max_drawdown': 0
            }
        
        total_pnl = sum(t['pnl'] for t in closed_trades)
        winning = [t for t in closed_trades if t['pnl'] > 0]
        losing = [t for t in closed_trades if t['pnl'] < 0]
        
        gross_profit = sum(t['pnl'] for t in winning) if winning else 0
        gross_loss = abs(sum(t['pnl'] for t in losing)) if losing else 1
        
        # Calculate drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        for trade in closed_trades:
            cumulative += trade['pnl']
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / (peak or 1) * 100
            if dd > max_dd:
                max_dd = dd
        
        return {
            'total_trades': len(closed_trades),
            'total_pnl': total_pnl,
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(closed_trades) * 100) if closed_trades else 0,
            'profit_factor': gross_profit / gross_loss if gross_loss > 0 else 0,
            'avg_win': (gross_profit / len(winning)) if winning else 0,
            'avg_loss': (gross_loss / len(losing)) if losing else 0,
            'best_trade': max([t['pnl'] for t in closed_trades]) if closed_trades else 0,
            'worst_trade': min([t['pnl'] for t in closed_trades]) if closed_trades else 0,
            'max_drawdown': max_dd
        }
    
    def _get_empty_market_data(self, symbol: str) -> MarketData:
        """Create empty market data structure"""
        return MarketData(
            symbol=symbol,
            ltp=0,
            open=0,
            high=0,
            low=0,
            prev_close=0,
            change=0,
            change_percent=0,
            volume=0,
            timestamp=datetime.datetime.now().isoformat(),
            bid_price=0,
            ask_price=0,
            bid_qty=0,
            ask_qty=0
        )
    
    def get_all_dashboard_data(self, watchlist: List[str]) -> Dict:
        """
        Get ALL data needed for dashboard in ONE call
        This is the main method you should use
        """
        return {
            'market_data': {k: asdict(v) for k, v in self.get_all_market_data(watchlist).items()},
            'index_data': {k: asdict(v) for k, v in self.get_index_data().items()},
            'account_summary': self.get_account_summary(),
            'portfolio_stats': self.get_portfolio_stats(),
            'recent_trades': self.get_trade_history(limit=30),
            'timestamp': datetime.datetime.now().isoformat()
        }


# Singleton instance
_data_service_instance = None

def get_realtime_data_service(tsl, config):
    """Get singleton instance of RealtimeDataService"""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = RealtimeDataService(tsl, config)
    return _data_service_instance