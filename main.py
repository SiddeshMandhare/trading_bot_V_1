# main.py
import os
import gc
import sys
import time
import sqlite3
import logging
import datetime
import winsound
from datetime import timedelta
from daily_risk_manager import get_daily_risk_manager
import pandas as pd
from typing import Dict, Any
from option_strategies import OptionSignalProcessor, OptionTradeManager
from config import Config
from config import Config
from auth_service import create_tradehull_with_totp
from telegram_service import TelegramService
from data_service import DataService
from trade_execution import TradeExecution
from risk_management import SignalStrength, MarketRegime, SignalCooldown, AdaptiveTrailingStop
from position_sizing import KellyPositionSizer
from trade_journal import TradeJournal
from health_check import HealthChecker
from utils.logger import get_logger

from strategies import (
    # Existing
    EMA_RSI_Strategy,
    MACD_Bollinger_Strategy,
    RSI_50_Crossover,
    VWAP_Strategy,
    MovingAverageCrossover,
    OpeningRangeBreakout,
    # New - Trend Following
    SupertrendStrategy,
    TripleEMA_ADX_Strategy,
    IchimokuStrategy,
    # New - Momentum
    StochasticRSI_Strategy,
    # New - Price Action
    PriceActionStrategy,
    # New - SMC (Smart Money Concepts)
    SMC_FairValueGap,
    SMC_LiquiditySweep,
    SMC_OrderBlock_BOS,
)

# Create logs directory if not exists
os.makedirs('logs', exist_ok=True)

# Initialize logger
log = get_logger("TradingBot", "logs/trading.log")


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import logging
logging.basicConfig(level=logging.DEBUG)



class OptionTradingBot:
    def __init__(self):
        log.info("Initializing OptionTradingBot with TOTP authentication...")
        self.test_tables()
        
