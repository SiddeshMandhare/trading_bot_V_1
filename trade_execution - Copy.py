# trade_execution.py - Enhanced with F&O (Options & Futures) Support

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

##    def place_super_order(self, name: str, action: str, qty: int, entry_price: float, 
##                     atr_points: float, strategy_name: str, chart,
##                     stop_loss_price: float = None, target_price: float = None) -> Optional[Dict]:
##        """
##        Place Super Order using DIRECT DHAN API CALL
##        Supports: EQUITIES, OPTIONS (CE/PE), FUTURES (FUT), INDICES
##        """
##        try:
##            # Calculate entry price from chart if not provided
##            if entry_price == 0 or entry_price is None:
##                entry_price = chart['close'].iloc[-1]
##            
##            # Calculate stop loss and target based on action
##            if action == 'BUY':
##                stop_loss_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER), 2)
##                target_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
##                
##                risk = entry_price - stop_loss_price
##                reward = target_price - entry_price
##                actual_ratio = reward / risk if risk > 0 else 0
##                
##                print(f"\n📊 RISK/REWARD CALCULATION (LONG):")
##                print(f"   Entry: ₹{entry_price:.2f}")
##                print(f"   Stop Loss: ₹{stop_loss_price:.2f} (Risk: ₹{risk:.2f})")
##                print(f"   Target: ₹{target_price:.2f} (Reward: ₹{reward:.2f})")
##                print(f"   Risk/Reward Ratio: 1:{actual_ratio:.1f}")
##                
##            else:  # SELL
##                stop_loss_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER), 2)
##                target_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
##                
##                risk = stop_loss_price - entry_price
##                reward = entry_price - target_price
##                actual_ratio = reward / risk if risk > 0 else 0
##                
##                print(f"\n📊 RISK/REWARD CALCULATION (SHORT):")
##                print(f"   Entry: ₹{entry_price:.2f}")
##                print(f"   Stop Loss: ₹{stop_loss_price:.2f} (Risk: ₹{risk:.2f})")
##                print(f"   Target: ₹{target_price:.2f} (Reward: ₹{reward:.2f})")
##                print(f"   Risk/Reward Ratio: 1:{actual_ratio:.1f}")
##            
##            # ============ DETERMINE INSTRUMENT TYPE & EXCHANGE SEGMENT ============
##            token = None
##            if hasattr(self.tsl, 'token_id'):
##                token = self.tsl.token_id
##            elif hasattr(self.tsl, 'access_token'):
##                token = self.tsl.access_token
##            elif hasattr(self.tsl, 'Dhan') and hasattr(self.tsl.Dhan, 'token'):
##                token = self.tsl.Dhan.token
##            
##            if not token:
##                print("❌ No access token available")
##                return None
##            
##            # Get security ID
##            security_id = self._get_security_id(name)
##            if not security_id:
##                print(f"❌ Could not get security ID for {name}")
##                # Try to get from instrument_df
##                if hasattr(self.tsl, 'instrument_df') and self.tsl.instrument_df is not None:
##                    df = self.tsl.instrument_df
##                    result = df[df['SEM_CUSTOM_SYMBOL'] == name]
##                    if result.empty:
##                        result = df[df['SEM_TRADING_SYMBOL'] == name]
##                    if not result.empty:
##                        security_id = str(result.iloc[-1]['SEM_SMST_SECURITY_ID'])
##                        print(f"🔑 Found security ID: {security_id}")
##            
##            if not security_id:
##                print(f"❌ Security ID not found for {name}")
##                return None
##            
##            # ============ INSTRUMENT TYPE DETECTION ============
##            instrument_type = "EQUITY"  # Default
##            exchange_segment = "NSE_EQ"
##            product_type = "INTRADAY"
##            order_type = "MARKET"
##            price_value = 0
##            
##            # Check for OPTIONS (CE/PE)
##            if 'CE' in name or 'PE' in name or 'PUT' in name or 'CALL' in name:
##                instrument_type = "OPTION"
##                exchange_segment = "NSE_FNO"
##                product_type = "MARGIN"  # Options need MARGIN product type
##                order_type = "LIMIT"      # Options work better with LIMIT
##                price_value = entry_price
##                print(f"   🎯 OPTION Detected: {name}")
##                print(f"   Exchange Segment: {exchange_segment}")
##                print(f"   Product Type: {product_type}")
##                
##                # Validate lot size for options
##                lot_size = self._get_option_lot_size(name)
##                if qty % lot_size != 0:
##                    print(f"   ⚠️ Warning: Quantity {qty} is not a multiple of lot size {lot_size}")
##            
##            # Check for FUTURES
##            elif 'FUT' in name or 'FUTURE' in name:
##                instrument_type = "FUTURE"
##                exchange_segment = "NSE_FNO"
##                product_type = "MARGIN"
##                order_type = "MARKET"
##                price_value = 0
##                print(f"   🎯 FUTURE Detected: {name}")
##            
##            # Check for INDICES
##            elif name in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']:
##                instrument_type = "INDEX"
##                exchange_segment = "IDX_I"
##                product_type = "INTRADAY"
##                order_type = "MARKET"
##                price_value = 0
##                print(f"   🎯 INDEX Detected: {name}")
##            
##            # Check for COMMODITIES
##            elif name in ['GOLD', 'SILVER', 'CRUDEOIL']:
##                instrument_type = "COMMODITY"
##                exchange_segment = "MCX_COMM"
##                product_type = "MARGIN"
##                order_type = "MARKET"
##                price_value = 0
##                print(f"   🎯 COMMODITY Detected: {name}")
##            
##            # Default: EQUITY
##            else:
##                instrument_type = "EQUITY"
##                exchange_segment = "NSE_EQ"
##                product_type = "INTRADAY"
##                order_type = "MARKET"
##                price_value = 0
##                print(f"   🎯 EQUITY Detected: {name}")
##            
##            # ============ BUILD PAYLOAD ============
##            payload = {
##                "dhanClientId": Config.CLIENT_CODE,
##                "transactionType": action,
##                "exchangeSegment": exchange_segment,
##                "productType": product_type,
##                "orderType": order_type,
##                "securityId": security_id,
##                "quantity": qty,
##                "price": price_value,
##                "triggerPrice": 0,
##                "targetPrice": target_price,
##                "stopLossPrice": stop_loss_price,
##                "trailingJump": Config.TRAILING_JUMP,
##                "correlationId": f"SO_{int(time.time())}"
##            }
##            
##            headers = {
##                "access-token": token,
##                "Content-Type": "application/json",
##                "client-id": Config.CLIENT_CODE
##            }
##            
##            url = "https://api.dhan.co/v2/super/orders"
##            
##            print(f"\n🚀 DIRECT API SUPER ORDER")
##            print(f"   Symbol: {name}")
##            print(f"   Instrument: {instrument_type}")
##            print(f"   Action: {action}")
##            print(f"   Quantity: {qty}")
##            print(f"   Exchange Segment: {exchange_segment}")
##            print(f"   Product Type: {product_type}")
##            print(f"   Order Type: {order_type}")
##            print(f"   Target: ₹{target_price}")
##            print(f"   Stop Loss: ₹{stop_loss_price}")
##            print(f"   Security ID: {security_id}")
##            
##            response = requests.post(url, headers=headers, json=payload, timeout=30)
##            
##            print(f"\n📥 Response Status: {response.status_code}")
##            
##            if response.status_code == 200:
##                result = response.json()
##                order_id = result.get("orderId")
##                
##                if order_id:
##                    print(f"✅ SUPER ORDER PLACED! Order ID: {order_id}")
##                    print(f"   Status: {result.get('orderStatus', 'PENDING')}")
##                    
##                    current_time = datetime.datetime.now(self.ist)
##                    
##                    return {
##                        'name': name, 'options_name': name, 'option_type': 'STOCK',
##                        'date': str(current_time.date()), 'entry_time': current_time.strftime('%H:%M:%S'),
##                        'max_holding_time': current_time + datetime.timedelta(hours=Config.MAX_HOLDING_HOURS),
##                        'super_order_id': order_id, 'entry_price': entry_price, 'qty': qty,
##                        'sl': stop_loss_price, 'target': target_price, 'strategy': strategy_name,
##                        'atr': atr_points, 'trade_type': instrument_type, 'buy_sell': action,
##                        'position_type': "LONG" if action == 'BUY' else "SHORT",
##                        'traded': "yes", 'order_type': 'SUPER_OPTIMIZED',
##                        'risk_reward_ratio': actual_ratio,
##                        'exchange_segment': exchange_segment,
##                        'product_type': product_type,
##                        'instrument_type': instrument_type
##                    }
##                else:
##                    print(f"❌ No order ID in response: {result}")
##                    return None
##            else:
##                print(f"❌ API Error {response.status_code}: {response.text}")
##                return None
##                
##        except Exception as e:
##            print(f"❌ Super Order error: {e}")
##            import traceback
##            traceback.print_exc()
##            return None



    def place_super_order(self, name: str, action: str, qty: int, entry_price: float, 
                     atr_points: float, strategy_name: str, chart,
                     stop_loss_price: float = None, target_price: float = None) -> Optional[Dict]:
        """
        Place Super Order using DIRECT DHAN API CALL
        Supports: EQUITIES, OPTIONS (CE/PE), FUTURES (FUT), INDICES
        """
        try:
            # Calculate entry price from chart if not provided
            if entry_price == 0 or entry_price is None:
                if chart is not None and hasattr(chart, 'iloc'):
                    entry_price = chart['close'].iloc[-1]
                else:
                    print("❌ No entry price provided and chart is None")
                    return None
            
            # ============ FIX: Only calculate if parameters NOT provided ============
            if stop_loss_price is None:
                if action == 'BUY':
                    stop_loss_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER), 2)
                else:  # SELL
                    stop_loss_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER), 2)
            
            if target_price is None:
                if action == 'BUY':
                    target_price = round(entry_price + (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
                else:  # SELL
                    target_price = round(entry_price - (atr_points * Config.ATR_MULTIPLIER * Config.RISK_REWARD_RATIO), 2)
            
            # ============ VALIDATE stop_loss and target ============
            # For LONG positions (BUY), stop loss must be LESS than entry price
            if action == 'BUY':
                if stop_loss_price >= entry_price:
                    print(f"⚠️ Invalid stop loss: {stop_loss_price} (must be < entry {entry_price})")
                    # Set a default 20% stop loss below entry
                    stop_loss_price = round(entry_price * 0.8, 2)
                    print(f"   Using fallback stop loss: {stop_loss_price}")
                
                if target_price <= entry_price:
                    print(f"⚠️ Invalid target: {target_price} (must be > entry {entry_price})")
                    target_price = round(entry_price * 2.5, 2)
                    print(f"   Using fallback target: {target_price}")
            
            # For SHORT positions (SELL), stop loss must be GREATER than entry price
            else:  # SELL
                if stop_loss_price <= entry_price:
                    print(f"⚠️ Invalid stop loss: {stop_loss_price} (must be > entry {entry_price})")
                    stop_loss_price = round(entry_price * 1.2, 2)
                    print(f"   Using fallback stop loss: {stop_loss_price}")
                
                if target_price >= entry_price:
                    print(f"⚠️ Invalid target: {target_price} (must be < entry {entry_price})")
                    target_price = round(entry_price * 0.5, 2)
                    print(f"   Using fallback target: {target_price}")
            
            # Ensure stop loss is positive
            if stop_loss_price <= 0:
                print(f"⚠️ Stop loss is zero or negative: {stop_loss_price}")
                stop_loss_price = round(entry_price * 0.8, 2) if action == 'BUY' else round(entry_price * 1.2, 2)
                print(f"   Using fallback: {stop_loss_price}")
            
            # Calculate risk/reward for logging
            risk = abs(entry_price - stop_loss_price)
            reward = abs(target_price - entry_price)
            actual_ratio = reward / risk if risk > 0 else 0
            
            print(f"\n📊 RISK/REWARD CALCULATION:")
            print(f"   Entry: ₹{entry_price:.2f}")
            print(f"   Stop Loss: ₹{stop_loss_price:.2f} (Risk: ₹{risk:.2f})")
            print(f"   Target: ₹{target_price:.2f} (Reward: ₹{reward:.2f})")
            print(f"   Risk/Reward Ratio: 1:{actual_ratio:.1f}")
            # =========================================================================
            
            # ============ DETERMINE INSTRUMENT TYPE & EXCHANGE SEGMENT ============
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
            
            # ============ INSTRUMENT TYPE DETECTION ============
            instrument_type = "EQUITY"  # Default
            exchange_segment = "NSE_EQ"
            product_type = "INTRADAY"
            order_type = "MARKET"
            price_value = 0
            
            # Check for OPTIONS (CE/PE)
            if 'CE' in name or 'PE' in name or 'PUT' in name or 'CALL' in name:
                instrument_type = "OPTION"
                exchange_segment = "NSE_FNO"
                product_type = "MARGIN"  # Options need MARGIN product type
                order_type = "LIMIT"      # Options work better with LIMIT
                price_value = entry_price
                print(f"   🎯 OPTION Detected: {name}")
                print(f"   Exchange Segment: {exchange_segment}")
                print(f"   Product Type: {product_type}")
                
                # Validate lot size for options
                lot_size = self._get_option_lot_size(name)
                if qty % lot_size != 0:
                    print(f"   ⚠️ Warning: Quantity {qty} is not a multiple of lot size {lot_size}")
            
            # Check for FUTURES
            elif 'FUT' in name or 'FUTURE' in name:
                instrument_type = "FUTURE"
                exchange_segment = "NSE_FNO"
                product_type = "MARGIN"
                order_type = "MARKET"
                price_value = 0
                print(f"   🎯 FUTURE Detected: {name}")
            
            # Check for INDICES
            elif name in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']:
                instrument_type = "INDEX"
                exchange_segment = "IDX_I"
                product_type = "INTRADAY"
                order_type = "MARKET"
                price_value = 0
                print(f"   🎯 INDEX Detected: {name}")
            
            # Check for COMMODITIES
            elif name in ['GOLD', 'SILVER', 'CRUDEOIL']:
                instrument_type = "COMMODITY"
                exchange_segment = "MCX_COMM"
                product_type = "MARGIN"
                order_type = "MARKET"
                price_value = 0
                print(f"   🎯 COMMODITY Detected: {name}")
            
            # Default: EQUITY
            else:
                instrument_type = "EQUITY"
                exchange_segment = "NSE_EQ"
                product_type = "INTRADAY"
                order_type = "MARKET"
                price_value = 0
                print(f"   🎯 EQUITY Detected: {name}")
            
            # ============ BUILD PAYLOAD ============
            payload = {
                "dhanClientId": Config.CLIENT_CODE,
                "transactionType": action,
                "exchangeSegment": exchange_segment,
                "productType": product_type,
                "orderType": order_type,
                "securityId": security_id,
                "quantity": qty,
                "price": price_value,
                "triggerPrice": 0,
                "targetPrice": target_price,
                "stopLossPrice": stop_loss_price,
                "trailingJump": Config.TRAILING_JUMP,
                "correlationId": f"SO_{int(time.time())}"
            }
            
            headers = {
                "access-token": token,
                "Content-Type": "application/json",
                "client-id": Config.CLIENT_CODE
            }
            
            url = "https://api.dhan.co/v2/super/orders"
            
            print(f"\n🚀 DIRECT API SUPER ORDER")
            print(f"   Symbol: {name}")
            print(f"   Instrument: {instrument_type}")
            print(f"   Action: {action}")
            print(f"   Quantity: {qty}")
            print(f"   Exchange Segment: {exchange_segment}")
            print(f"   Product Type: {product_type}")
            print(f"   Order Type: {order_type}")
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
                        'atr': atr_points, 'trade_type': instrument_type, 'buy_sell': action,
                        'position_type': "LONG" if action == 'BUY' else "SHORT",
                        'traded': "yes", 'order_type': 'SUPER_OPTIMIZED',
                        'risk_reward_ratio': actual_ratio,
                        'exchange_segment': exchange_segment,
                        'product_type': product_type,
                        'instrument_type': instrument_type
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
        """Get security ID for symbol - supports equities, indices, and options"""
        try:
            # Index security IDs
            INDEX_IDS = {
                "NIFTY": "13",
                "BANKNIFTY": "25", 
                "FINNIFTY": "27",
                "SENSEX": "51",
            }
            
            # ============ FOR OPTIONS: Get from instrument_df ============
            # Check if it's an option (contains PUT/CALL or CE/PE)
            if 'PUT' in symbol or 'CALL' in symbol or 'CE' in symbol or 'PE' in symbol:
                if hasattr(self.tsl, 'instrument_df') and self.tsl.instrument_df is not None:
                    df = self.tsl.instrument_df
                    # Exact match first
                    result = df[df['SEM_CUSTOM_SYMBOL'] == symbol]
                    if result.empty:
                        # Try partial match
                        result = df[df['SEM_CUSTOM_SYMBOL'].str.contains(symbol, na=False)]
                    if not result.empty and 'SEM_SMST_SECURITY_ID' in result.columns:
                        sec_id = str(result.iloc[-1]['SEM_SMST_SECURITY_ID'])
                        print(f"🔑 OPTION: Found security ID for {symbol}: {sec_id}")
                        return sec_id
            
            # Direct index match
            for name, sec_id in INDEX_IDS.items():
                if symbol.upper() == name.upper():
                    print(f"🔑 Index ID for {symbol}: {sec_id}")
                    return sec_id
            
            # For equities, try from instrument_df
            if hasattr(self.tsl, 'instrument_df') and self.tsl.instrument_df is not None:
                df = self.tsl.instrument_df
                result = df[df['SEM_CUSTOM_SYMBOL'] == symbol]
                if result.empty:
                    result = df[df['SEM_TRADING_SYMBOL'] == symbol]
                if not result.empty and 'SEM_SMST_SECURITY_ID' in result.columns:
                    sec_id = str(result.iloc[-1]['SEM_SMST_SECURITY_ID'])
                    print(f"🔑 Equity security ID: {sec_id}")
                    return sec_id
            
            print(f"⚠️ Could not find security ID for {symbol}")
            return None
            
        except Exception as e:
            print(f"Error getting security ID: {e}")
            return None

    def _get_option_lot_size(self, option_symbol: str) -> int:
        """Get lot size for option symbol"""
        try:
            # Standard lot sizes for indices
            if 'NIFTY' in option_symbol:
                return 65
            elif 'BANKNIFTY' in option_symbol:
                return 30
            elif 'FINNIFTY' in option_symbol:
                return 60
            elif 'SENSEX' in option_symbol:
                return 20
            else:
                # For stock options, try to get from instrument file
                if hasattr(self.tsl, 'get_lot_size'):
                    return self.tsl.get_lot_size(option_symbol) or 1
                return 1
        except:
            return 1

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
