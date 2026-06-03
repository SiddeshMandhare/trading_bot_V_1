# trade_execution.py - Replace place_super_order with this

import time
import datetime
import requests
import json
from typing import Dict, Optional
from config import Config
from risk_management import DynamicExitCalculator


class TradeExecution:
    def __init__(self, tsl, multi_account_manager=None):
        self.tsl = tsl
        self.multi_account_manager = multi_account_manager
        self.orderbook = {}
        self.completed_orders = []
        self.ist = Config.IST
        self.current_balance = Config.BASE_CAPITAL

    def get_balance(self):
        try:
            return self.tsl.get_balance()
        except Exception as e:
            print(f"Balance fetch error (non-critical): {e}")
            return Config.BASE_CAPITAL

    def get_available_capital(self):
        try:
            balance = self.tsl.get_balance()
            if balance and balance > 0:
                return balance
        except:
            pass
        return Config.BASE_CAPITAL

    def calculate_position_size(self, atr_points: float, current_price: float, strategy_name: str = None) -> int:
        current_capital = self.get_available_capital()
        
        if current_capital <= Config.Minimum_trading_capital:
            return 0
        
        risk_amount = current_capital * Config.BASE_CAPITAL_RISK_PERCENT
        
        if atr_points <= 0:
            atr_points = current_price * 0.01
        
        position_size = int(risk_amount / atr_points)
        
        return max(1, position_size)

    def place_super_order(self, name: str, action: str, qty: int, entry_price: float, 
                         atr_points: float, strategy_name: str, chart) -> Optional[Dict]:
        """
        Place Super Order using DIRECT DHAN API CALL (bypasses library bugs)
        """
        try:
            # Calculate entry price from chart if not provided
            if entry_price == 0 or entry_price is None:
                entry_price = chart['close'].iloc[-1]
            
            # Calculate stop loss and target based on action
            if action == 'BUY':
                stop_loss_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER), 2)
                target_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
                
                risk = entry_price - stop_loss_price
                reward = target_price - entry_price
                actual_ratio = reward / risk if risk > 0 else 0
                
                print(f"\n📊 RISK/REWARD CALCULATION (LONG):")
                print(f"   Entry: ₹{entry_price:.2f}")
                print(f"   Stop Loss: ₹{stop_loss_price:.2f} (Risk: ₹{risk:.2f})")
                print(f"   Target: ₹{target_price:.2f} (Reward: ₹{reward:.2f})")
                print(f"   Risk/Reward Ratio: 1:{actual_ratio:.1f}")
                
            else:  # SELL
                stop_loss_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER), 2)
                target_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
                
                risk = stop_loss_price - entry_price
                reward = entry_price - target_price
                actual_ratio = reward / risk if risk > 0 else 0
                
                print(f"\n📊 RISK/REWARD CALCULATION (SHORT):")
                print(f"   Entry: ₹{entry_price:.2f}")
                print(f"   Stop Loss: ₹{stop_loss_price:.2f} (Risk: ₹{risk:.2f})")
                print(f"   Target: ₹{target_price:.2f} (Reward: ₹{reward:.2f})")
                print(f"   Risk/Reward Ratio: 1:{actual_ratio:.1f}")
            
            # ============ DIRECT API CALL ============
            # Get token from tsl
            token = None
            if hasattr(self.tsl, 'token_id'):
                token = self.tsl.token_id
            elif hasattr(self.tsl, 'access_token'):
                token = self.tsl.access_token
            elif hasattr(self.tsl, 'Dhan') and hasattr(self.tsl.Dhan, 'token'):
                token = self.tsl.Dhan.token
            
            if not token:
                print("❌ No access token available")
                return None
            
            # Get security ID
            security_id = self._get_security_id(name)
            if not security_id:
                print(f"❌ Could not get security ID for {name}")
                return None
            
                # Try to get from instrument_df
                if hasattr(self.tsl, 'instrument_df') and self.tsl.instrument_df is not None:
                    df = self.tsl.instrument_df
                    result = df[df['SEM_CUSTOM_SYMBOL'] == name]
                    if result.empty:
                        result = df[df['SEM_TRADING_SYMBOL'] == name]
                    if not result.empty:
                        security_id = str(result.iloc[-1]['SEM_SMST_SECURITY_ID'])
                        print(f"🔑 Found security ID: {security_id}")
            
            if not security_id:
                print(f"❌ Security ID not found for {name}")
                return None
            
            # Build payload for Dhan API v2
            payload = {
                "dhanClientId": Config.CLIENT_CODE,
                "transactionType": action,
                "exchangeSegment": "NSE_EQ",  # For equities
                "productType": "INTRADAY",
                "orderType": "MARKET",
                "securityId": security_id,
                "quantity": qty,
                "price": 0,
                "triggerPrice": 0,
                "targetPrice": target_price,
                "stopLossPrice": stop_loss_price,
                "trailingJump": Config.TRAILING_JUMP,
                "correlationId": f"SO_{int(time.time())}"
            }
            
            # For options
            if 'CE' in name or 'PE' in name:
                payload["exchangeSegment"] = "NSE_FNO"
            
            # For indices
            if name in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']:
                payload["exchangeSegment"] = "IDX_I"
            
            headers = {
                "access-token": token,
                "Content-Type": "application/json",
                "client-id": Config.CLIENT_CODE
            }
            
            url = "https://api.dhan.co/v2/super/orders"
            
            print(f"\n🚀 DIRECT API SUPER ORDER")
            print(f"   URL: {url}")
            print(f"   Symbol: {name}")
            print(f"   Action: {action}")
            print(f"   Quantity: {qty}")
            print(f"   Target: ₹{target_price}")
            print(f"   Stop Loss: ₹{stop_loss_price}")
            print(f"   Security ID: {security_id}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get("orderId")
                
                if order_id:
                    print(f"✅ SUPER ORDER PLACED! Order ID: {order_id}")
                    print(f"   Status: {result.get('orderStatus', 'PENDING')}")
                    
                    current_time = datetime.datetime.now(self.ist)
                    
                    return {
                        'name': name, 'options_name': name, 'option_type': 'STOCK',
                        'date': str(current_time.date()), 'entry_time': current_time.strftime('%H:%M:%S'),
                        'max_holding_time': current_time + datetime.timedelta(hours=Config.MAX_HOLDING_HOURS),
                        'super_order_id': order_id, 'entry_price': entry_price, 'qty': qty,
                        'sl': stop_loss_price, 'target': target_price, 'strategy': strategy_name,
                        'atr': atr_points, 'trade_type': 'EQUITY', 'buy_sell': action,
                        'position_type': "LONG" if action == 'BUY' else "SHORT",
                        'traded': "yes", 'order_type': 'SUPER_OPTIMIZED',
                        'risk_reward_ratio': actual_ratio
                    }
                else:
                    print(f"❌ No order ID in response: {result}")
                    return None
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Super Order error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_security_id(self, symbol: str) -> str:
        """Get security ID for symbol from various sources"""
        try:
            # Try from tsl's instrument_df
            if hasattr(self.tsl, 'instrument_df') and self.tsl.instrument_df is not None:
                df = self.tsl.instrument_df
                result = df[df['SEM_CUSTOM_SYMBOL'] == symbol]
                if result.empty:
                    result = df[df['SEM_TRADING_SYMBOL'] == symbol]
                if not result.empty and 'SEM_SMST_SECURITY_ID' in result.columns:
                    return str(result.iloc[-1]['SEM_SMST_SECURITY_ID'])
            
            # Try from token_dict
            if hasattr(self.tsl, 'token_dict') and symbol in self.tsl.token_dict:
                return str(self.tsl.token_dict[symbol]['token'])
            
            # Try common indices
            index_ids = {
                "NIFTY": "13",
                "BANKNIFTY": "25", 
                "FINNIFTY": "27",
                "SENSEX": "51"
            }
            if symbol in index_ids:
                return index_ids[symbol]
                
        except Exception as e:
            print(f"Error getting security ID: {e}")
        
        return None

    def place_traditional_order(self, name: str, action: str, qty: int, atr_points: float) -> Optional[Dict]:
        """Place traditional order (fallback)"""
        try:
            entry_orderid = self.tsl.order_placement(
                tradingsymbol=name, exchange='NSE', quantity=qty, price=0,
                trigger_price=0, order_type='MARKET', transaction_type=action, trade_type='MIS'
            )
            
            if not entry_orderid:
                return None
            
            time.sleep(2)
            executed_price = self.tsl.get_executed_price(entry_orderid)
            ltp_data = self.tsl.get_ltp_data(names=[name])
            entry_price = executed_price if executed_price else ltp_data.get(name, 0)
            
            if action == 'BUY':
                stop_loss_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER), 2)
                target_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
            else:
                stop_loss_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER), 2)
                target_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
            
            current_time = datetime.datetime.now(self.ist)
            
            # Place SL order
            sl_transaction = 'SELL' if action == 'BUY' else 'BUY'
            self.tsl.order_placement(
                tradingsymbol=name, exchange='NSE', quantity=qty,
                price=stop_loss_price, trigger_price=stop_loss_price,
                order_type='STOPLOSS', transaction_type=sl_transaction, trade_type='MIS'
            )
            
            return {
                'name': name, 'options_name': name, 'option_type': 'STOCK',
                'date': str(current_time.date()), 'entry_time': current_time.strftime('%H:%M:%S'),
                'max_holding_time': current_time + datetime.timedelta(hours=Config.MAX_HOLDING_HOURS),
                'entry_orderid': entry_orderid, 'entry_price': entry_price, 'qty': qty,
                'sl': stop_loss_price, 'target': target_price, 'strategy': 'MULTI',
                'atr': atr_points, 'trade_type': 'EQUITY', 'buy_sell': action,
                'position_type': "LONG" if action == 'BUY' else "SHORT",
                'traded': "yes", 'order_type': 'TRADITIONAL'
            }
        except Exception as e:
            print(f"Traditional order error: {e}")
            return None