##        if os.path.exists('trading_bot.db'):
##            os.remove('trading_bot.db')
        
        # Authenticate with Dhan
        self.tsl = create_tradehull_with_totp(Config.CLIENT_CODE, Config.PIN, Config.TOTP_SECRET)
        if not self.tsl:
            raise Exception("Primary account authentication failed")
        
        # Initialize services
        self.data_service = DataService(self.tsl)


        from paper_trading import PaperTradingManager
        self.execution = TradeExecution(self.tsl)
        if self.paper_trading_enabled:
            self.execution.paper_trading = PaperTradingManager()
        

        # Add this:
        from daily_risk_manager import get_daily_risk_manager
        self.risk_manager = get_daily_risk_manager()
        self.execution.set_risk_manager(self.risk_manager)

    
        # ============ SETUP DYNAMIC WATCHLISTS ============
        # Store both watchlists from config
        self.equity_watchlist = Config.EQUITY_WATCHLIST
        self.fno_watchlist = Config.FNO_WATCHLIST
        
        # Set active watchlist based on current trading mode
        self.update_active_watchlist()
        
        log.info(f"📋 TRADING MODE: {Config.TRADING_MODE}")
        print(f"   Active Watchlist: {self.watchlist}")
        print(f"   Equity Watchlist: {self.equity_watchlist}")
        print(f"   F&O Watchlist: {self.fno_watchlist}")
        # ==================================================
        
        # Initialize components
        self.signal_cooldown = SignalCooldown()
        self.trailing_manager = AdaptiveTrailingStop() if Config.ENABLE_ADAPTIVE_TRAILING else None
        self.kelly_sizer = KellyPositionSizer() if Config.USE_Kelly_SIZING else None
        self.completed_orders = []
        self.orderbook = {}

        # Initialize Trade Journal
        self.trade_journal = TradeJournal()
        log.success("Trade Journal initialized")
        
        # Initialize Health Checker
        self.health_checker = HealthChecker(self)
        log.success("Health Checker initialized")


        # Start health monitoring in background
        self.health_checker.start_monitoring(interval_seconds=60)
        
        
        # Database
        self.conn = self._init_database()
        
        # Strategies
        self.strategies = self._init_strategies()
        
        # Capital
        self.current_balance = self._set_dynamic_capital()
        self.execution.current_balance = self.current_balance
        
        # Telegram
        self.telegram = TelegramService(Config.BOT_TOKEN, Config.RECEIVER_CHAT_ID, self)
        self.telegram.start_command_handler()
        
        log.success(f"Bot ready! Balance: ₹{self.current_balance:,.2f}")


        # Initialize option trading components
        self.option_active = getattr(Config, 'OPTION_TRADING_ENABLED', False)
        self.option_processor = None
        if getattr(Config, 'OPTION_TRADING_ENABLED', False):
            self.option_processor = OptionSignalProcessor(self.tsl, self.execution)
            log.success("Option trading module ready")
            print(f"   Trading: {getattr(Config, 'OPTION_SYMBOLS', [])}")
        
        if self.option_active:
            self.option_processor = OptionSignalProcessor(self.tsl, self.execution)
            log.success("Option trading module initialized")
            print(f"   Trading options on: {getattr(Config, 'OPTION_SYMBOLS', [])}")
            print(f"   OTM Count: {getattr(Config, 'OPTION_OTM_COUNT', 1)}")
            print(f"   Max Lots: {getattr(Config, 'OPTION_MAX_LOTS_PER_TRADE', 5)}")
            print(f"   Risk per trade: {getattr(Config, 'OPTION_RISK_PER_TRADE_PERCENT', 0.01)*100}%")



        # Initialize trade execution
        self.trade_executor = TradeExecution(self.tsl, multi_account_manager=None)
        
        # Check if paper trading is enabled
        self.paper_trading_enabled = getattr(Config, 'PAPER_TRADING_ENABLED', False)
        
        if self.paper_trading_enabled:
            log.info(f"📝 PAPER TRADING MODE ENABLED - Starting balance: ₹{Config.PAPER_BALANCE:,.2f}")
        else:
            self.logger.info(f"💰 LIVE TRADING MODE - Balance: ₹{self.current_balance:,.2f}")



    def test_tables(self):
        """Test all table formats - remove this after testing"""
        try:
            # Only import if tabulate is available
            from tabulate import tabulate
            print("\n" + "="*60)
            print("  TABLE FORMAT TEST (TABULATE AVAILABLE)")
            print("="*60)
            
            # Test simple table
            test_data = [
                ["NIFTY", "PUT", 23450, 49.40, 123.50],
                ["BANKNIFTY", "CALL", 48500, 85.20, 212.80],
            ]
            headers = ["Symbol", "Type", "Strike", "Entry", "Target"]
            print(tabulate(test_data, headers=headers, tablefmt="grid"))
            print("\n✅ Table formatting is working!")
            
        except ImportError:
            print("\n⚠️ WARNING: 'tabulate' library not installed!")
            print("   Run: pip install tabulate")
            print("   Tables will not display properly until installed.")
        except Exception as e:
            print(f"\n❌ Error testing tables: {e}")


    # Add a method to check risk before trading
    def check_risk_before_trade(self, lot_size=1) -> tuple:
        """Check if trade is allowed by risk manager"""
        allowed, reason = self.risk_manager.before_trade(lot_size)
        if not allowed:
            log.risk(f"🚫 RISK BLOCK: {reason}")
            self.telegram.send_alert(f"🚫 RISK BLOCKED: {reason}")
        return allowed, reason

    def update_risk_after_trade(self, pnl: float, is_entry: bool = True, lot_size: int = 1):
        """Update risk manager after trade"""
        if is_entry:
            self.risk_manager.after_trade_entry(lot_size)
        else:
            self.risk_manager.update_pnl(pnl)
            self.risk_manager.after_trade_exit(lot_size)
            
            # Check if blocked after exit
            status = self.risk_manager.get_status()
            if status['is_blocked']:
                log.risk(f"🔴 TRADING BLOCKED: {status['block_reason']}")
                self.telegram.send_alert(f"🔴 TRADING BLOCKED FOR TODAY\n{status['block_reason']}")



    def track_trade_performance(self):
            """Track and display trade performance"""
            if hasattr(self, 'trade_history') and self.trade_history:
                log.performance_table(self.trade_history)
            else:
                log.info("No trades in history yet")

    # Add these methods to OptionTradingBot class

    def set_trading_mode(self, mode: str):
        """Change trading mode and update watchlist dynamically"""
        from config import Config
        from config import Config
        
        if mode.upper() in ['EQUITY_ONLY', 'FNO_ONLY', 'BOTH']:
            old_mode = Config.TRADING_MODE
            Config.TRADING_MODE = mode.upper()
            
            # Update option trading based on mode
            if mode.upper() == 'EQUITY_ONLY':
                option_config.OPTION_TRADING_ENABLED = False
                self.option_active = False
                print(f"📊 Mode: EQUITY_ONLY - Trading only equities")
            elif mode.upper() == 'FNO_ONLY':
                option_config.OPTION_TRADING_ENABLED = True
                self.option_active = True
                print(f"🎯 Mode: FNO_ONLY - Trading only F&O options")
            else:  # BOTH
                option_config.OPTION_TRADING_ENABLED = True
                self.option_active = True
                print(f"🔄 Mode: BOTH - Trading equities AND F&O options")
            
            # Update active watchlist
            self.update_active_watchlist()
            
            # Send Telegram alert if available
            if hasattr(self, 'telegram') and self.telegram:
                alert_msg = f"🔄 Trading Mode Changed: {old_mode} → {Config.TRADING_MODE}\n📋 Active Symbols: {', '.join(self.watchlist[:5])}{'...' if len(self.watchlist) > 5 else ''}"
                self.telegram.send_alert(alert_msg)
            
            print(f"✅ Trading mode changed to {Config.TRADING_MODE}")
            print(f"📋 New watchlist: {self.watchlist}")
            return True
        return False



    def update_active_watchlist(self):
        """Update active watchlist based on current trading mode"""
        from config import Config
        
        if Config.TRADING_MODE == "EQUITY_ONLY":
            self.watchlist = self.equity_watchlist.copy()
            print(f"📊 EQUITY MODE: Scanning {len(self.watchlist)} equity symbols")
        elif Config.TRADING_MODE == "FNO_ONLY":
            self.watchlist = self.fno_watchlist.copy()
            print(f"🎯 FNO MODE: Scanning {len(self.watchlist)} F&O symbols")
        else:  # BOTH mode
            # Combine both lists, remove duplicates
            self.watchlist = list(set(self.equity_watchlist + self.fno_watchlist))
            print(f"🔄 BOTH MODE: Scanning {len(self.watchlist)} symbols (Equity + F&O)")
        
        # Update Config.WATCHLIST for compatibility with other code
        Config.WATCHLIST = self.watchlist


    

    def get_trading_mode_status(self) -> Dict:
        """Get current trading mode status"""
        from config import Config
        from config import Config
        
        return {
            'mode': Config.TRADING_MODE,
            'equity_enabled': Config.TRADING_MODE != "FNO_ONLY",
            'fno_enabled': Config.TRADING_MODE != "EQUITY_ONLY" and option_config.OPTION_TRADING_ENABLED,
            'fno_symbols': option_config.OPTION_SYMBOLS,
            'watchlist': Config.WATCHLIST
        }

    def _init_strategies(self):
        strategies = []
        strategy_map = {
            # Existing
            'EMA_RSI': EMA_RSI_Strategy,
            'MACD_Bollinger': MACD_Bollinger_Strategy,
            'RSI_50_Crossover': RSI_50_Crossover,
            'VWAP_Reversion': VWAP_Strategy,
            'MA_Crossover_50_200': MovingAverageCrossover,
            'ORB_30min': OpeningRangeBreakout,
            # New - Trend Following
            'Supertrend_RSI': SupertrendStrategy,
            'TripleEMA_ADX': TripleEMA_ADX_Strategy,
            'Ichimoku_Cloud': IchimokuStrategy,
            # New - Momentum
            'StochasticRSI_MACD': StochasticRSI_Strategy,
            # New - Price Action
            'PriceAction_Engulfing_PinBar': PriceActionStrategy,
            # New - SMC
            'SMC_FairValueGap': SMC_FairValueGap,
            'SMC_LiquiditySweep': SMC_LiquiditySweep,
            'SMC_OrderBlock_BOS': SMC_OrderBlock_BOS,
        }

        for name in Config.ACTIVE_STRATEGIES:
            if name in strategy_map:
                strategies.append(strategy_map[name]())
                log.success(f"Loaded strategy: {name}")
            else:
                log.warning(f"Strategy '{name}' not found")
        return strategies
    

    def _init_database(self):
        conn = sqlite3.connect('trading_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, 
                entry_time DATETIME, 
                entry_price REAL,
                exit_time DATETIME,
                exit_price REAL,
                quantity INTEGER, 
                stop_loss REAL, 
                pnl REAL,
                strategy TEXT, 
                status TEXT,
                position_type TEXT,
                order_id TEXT
            )
        ''')
        
        # Add missing columns if they don't exist
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'exit_time' not in columns:
            cursor.execute("ALTER TABLE trades ADD COLUMN exit_time DATETIME")
        if 'exit_price' not in columns:
            cursor.execute("ALTER TABLE trades ADD COLUMN exit_price REAL DEFAULT 0")
        if 'position_type' not in columns:
            cursor.execute("ALTER TABLE trades ADD COLUMN position_type TEXT DEFAULT 'LONG'")
        if 'order_id' not in columns:
            cursor.execute("ALTER TABLE trades ADD COLUMN order_id TEXT")
        
        conn.commit()
        return conn


    
    
    def _set_dynamic_capital(self):
        try:
            balance = self.execution.get_balance()
            if balance and balance > 0:
                return balance
        except:
            pass
        return Config.BASE_CAPITAL
    
    def get_available_capital(self):
        return self.current_balance
    
    def update_balance_after_trade(self, trade_value: float, pnl: float = 0, operation: str = "deduct"):
        margin_amount = trade_value / Config.BROKER_MARGIN_MULTIPLIER
        if operation == "deduct":
            self.current_balance -= margin_amount
        else:
            self.current_balance += margin_amount + (pnl / Config.BROKER_MARGIN_MULTIPLIER)
        return True
    
    def save_trade(self, trade_data: Dict):
        """Save trade to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO trades (symbol, entry_time, entry_price, quantity, stop_loss, pnl, strategy, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('name', ''),
                f"{trade_data.get('date', '')} {trade_data.get('entry_time', '')}",
                trade_data.get('entry_price', 0),
                trade_data.get('qty', 0),
                trade_data.get('sl', 0),
                trade_data.get('pnl', 0),
                trade_data.get('strategy', ''),
                'closed' if trade_data.get('exit_time') else 'open'
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Failed to save trade: {e}")
    
    def send_trade_alert(self, trade_data: Dict, alert_type: str):
        """Send trade alert to Telegram with strategy info"""
        try:
            if alert_type == "ENTRY":
                # Get strategy name from trade_data
                strategy_name = trade_data.get('strategy', 'Unknown')
                
                message = f"""🚀 ENTRY: {trade_data.get('buy_sell', '')} {trade_data.get('qty', 0)} {trade_data.get('name', '')} @ ₹{trade_data.get('entry_price', 0):.2f}
    📊 Strategy: {strategy_name}
    🎯 Target: ₹{trade_data.get('target', 0):.2f}
    🛡️ SL: ₹{trade_data.get('sl', 0):.2f}
    📈 R:R: 1:{trade_data.get('risk_reward_ratio', 0):.1f}"""
                
            elif alert_type == "EXIT":
                pnl = trade_data.get('pnl', 0)
                emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➖"
                message = f"""🔴 EXIT: {trade_data.get('name', '')}
    {emoji} P&L: ₹{pnl:+,.2f}
    Reason: {trade_data.get('remark', 'N/A')}"""
            else:
                return
            
            self.telegram.send_alert(message)
        except Exception as e:
            print(f"Alert error: {e}")
    
    def generate_signals(self, chart: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        signals = {'buy_call': False, 'buy_put': False, 'strategies': []}
        
        for strategy in self.strategies:
            try:
                # ============ ADD DEBUG PRINT HERE ============
                log.data(f"{strategy.get_strategy_name()} - Chart length: {len(chart)}")
                # =============================================
                
                strategy.calculate_indicators(chart)
                strategy_signals = strategy.generate_signals(chart, symbol)
                
                # ADD THIS DEBUG
                if strategy_signals.get('buy_call') or strategy_signals.get('buy_put'):
                    log.signal(f"{strategy.get_strategy_name()} generated signal for {symbol}!")
                
                signals['strategies'].append({
                    'name': strategy.get_strategy_name(),
                    'signals': strategy_signals
                })
                
                weight = Config.STRATEGY_WEIGHTS.get(strategy.get_strategy_name(), 0)
                if weight > 0:
                    if strategy_signals.get('buy_call'):
                        signals['buy_call'] = True
                    if strategy_signals.get('buy_put'):
                        signals['buy_put'] = True
            except Exception as e:
                logger.error(f"Strategy {strategy.get_strategy_name()} failed: {e}")
        
        return signals
    

    def place_stock_order(self, name: str, signals: Dict, chart: pd.DataFrame):
        """Place a stock order with proper execution"""
        if name in self.orderbook:
            print(f"   ⚠️ Already have a position in {name}, skipping")
            return
        
        action = 'BUY' if signals.get('buy_call') else 'SELL'
        
        log.order(f"Attempting {action} order for {name}...")
        
        # Find triggering strategy
        triggering_strategy = None
        for s in signals.get('strategies', []):
            if (action == 'BUY' and s['signals'].get('buy_call')) or (action == 'SELL' and s['signals'].get('buy_put')):
                triggering_strategy = s
                break
        
        if not triggering_strategy:
            print(f"   ⚠️ No triggering strategy found for {action}")
            return
        
        strategy_name = triggering_strategy['name']
        current_price = chart['close'].iloc[-1]
        
        log.data(f"Current Price: ₹{current_price:.2f}")
        
        # Signal strength check
        scores = SignalStrength.calculate_signal_strength(chart, name, action)
        log.risk(f"Signal Strength: {scores['overall']}/100 (Required: {Config.MIN_SIGNAL_STRENGTH})")

        log.data(f"Grade: {SignalStrength.get_signal_grade(scores)}")
        log.info(f"Strategy: {strategy_name}")

        if not SignalStrength.should_trade(scores):
            print(f"   ❌ Signal too weak ({scores['overall']} < {Config.MIN_SIGNAL_STRENGTH})")
            return
        
        # Market regime filter
        if Config.USE_MARKET_REGIME_FILTER:
            regime = MarketRegime.detect_regime(chart)
            bias = MarketRegime.get_bias(regime)
            print(f"   📈 Market Regime: {regime}, Bias: {bias}")
            if (bias == 'LONG_ONLY' and action != 'BUY') or (bias == 'SHORT_ONLY' and action != 'SELL'):
                print(f"   ❌ Market regime filter blocked {action} signal in {bias} regime")
                return
        
        # Cooldown check
        current_time = Config.get_current_time()
        if not self.signal_cooldown.can_take_signal(name, current_price, current_time):
            print(f"   ⏸️ Signal cooldown active for {name}")
            return
        
        # Calculate ATR
        try:
            # Try to get ATR from chart if available
            if 'atr' in chart.columns:
                atr_points = chart['atr'].iloc[-1] * Config.ATR_MULTIPLIER
            else:
                # Calculate ATR manually
                high_low = chart['high'] - chart['low']
                high_close = abs(chart['high'] - chart['close'].shift())
                low_close = abs(chart['low'] - chart['close'].shift())
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = tr.rolling(window=14).mean()
                atr_points = atr.iloc[-1] * Config.ATR_MULTIPLIER if not pd.isna(atr.iloc[-1]) else current_price * 0.01
        except Exception as e:
            print(f"   ⚠️ ATR calculation error: {e}, using default")
            atr_points = current_price * 0.01
        
        print(f"   📊 ATR Points: {atr_points:.2f}")
        
        # Position size
        qty = self.execution.calculate_position_size(atr_points, current_price, strategy_name)
        if qty <= 0:
            print(f"   ❌ Position size calculation returned {qty}")
            return
        
        print(f"   📦 Quantity: {qty} shares")
        print(f"   💰 Trade Value: ₹{qty * current_price:.2f}")
        
        # Place order
        try:
            if Config.USE_SUPER_ORDERS:
                print(f"   🚀 Placing SUPER ORDER...")
                order = self.execution.place_super_order(
                    name, action, qty, current_price, atr_points, strategy_name, chart
                )
            else:
                print(f"   🚀 Placing TRADITIONAL ORDER...")
                order = self.execution.place_traditional_order(name, action, qty, atr_points)
            
            if order:
                trade_value = qty * current_price
                self.update_balance_after_trade(trade_value, operation="deduct")
                self.orderbook[name] = order
                self.signal_cooldown.record_signal(name, current_price, current_time)
                self.save_trade(order)
                self.send_trade_alert(order, "ENTRY")
                log.success(f"ORDER PLACED SUCCESSFULLY!")
                print(f"      Action: {action} {qty} {name}")
                print(f"      Entry: ₹{order.get('entry_price', current_price):.2f}")
                print(f"      Stop Loss: ₹{order.get('sl', 0):.2f}")
                print(f"      Target: ₹{order.get('target', 0):.2f}")
            else:
                log.error(f"Order placement failed...")
                
        except Exception as e:
            print(f"   ❌ Order placement error: {e}")
            import traceback
            traceback.print_exc()

        
        



    def monitor_open_positions(self, symbol: str):
        if symbol not in self.orderbook:
            return
        
        order = self.orderbook[symbol]
        current_price = self.data_service.get_current_price(symbol)
        
        if not current_price:
            return
        
        # Adaptive trailing stop
        if Config.ENABLE_ADAPTIVE_TRAILING and self.trailing_manager and order.get('order_type') == 'SUPER_OPTIMIZED':
            new_stop = self.trailing_manager.calculate_new_stop(
                symbol, order['position_type'], current_price, order['entry_price'], order.get('atr', 0)
            )
            if new_stop and new_stop != order.get('sl'):
                order['sl'] = new_stop
        
        # Check stop loss
        sl_hit = (order['position_type'] == 'LONG' and current_price <= order['sl']) or \
                 (order['position_type'] == 'SHORT' and current_price >= order['sl'])
        
        if sl_hit:
            self._close_position(symbol, current_price, "SL_HIT")
            return
        
        # Check holding time
        if 'max_holding_time' in order and Config.get_current_time() >= order['max_holding_time']:
            self._close_position(symbol, current_price, "HOLDING_TIME_EXCEEDED")
    
    def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Modified to add trade journal entry"""
        if symbol not in self.orderbook:
            return
        
        order = self.orderbook[symbol]
        pnl = ((exit_price - order['entry_price']) * order['qty']) if order['position_type'] == 'LONG' \
              else ((order['entry_price'] - exit_price) * order['qty'])
        
        trade_value = order['qty'] * order['entry_price']
        self.update_balance_after_trade(trade_value, pnl, operation="add")
        
        order.update({'exit_price': exit_price, 'pnl': pnl, 'remark': reason, 'exit_time': Config.get_current_time().strftime('%H:%M:%S')})
        
        # ============ ADD TRADE JOURNAL ENTRY ============
        try:
            # Prepare trade data for journal
            trade_data = {
                'trade_id': order.get('trade_id', len(self.completed_orders) + 1),
                'symbol': symbol,
                'entry_time': f"{order.get('date', '')} {order.get('entry_time', '')}",
                'entry_price': order['entry_price'],
                'quantity': order['qty'],
                'strategy': order.get('strategy', 'Unknown')
            }
            
            trade_result = {
                'exit_time': Config.get_current_time().strftime('%Y-%m-%d %H:%M:%S'),
                'exit_price': exit_price,
                'pnl': pnl,
                'exit_reason': reason,
                'emotional_state': self._get_emotional_state(pnl),  # Add this method
                'tags': [reason, order.get('position_type', '')]
            }
            
            # Add to journal
            journal_id = self.trade_journal.add_entry(trade_data, trade_result)
            print(f"📝 Trade journal entry added (ID: {journal_id})")
            
        except Exception as e:
            print(f"⚠️ Failed to add trade journal entry: {e}")
        # =================================================

        # After calculating pnl, update risk manager
        if hasattr(self, 'execution') and self.execution:
            self.execution.update_trade_pnl(order, pnl)
        
        self.completed_orders.append(order.copy())
        del self.orderbook[symbol]
        
        self.save_trade(order)
        self.send_trade_alert(order, "EXIT")
        print(f"Position closed: {symbol} P&L: ₹{pnl:+,.2f}")
    
    def close_all_positions(self):
        for symbol in list(self.orderbook.keys()):
            price = self.data_service.get_current_price(symbol)
            if price:
                self._close_position(symbol, price, "MANUAL_CLOSE")
    
##    def is_market_open(self) -> bool:
##        current_time = Config.get_current_time().time()
##        weekday = Config.get_current_time().weekday()
##        return (datetime.time(9, 15) <= current_time <= datetime.time(15, 30)) and (weekday < 5)


    def is_market_open(self) -> bool:
        # TEMPORARY OVERRIDE FOR TESTING - REMOVE AFTER
        # Force market open to test index data fetching
        return True  # Force open for testing

    def _get_emotional_state(self, pnl: float) -> str:
        """Determine emotional state based on P&L"""
        if pnl > 500:
            return "Confident"
        elif pnl > 200:
            return "Satisfied"
        elif pnl > 0:
            return "Cautious"
        elif pnl > -200:
            return "Disappointed"
        elif pnl > -500:
            return "Anxious"
        else:
            return "Frustrated"


    def get_health_status(self) -> Dict:
        """Get current health status"""
        return self.health_checker.get_summary()
    
    def print_health_status(self):
        """Print health status to console"""
        status = self.health_checker.get_status()
        print("\n" + "="*60)
        print("🏥 HEALTH STATUS")
        print("="*60)
        print(f"   Status: {'🟢 HEALTHY' if status.is_healthy else '🔴 UNHEALTHY'}")
        print(f"   CPU: {status.cpu_percent}%")
        print(f"   Memory: {status.memory_percent}%")
        print(f"   Disk: {status.disk_usage}%")
        print(f"   DB Size: {status.db_size_mb} MB")
        print(f"   Open Positions: {status.open_positions}")
        print(f"   Uptime: {status.uptime_seconds/3600:.1f} hours")
        print(f"   API Status: {status.api_status}")
        print(f"   Errors (1h): {status.errors_last_hour}")
        print("="*60)
    
    def get_journal_stats(self) -> Dict:
        """Get trade journal statistics"""
        return self.trade_journal.get_performance_stats()
    
    def print_journal_stats(self):
        """Print journal stats to console"""
        stats = self.trade_journal.get_performance_stats()
        if stats:
            print("\n" + "="*60)
            print("📔 TRADE JOURNAL STATISTICS")
            print("="*60)
            print(f"   Total Trades: {stats.get('total_trades', 0)}")
            print(f"   Win Rate: {stats.get('win_rate', 0):.1f}%")
            print(f"   Total P&L: ₹{stats.get('total_pnl', 0):,.2f}")
            print(f"   Avg P&L: ₹{stats.get('avg_pnl', 0):,.2f}")
            print(f"   Best Trade: ₹{stats.get('best_trade', 0):,.2f}")
            print(f"   Worst Trade: ₹{stats.get('worst_trade', 0):,.2f}")
            print("="*60)

    
    def verify_api_connection(self) -> bool:
        test_chart = self.data_service.get_symbol_data('RELIANCE')
        return test_chart is not None
    
    # def run(self):
    #     log.header("STARTING MAIN TRADING LOOP")
    #     print(f"Market open? {self.is_market_open()}")
    #     print(f"Current time: {Config.get_current_time()}")
    #     print(f"Watchlist: {Config.WATCHLIST}")
        
    #     try:
    #         while True:
    #             if self.is_market_open():
    #                 print(f"\n🕐 Market is OPEN - Scanning watchlist: {Config.WATCHLIST}")
    #                 for symbol in Config.WATCHLIST:
    #                     print(f"\n📊 Processing {symbol}...")
    #                     chart = self.data_service.get_symbol_data(symbol)
    #                     if chart is not None and len(chart) > 20:
    #                         # Generate signals
    #                         signals = self.generate_signals(chart, symbol)
                            
    #                         # Log what signals we got
    #                         if signals['buy_call'] or signals['buy_put']:
    #                             print(f"🔔 SIGNAL DETECTED for {symbol}: CALL={signals['buy_call']}, PUT={signals['buy_put']}")
    #                             self.place_stock_order(symbol, signals, chart)
    #                         else:
    #                             print(f"   No signal for {symbol}")
                            
    #                         # Monitor positions if any
    #                         if symbol in self.orderbook:
    #                             self.monitor_open_positions(symbol)
    #                     else:
    #                         print(f"   ⚠️ No chart data for {symbol}")
                    
    #                 # Wait before next scan (15 seconds per timeframe)
    #                 wait_time = 15 * int(Config.TIMEFRAME)
    #                 log.info(f"Waiting {wait_time} seconds before next scan...")
    #                 time.sleep(wait_time)
    #             else:
    #                 print("🕐 Market closed. Waiting...")
    #                 if Config.get_current_time().time() > datetime.time(15, 30):
    #                     print("Market closed for the day. Exiting...")
    #                     self.close_all_positions()
    #                     break
    #                 time.sleep(60)




    # def run(self):
    #     print("Starting main trading loop...")
    #     print(f"Market open? {self.is_market_open()}")
    #     print(f"Current time: {Config.get_current_time()}")
    #     print(f"Watchlist: {Config.WATCHLIST}")
        
    #     try:
    #         while True:
    #             if self.is_market_open():
    #                 print(f"\n🕐 Market is OPEN - Scanning watchlist...")
    #                 for symbol in Config.WATCHLIST:
    #                     chart = self.data_service.get_symbol_data(symbol)
    #                     if chart is not None and len(chart) > 20:
    #                         signals = self.generate_signals(chart, symbol)
    #                         if signals['buy_call'] or signals['buy_put']:
    #                             self.place_stock_order(symbol, signals, chart)
    #                         if symbol in self.orderbook:
    #                             self.monitor_open_positions(symbol)
                    
    #                 wait_time = 15 * int(Config.TIMEFRAME)
    #                 print(f"⏳ Waiting {wait_time} seconds...")
    #                 time.sleep(wait_time)
    #             else:
    #                 # Market is closed - wait and check again
    #                 current_time = Config.get_current_time()
    #                 print(f"🕐 Market closed. Current time: {current_time.strftime('%H:%M:%S')}")
                    
    #                 # Calculate time until next market open
    #                 next_open = Config.get_current_time().replace(hour=9, minute=15, second=0, microsecond=0)
    #                 if current_time.time() > datetime.time(15, 30):
    #                     # Market closed for the day, wait until tomorrow
    #                     next_open = next_open + datetime.timedelta(days=1)
                        
    #                 wait_seconds = (next_open - current_time).total_seconds()
    #                 if wait_seconds > 0:
    #                     print(f"📅 Next market open: {next_open.strftime('%Y-%m-%d %H:%M:%S')}")
    #                     print(f"⏰ Waiting {wait_seconds/60:.0f} minutes until market opens...")
    #                     # Wait smaller chunks to allow keyboard interrupt
    #                     for _ in range(int(wait_seconds / 60)):
    #                         time.sleep(60)
    #                         if self.is_market_open():
    #                             break
    #                 else:
    #                     time.sleep(60)
                        
    #     except KeyboardInterrupt:
    #         print("\n🛑 Bot stopped by user")
    #         self.close_all_positions()
    #     except Exception as e:
    #         print(f"❌ Error in main loop: {e}")
    #         import traceback
    #         traceback.print_exc()

        
                    
    #     except KeyboardInterrupt:
    #         print("\n🛑 Bot stopped by user")
    #         self.close_all_positions()
    #     except Exception as e:
    #         print(f"❌ Error in main loop: {e}")
    #         import traceback
    #         traceback.print_exc()
    #         self.close_all_positions()



    def run(self):
        log.header("STARTING MAIN TRADING LOOP")
        log.info(f"Market open? {self.is_market_open()}")
        log.info(f"Current time: {Config.get_current_time()}")
        log.info(f"Active Watchlist: {self.watchlist}")
        log.info(f"Trading Mode: {Config.TRADING_MODE}")
        
        if self.option_active:
            log.section("OPTION TRADING MODE ACTIVE")
            log.info(f"Trading options on: {getattr(Config, 'OPTION_SYMBOLS', [])}")
            log.info(f"OTM Count: {getattr(Config, 'OPTION_OTM_COUNT', 1)}")
            log.info(f"Max Lots: {getattr(Config, 'OPTION_MAX_LOTS_PER_TRADE', 2)}")
            log.risk(f"Stop Loss: {getattr(Config, 'OPTION_SL_MULTIPLIER', 0.2)*100}% of premium")
            log.trade(f"Target: {getattr(Config, 'OPTION_TARGET_MULTIPLIER', 2.5)*100}% of premium")
        
        try:
            while True:
                if self.is_market_open():
                    print(f"\n🕐 Market is OPEN - {Config.get_current_time().strftime('%H:%M:%S')}")
                    
                    # Use self.watchlist (dynamic based on mode)
                    for symbol in self.watchlist:
                        print(f"\n📊 Processing {symbol}...")
                        chart = self.data_service.get_symbol_data(symbol)
                        
                        if chart is not None and len(chart) > 20:
                            # Call process_symbol_with_options which handles everything
                            # This method generates signals internally and returns signals
                            signals = self.process_symbol_with_options(symbol, chart)
                            
                            # Now signals is defined and we can use it for debugging
                            if signals and (signals.get('buy_call') or signals.get('buy_put')):
                                log.signal(f"SIGNAL FOUND for {symbol}: CALL={signals.get('buy_call')}, PUT={signals.get('buy_put')}")
                            else:
                                log.data(f"NO SIGNAL for {symbol}")
                                
                            # Also print strategy details
                            if signals:
                                for s in signals.get('strategies', []):
                                    print(f"   Strategy {s['name']}: {s['signals']}")
                        else:
                            print(f"   ⚠️ No chart data for {symbol}")
                        
                        # Monitor existing positions
                        if symbol in self.orderbook:
                            self.monitor_option_position(symbol)



                    # ============ ADD PAPER TRADING MONITORING HERE ============
                    # RIGHT AFTER processing all symbols, BEFORE the wait time
                    if self.paper_trading_enabled and hasattr(self.execution, 'paper_trading'):
                        # Get current prices for paper positions
                        if self.execution.paper_trading.positions:
                            symbols = list(self.execution.paper_trading.positions.keys())
                            ltp_data = {}
                            for sym in symbols:
                                try:
                                    price = self.data_service.get_current_price(sym)
                                    if price:
                                        ltp_data[sym] = price
                                except:
                                    pass
                            
                            # Monitor paper positions
                            if hasattr(self.execution, 'monitor_paper_positions'):
                                self.execution.monitor_paper_positions(ltp_data)
                            
                            # Show paper summary every few cycles
                            if hasattr(self, '_paper_cycle_count'):
                                self._paper_cycle_count += 1
                            else:
                                self._paper_cycle_count = 0
                            
                            if self._paper_cycle_count % 10 == 0:  # Every 10 cycles
                                summary = self.execution.paper_trading.get_account_summary()
                                print(f"\n📊 PAPER TRADING SUMMARY:")
                                print(f"   Balance: ₹{summary['current_balance']:,.2f}")
                                print(f"   Total P&L: ₹{summary['total_pnl']:+,.2f}")
                                print(f"   Win Rate: {summary['win_rate']}%")
                                print(f"   Active Positions: {summary['active_positions']}")
                    # ============ END PAPER TRADING MONITORING ============
                    

                            
                    # ============ ADD THIS AFTER PROCESSING ALL SYMBOLS ============
                    # Force garbage collection to free memory
                    gc.collect()
                    #
                
                    # Wait before next scan
                    wait_time = 15 * int(Config.TIMEFRAME)
                    print(f"\n⏳ Waiting {wait_time} seconds before next scan...")
                    
                    # Wait in small increments to allow for interrupt
                    for _ in range(wait_time):
                        time.sleep(1)
                        if not self.is_market_open():
                            break
                            
                else:
                    # Market is closed
                    current_time = Config.get_current_time()
                    print(f"🕐 Market closed. Current time: {current_time.strftime('%H:%M:%S')}")
                    print(f"   Next market open: 9:15 AM")
                    
                    # Close any open positions at end of day
                    if current_time.time() > datetime.time(15, 30):
                        if self.orderbook:
                            print("Market closed for the day. Closing all positions...")
                            self.close_all_positions()
                        
                        # Calculate next market open
                        next_open = current_time.replace(hour=9, minute=15, second=0)
                        if current_time.time() > datetime.time(15, 30):
                            next_open = next_open + timedelta(days=1)
                        
                        wait_seconds = (next_open - current_time).total_seconds()
                        if wait_seconds > 0:
                            print(f"📅 Next market open: {next_open.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"⏰ Waiting {wait_seconds/3600:.1f} hours...")
                            
                            # Wait in 5-minute chunks
                            for _ in range(int(wait_seconds / 300)):
                                time.sleep(300)
                                if self.is_market_open():
                                    break
                    else:
                        time.sleep(60)
                            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            self.close_all_positions()
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            self.close_all_positions()


##
##    def log_all_signals(self, chart: pd.DataFrame, symbol: str):
##        """Log all strategy signals for debugging"""
##        log.section(f"SIGNAL SUMMARY for {symbol}"))
##        print("-" * 50)
##        
##        for strategy in self.strategies:
##            try:
##                strategy.calculate_indicators(chart)
##                strategy_signals = strategy.generate_signals(chart, symbol)
##                name = strategy.get_strategy_name()
##                
##                # Calculate score for this strategy's direction
##                if strategy_signals.get('buy_call'):
##                    scores = SignalStrength.calculate_signal_strength(chart, symbol, 'BUY')
##                    log.signal(f"✅ {name}: BUY (Score: {scores['overall']}/100)")
##                elif strategy_signals.get('buy_put'):
##                    scores = SignalStrength.calculate_signal_strength(chart, symbol, 'SELL')
##                    log.info(f"⚪ {name}: No signal")
##                else:
##                    log.info(f"⚪ {name}: No signal")
##            except Exception as e:
##                print(f"   ❌ {strategy.get_strategy_name()}: Error - {e}")
##        
##        print("-" * 50)

    
    # def process_symbol(self, symbol: str, chart: pd.DataFrame):
    #     """Process trading logic for one symbol"""
    #     try:
    #         # Calculate indicators for all strategies
    #         for strategy in self.strategies:
    #             strategy.calculate_indicators(chart)
            
    #         # Generate signals
    #         signals = self.generate_signals(chart, symbol)
            
    #         # Calculate signal strength for debugging
    #         scores_buy = SignalStrength.calculate_signal_strength(chart, symbol, 'BUY')
    #         scores_sell = SignalStrength.calculate_signal_strength(chart, symbol, 'SELL')
            
    #         # Detailed logging
    #         print(f"\n{'─'*50}")
    #         print(f"📊 {symbol} Analysis:")
    #         print(f"   Current Price: ₹{chart['close'].iloc[-1]:.2f}")
    #         print(f"   Buy Signal: {'✅ YES' if signals['buy_call'] else '❌ NO'} (Score: {scores_buy['overall']}/100)")
    #         print(f"   Sell Signal: {'✅ YES' if signals['buy_put'] else '❌ NO'} (Score: {scores_sell['overall']}/100)")
    #         print(f"   Buy Grade: {SignalStrength.get_signal_grade(scores_buy)}")
    #         print(f"   Sell Grade: {SignalStrength.get_signal_grade(scores_sell)}")
    #         print(f"{'─'*50}")
            
    #         # Execute order if signal strong enough
    #         if (signals['buy_call'] or signals['buy_put']) and symbol not in self.orderbook:
    #             # Determine which signal is stronger
    #             if signals['buy_call'] and signals['buy_put']:
    #                 # Both signals present - choose the stronger one
    #                 if scores_buy['overall'] > scores_sell['overall']:
    #                     action = 'BUY'
    #                     print(f"🎯 Both signals present - Choosing BUY (Score: {scores_buy['overall']} > {scores_sell['overall']})")
    #                 else:
    #                     action = 'SELL'
    #                     print(f"🎯 Both signals present - Choosing SELL (Score: {scores_sell['overall']} > {scores_buy['overall']})")
                
    #             print(f"\n🚀 Placing order for {symbol}")
    #             self.place_stock_order(symbol, signals, chart)
                
    #         # Monitor existing positions
    #         if symbol in self.orderbook:
    #             order = self.orderbook[symbol]
    #             if 'traded' not in order:
    #                 order['traded'] = "yes"
                    
    #             if order.get('traded') == "yes":
    #                 try:
    #                     current_price = self.data_service.get_current_price(symbol)
    #                     if current_price:
    #                         print(f"   📍 Monitoring {symbol}: Current ₹{current_price:.2f} | SL: ₹{order.get('sl', 0):.2f}")
    #                     self.monitor_open_positions(symbol)
    #                 except Exception as e:
    #                     print(f"   ❌ Error monitoring {symbol}: {e}")
                                
    #     except Exception as e:
    #         print(f"❌ Error processing {symbol}: {str(e)}")
    #         import traceback
    #         traceback.print_exc()

    def log_all_signals(self, chart: pd.DataFrame, symbol: str):
        """Log all strategy signals in beautiful table format"""
        
        # Collect all strategy signals
        table_data = []
        
        for strategy in self.strategies:
            try:
                strategy.calculate_indicators(chart)
                strategy_signals = strategy.generate_signals(chart, symbol)
                name = strategy.get_strategy_name()
                
                # Determine signal type and score
                if strategy_signals.get('buy_call'):
                    scores = SignalStrength.calculate_signal_strength(chart, symbol, 'BUY')
                    signal_type = "BUY CALL"
                    score = scores['overall']
                    color = "🟢"
                elif strategy_signals.get('buy_put'):
                    scores = SignalStrength.calculate_signal_strength(chart, symbol, 'SELL')
                    signal_type = "SELL PUT"
                    score = scores['overall']
                    color = "🔴"
                else:
                    signal_type = "NO SIGNAL"
                    score = 0
                    color = "⚪"
                
                table_data.append({
                    'Strategy': name[:25],
                    'Signal': f"{color} {signal_type}",
                    'Score': score if score > 0 else "-",
                    'Confidence': self._get_confidence_level(score)
                })
                
            except Exception as e:
                table_data.append({
                    'Strategy': strategy.get_strategy_name()[:25],
                    'Signal': "❌ ERROR",
                    'Score': "-",
                    'Confidence': str(e)[:20]
                })
        
        # Display the table
        if table_data:
            log.signal_table(table_data)
        else:
            log.info("No strategies to display")

    def _get_confidence_level(self, score: int) -> str:
        """Get confidence level based on score"""
        if score >= 70:
            return "HIGH 🔥"
        elif score >= 50:
            return "MEDIUM ⭐"
        elif score >= 30:
            return "LOW 💧"
        elif score > 0:
            return "VERY LOW ⚠️"
        else:
            return "-"



    def should_trade_equity(self, symbol: str) -> bool:
        """Check if equity trading is allowed for this symbol"""
        from config import Config
        
        if Config.TRADING_MODE == "FNO_ONLY":
            return False
        return True
    
    def should_trade_fno(self, symbol: str) -> bool:
        """Check if F&O trading is allowed for this symbol"""
        from config import Config
        from config import Config
        
        if Config.TRADING_MODE == "EQUITY_ONLY":
            return False
        
        # Check if symbol is in FNO list
        if symbol not in option_config.OPTION_SYMBOLS:
            return False
        
        return True


    # def process_symbol_with_options(self, symbol: str, chart: pd.DataFrame):
    #     """Process symbol including option trading"""
    #     try:
    #         # Generate signals from strategies
    #         signals = self.generate_signals(chart, symbol)
            
    #         # Check if we should trade options for this symbol
    #         should_trade_options = (
    #             self.option_active and 
    #             self.option_processor and
    #             symbol in getattr(Config, 'OPTION_SYMBOLS', [])
    #         )
            
    #         # Check if we have a signal
    #         if signals.get('buy_call') or signals.get('buy_put'):
    #             # Log the signal
    #             self.log_all_signals(chart, symbol)
                
    #             # Get signal strength
    #             action = 'BUY' if signals.get('buy_call') else 'SELL'
    #             scores = SignalStrength.calculate_signal_strength(chart, symbol, action)
                
    #             print(f"\n📊 Signal Strength: {scores['overall']}/100 (Required: {Config.MIN_SIGNAL_STRENGTH})")
                
    #             if SignalStrength.should_trade(scores):
    #                 if should_trade_options:
    #                     # Trade options instead of equities
    #                     signal_data = {
    #                         'buy_call': signals.get('buy_call'),
    #                         'buy_put': signals.get('buy_put'),
    #                         'triggering_strategy': self._get_triggering_strategy(signals)
    #                     }
                        
    #                     current_time = Config.get_current_time()
    #                     option_order = self.option_processor.process_signal_for_option(
    #                         signal_data, chart, symbol, current_time
    #                     )
                        
    #                     if option_order and symbol not in self.orderbook:
    #                         self.orderbook[symbol] = option_order
    #                         self.save_trade(option_order)
    #                         self.send_trade_alert(option_order, "ENTRY")
    #                         print(f"✅ OPTION order placed for {symbol}")
    #                     elif option_order:
    #                         print(f"⚠️ Position already exists for {symbol}")
    #                 else:
    #                     # Trade equities as before
    #                     self.place_stock_order(symbol, signals, chart)
    #             else:
    #                 print(f"   Signal too weak ({scores['overall']} < {Config.MIN_SIGNAL_STRENGTH})")
    #         else:
    #             # No signal, just log if debugging
    #             if len(Config.WATCHLIST) <= 5:
    #                 print(f"   No signal for {symbol}")
            
    #         # Monitor existing positions
    #         if symbol in self.orderbook:
    #             self.monitor_option_position(symbol)
                
    #     except Exception as e:
    #         print(f"❌ Error processing {symbol}: {e}")
    #         import traceback
    #         traceback.print_exc()



    def process_symbol_with_options(self, symbol: str, chart: pd.DataFrame):
        """Process symbol including option/equity trading based on mode"""
        try:
            from config import Config
            trading_mode = Config.TRADING_MODE
            
            # Determine symbol type
            is_fno_symbol = symbol in self.fno_watchlist
            is_equity_symbol = symbol in self.equity_watchlist
            
            log.separator()
            log.info(f"Processing {symbol} - Mode: {trading_mode}")
            log.data(f"F&O Symbol: {is_fno_symbol} | Equity Symbol: {is_equity_symbol}")
            print(f"{'='*50}")
            
            # Generate signals
            signals = self.generate_signals(chart, symbol)
            
            # Check if we have a signal
            if signals.get('buy_call') or signals.get('buy_put'):
                # Log the signal
                self.log_all_signals(chart, symbol)
                
                # Get signal strength
                action = 'BUY' if signals.get('buy_call') else 'SELL'
                scores = SignalStrength.calculate_signal_strength(chart, symbol, action)
                
                print(f"\n📊 Signal Strength: {scores['overall']}/100 (Required: {Config.MIN_SIGNAL_STRENGTH})")
                
                if SignalStrength.should_trade(scores):
                    
                    # ============ CASE 1: FNO ONLY Mode ============
                    if trading_mode == "FNO_ONLY" and is_fno_symbol:
                        print(f"🎯 FNO MODE: Trading options for {symbol}")
                        self._execute_option_trade(symbol, signals, chart)
                    
                    # ============ CASE 2: EQUITY ONLY Mode ============
                    elif trading_mode == "EQUITY_ONLY" and is_equity_symbol:
                        print(f"🎯 EQUITY MODE: Trading equities for {symbol}")
                        self._execute_equity_trade(symbol, signals, chart)
                    
                    # ============ CASE 3: BOTH Mode ============
                    elif trading_mode == "BOTH":
                        # Trade F&O if it's an F&O symbol
                        if is_fno_symbol:
                            print(f"🎯 BOTH MODE: Trading options for {symbol}")
                            self._execute_option_trade(symbol, signals, chart)
                        
                        # Also trade equity if it's an equity symbol and not already in a position
                        elif is_equity_symbol and symbol not in self.orderbook:
                            print(f"🎯 BOTH MODE: Trading equities for {symbol}")
                            self._execute_equity_trade(symbol, signals, chart)
                        
                        else:
                            print(f"⚠️ {symbol} not configured for any trading type")
                    
                    else:
                        print(f"⚠️ Trading mode {trading_mode} not configured for {symbol}")
                        print(f"   Is F&O? {is_fno_symbol} | Is Equity? {is_equity_symbol}")
                else:
                    print(f"   Signal too weak ({scores['overall']} < {Config.MIN_SIGNAL_STRENGTH})")
            else:
                # No signal
                if len(self.watchlist) <= 10:
                    print(f"   No signal for {symbol}")
            
            # Monitor existing positions
            if symbol in self.orderbook:
                self.monitor_option_position(symbol)

            # Return signals for debugging in run method
            return signals
                
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None


    

    def _execute_option_trade(self, symbol: str, signals: Dict, chart: pd.DataFrame):
        """Execute option trade"""
        try:
            # Get triggering strategy name
            strategy_name = self._get_triggering_strategy(signals)
        
            signal_data = {
                'buy_call': signals.get('buy_call'),
                'buy_put': signals.get('buy_put'),
                'triggering_strategy': self._get_triggering_strategy(signals)
            }
            
            current_time = Config.get_current_time()
            option_order = self.option_processor.process_signal_for_option(
                signal_data, chart, symbol, current_time
            )
            
            if option_order and symbol not in self.orderbook:
                option_order['strategy'] = strategy_name
                self.orderbook[symbol] = option_order
                self.save_trade(option_order)
                self.send_trade_alert(option_order, "ENTRY")
                print(f"✅ OPTION order placed for {symbol} (Strategy: {strategy_name})")
                return True
            elif option_order:
                log.warning(f"Position already exists for {symbol}")
            else:
                log.error(f"Failed to place option order for {symbol}")
                
        except Exception as e:
            error_msg = str(e)
            if "Market is Closed" in error_msg:
                log.warning(f"Market closed - Cannot place order for {symbol}")
            else:
                log.error(f"Option trade failed: {error_msg}")
    
    def _execute_equity_trade(self, symbol: str, signals: Dict, chart: pd.DataFrame):
        """Execute equity trade"""
        try:
            self.place_stock_order(symbol, signals, chart)
            return True
        except Exception as e:
            print(f"❌ Equity trade failed: {e}")
            return False


    def _get_triggering_strategy(self, signals: Dict) -> str:
        """Get the strategy that triggered the signal"""
        for s in signals.get('strategies', []):
            if s['signals'].get('buy_call') or s['signals'].get('buy_put'):
                return s['name']
        return 'MULTI_STRATEGY'

    def monitor_option_position(self, symbol: str):
        """Monitor open option position with enhanced checks"""
        if symbol not in self.orderbook:
            return
        
        position = self.orderbook[symbol]


        # Get current premium from API
        current_premium = self.option_processor.get_premium(position['name'])
        
        # ============ DETECT MANUAL INTERVENTION ============
        # Check if stop loss was manually changed on exchange
        if hasattr(self.tsl, 'get_order_details'):
            order_details = self.tsl.get_order_details(position.get('super_order_id'))
            if order_details:
                exchange_sl = order_details.get('stopLossPrice', 0)
                our_sl = position.get('sl', 0)
                
                # If exchange SL is different from our recorded SL (by more than 0.5)
                if abs(exchange_sl - our_sl) > 0.5:
                    log.warning(f"⚠️ MANUAL INTERVENTION DETECTED for {symbol}!")
                    log.warning(f"   Our SL: ₹{our_sl} | Exchange SL: ₹{exchange_sl}")
                    log.warning(f"   Difference: ₹{abs(exchange_sl - our_sl)}")
                    
                    # Update our records
                    position['sl'] = exchange_sl
                    position['manual_sl_modified'] = True
                    
                    # Send alert
                    self.telegram.send_alert(
                        f"⚠️ MANUAL SL CHANGE DETECTED\n"
                        f"Symbol: {symbol}\n"
                        f"New SL: ₹{exchange_sl}\n"
                        f"Old SL: ₹{our_sl}"
                    )
        
        # Check if position was manually closed
        if current_premium == 0 or current_premium is None:
            log.warning(f"⚠️ Position {symbol} may have been manually closed (premium=0)")
            self.orderbook.pop(symbol, None)
            self.telegram.send_alert(f"🔴 MANUAL CLOSE DETECTED: {symbol} position closed externally")
            return
        
        
        # Skip if not an option position
        if 'option_type' not in position:
            # Handle equity position
            self.monitor_open_positions(symbol)
            return
        
        # Get current data
        if not self.option_processor:
            return
        
        current_premium = self.option_processor.get_premium(position['name'])
        if current_premium == 0:
            return
        
        current_spot = self.option_processor.get_spot_price(position.get('underlying', 'NIFTY'))
        entry_spot = position.get('entry_spot', current_spot)
        
        # Calculate holding time
        if 'entry_time' in position and position.get('date'):
            try:
                entry_datetime_str = f"{position['date']} {position['entry_time']}"
                from datetime import datetime as dt
                entry_datetime = dt.strptime(entry_datetime_str, '%Y-%m-%d %H:%M:%S')
                if Config.IST:
                    entry_datetime = Config.IST.localize(entry_datetime)
                holding_minutes = (Config.get_current_time() - entry_datetime).total_seconds() / 60
                position['holding_minutes'] = holding_minutes
            except Exception as e:
                print(f"Time calculation error: {e}")
        
        # Check stop loss
        stop_hit, stop_reason = self.option_processor.manager.check_stop_loss(
            position, current_premium, current_spot, entry_spot
        )
        
        if stop_hit:
            self._close_option_position(symbol, current_premium, stop_reason)
            return
        
        # Check targets
        target_hit, target_reason, exit_price = self.option_processor.manager.check_targets(
            position, current_premium, current_spot
        )
        
        if target_hit:
            # If partial booking, handle accordingly
            if position.get('partial_booked', False):
                # Close remaining lots
                self._close_option_position(symbol, exit_price, target_reason)
            else:
                # Full exit or partial
                self._close_option_position(symbol, exit_price, target_reason)
            return
        
        # Update trailing stop
        current_delta = position.get('greeks', {}).get('delta', 0.5)
        new_sl = self.option_processor.manager.update_trailing_stop(
            position['name'], current_premium, position['entry_price'], current_delta
        )
        
        if new_sl and new_sl > position.get('sl', 0):
            position['sl'] = new_sl
            print(f"📈 TRAILING STOP UPDATED: {position['name']} SL now ₹{new_sl:.2f}")

    def _close_option_position(self, symbol: str, exit_price: float, reason: str):
        """Close an option position"""
        if symbol not in self.orderbook:
            return
        
        position = self.orderbook[symbol]
        
        # Calculate P&L
        entry_price = position.get('entry_price', 0)
        qty = position.get('qty', 0)
        option_type = position.get('option_type', 'CALL')
        
        if option_type == 'CALL':
            pnl = (exit_price - entry_price) * qty
        else:
            pnl = (entry_price - exit_price) * qty
        
        # Update position
        position.update({
            'exit_price': exit_price,
            'pnl': pnl,
            'remark': reason,
            'exit_time': Config.get_current_time().strftime('%H:%M:%S'),
            'status': 'closed'
        })
        
        self.completed_orders.append(position.copy())
        del self.orderbook[symbol]
        
        # Save to database
        self.save_trade(position)
        
        # Send alert
        emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➖"
        alert_msg = f"""🔴 OPTION EXIT: {position.get('name', '')}
    {emoji} P&L: ₹{pnl:+,.2f}
    Reason: {reason}
    Exit Price: ₹{exit_price:.2f}"""
        
        self.send_trade_alert(position, "EXIT")
        print(f"✅ Option position closed: {symbol} | P&L: ₹{pnl:+,.2f} | Reason: {reason}")


    def log_manual_intervention(self, action: str, details: Dict):
        """Log manual intervention for audit trail"""
        try:
            intervention_record = {
                'timestamp': Config.get_current_time().strftime('%Y-%m-%d %H:%M:%S'),
                'action': action,
                'details': str(details),
                'source': 'MANUAL'
            }
            
            # Create table if not exists
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manual_interventions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    action TEXT,
                    details TEXT
                )
            ''')
            cursor.execute('''
                INSERT INTO manual_interventions (timestamp, action, details)
                VALUES (?, ?, ?)
            ''', (intervention_record['timestamp'], action, intervention_record['details']))
            self.conn.commit()
            
            # Send alert if telegram exists
            if hasattr(self, 'telegram') and self.telegram:
                self.telegram.send_alert(f"📝 MANUAL ACTION LOGGED: {action}")
            log.warning(f"MANUAL INTERVENTION: {action} - {details}")
            
        except Exception as e:
            log.error(f"Failed to log manual intervention: {e}")


if __name__ == "__main__":
    try:
        bot = OptionTradingBot()
        bot.telegram.send_startup_message()
        print(f"🔧 OPTION_EXPIRY = {Config.OPTION_EXPIRY}")
        if not bot.verify_api_connection():
            print("API connection failed!")
            winsound.Beep(2000, 1000)
            sys.exit(1)
        
        #bot.telegram.send_alert("🤖 Trading Bot Started with TOTP Authentication!")
        bot.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Program terminated")











