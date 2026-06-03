# config.py
import datetime
import pytz

class Config:

    # ============ TRADING MODE SELECTOR ============
    # Options: 'EQUITY_ONLY', 'FNO_ONLY', 'BOTH'
    TRADING_MODE = "FNO_ONLY"  # Change this to switch modes
    

    # ============ API Credentials (TOTP Authentication) ============
    CLIENT_CODE = "1109910610"
    PIN = "121295"
    TOTP_SECRET = "IXTDHOOGHOPVCTMTE2V3NCYCMUMQWA4M"
    
    # ============ Secondary Trading Accounts (Copy Trading) ============
    TRADING_ACCOUNTS = {
        "ACCOUNT_2": {
            "client_code": "",
            "pin": "",
            "totp_secret": "",
            "multiplier": 1.0,
            "enabled": False
        },
        "ACCOUNT_3": {
            "client_code": "",
            "pin": "",
            "totp_secret": "",
            "multiplier": 0.5,
            "enabled": False
        },
    }
    
    # Copy Trading Settings
    EXECUTION_MODE = "PARALLEL"
    MAX_RETRIES_PER_ACCOUNT = 2
    REQUIRE_ALL_ACCOUNTS = False
    TRADE_DELAY_SECONDS = 1

    # Risk Management
    BASE_CAPITAL = 30000
    MARKET_MONEY_RISK_PERCENT = 0.01
    BASE_CAPITAL_RISK_PERCENT = 0.005
    MAX_CAPITAL_PER_TRADE = 0.5
    MAX_ORDERS_PER_DAY = 5
    RISK_REWARD_RATIO = 3
    ATR_MULTIPLIER = 5
    Minimum_trading_capital = 10
    BROKER_MARGIN_MULTIPLIER = 4
    
    # Trading Parameters
    TIMEFRAME = "1"
    #OTM_COUNT = 10
    MAX_HOLDING_HOURS = 5
    REENTRY_ALLOWED = True
    USE_SUPER_ORDERS = True
    TRAILING_JUMP = 2
    
    # Optimization Parameters
    MIN_SIGNAL_STRENGTH = 10
    SIGNAL_COOLDOWN_MINUTES = 5
    MAX_SIGNALS_PER_HOUR = 3
    USE_MARKET_REGIME_FILTER = True
    USE_Kelly_SIZING = True
    MIN_KELlY_TRADES = 10
    HALF_KELLY = True
    ENABLE_ADAPTIVE_TRAILING = True
    ENABLE_DYNAMIC_EXITS = True
    ENABLE_STRATEGY_WEIGHT_OPTIMIZATION = True


    # ============ Paper Trading Settings ============
    PAPER_TRADING_ENABLED = False
    PAPER_BALANCE = 1000000  # ₹10 Lakhs

    # ============ Logging Settings ============
    LOG_LEVEL = "INFO"
    LOG_DIR = "logs"
    LOG_RETENTION_DAYS = 30


    # ============ DAILY RISK LIMITS (PROFESSIONAL) ============
    MAX_DAILY_LOSS = 2500  # Maximum loss/drawdown per day
    MAX_DAILY_LOSS_MODE = "DRAWDOWN"  # "ABSOLUTE" or "DRAWDOWN"
    MAX_POSITION_SIZE = 5  # Maximum lots per trade
    MAX_DAILY_TRADES = 10  # Maximum trades per day
    MAX_DAILY_POSITIONS = 3  # Maximum concurrent positions



    # Strategy Configuration
    
    ACTIVE_STRATEGIES = [
        # Existing
        'EMA_RSI',
        'MACD_Bollinger', 
        'RSI_50_Crossover',
        'VWAP_Reversion',
        'MA_Crossover_50_200',
        'ORB_30min',
        # New - Trend Following
        'Supertrend_RSI',
        'TripleEMA_ADX',
        'Ichimoku_Cloud',
        # New - Momentum
        'StochasticRSI_MACD',
        # New - Price Action
        'PriceAction_Engulfing_PinBar',
        # New - SMC (Smart Money Concepts)
        'SMC_FairValueGap',
        'SMC_LiquiditySweep',
        'SMC_OrderBlock_BOS'
    ]
    
    STRATEGY_WEIGHTS = {
        'EMA_RSI': 0.08,
        'MACD_Bollinger': 0.08,
        'RSI_50_Crossover': 0.08,
        'VWAP_Reversion': 0.08,
        'MA_Crossover_50_200': 0.08,
        'ORB_30min': 0.05,
        # New weights
        'Supertrend_RSI': 0.08,
        'TripleEMA_ADX': 0.08,
        'Ichimoku_Cloud': 0.08,
        'StochasticRSI_MACD': 0.08,
        'PriceAction_Engulfing_PinBar': 0.07,
        'SMC_FairValueGap': 0.08,
        'SMC_LiquiditySweep': 0.08,
        'SMC_OrderBlock_BOS': 0.08,
    }
    
    # Alerting
    BOT_TOKEN = "8328373474:AAGwUiussSYN3wyiHgvjO0LeMFGOdjRYRjI"
    RECEIVER_CHAT_ID = "881317629"

    # ============ WATCHLISTS ============
    # Equity Watchlist (used for EQUITY_ONLY and BOTH modes)
    EQUITY_WATCHLIST = ['IDBI', 'BEL', 'ITC', 'RELIANCE', 'HDFCBANK', 'TCS', 'INFY']
    
    # F&O Watchlist (used for FNO_ONLY and BOTH modes)
    FNO_WATCHLIST = ['NIFTY'] #['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']
    
    # Option Symbols (same as FNO_WATCHLIST, used for validation)
    OPTION_SYMBOLS =  ['NIFTY'] #["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]
    
    # Timezone
    IST = pytz.timezone('Asia/Kolkata')
    
    @staticmethod
    def get_current_time():
        return datetime.datetime.now(Config.IST)
    
    @staticmethod
    def get_active_watchlist():
        """Return the active watchlist based on trading mode"""
        if Config.TRADING_MODE == "EQUITY_ONLY":
            return Config.EQUITY_WATCHLIST
        elif Config.TRADING_MODE == "FNO_ONLY":
            return Config.FNO_WATCHLIST
        else:  # BOTH mode
            return list(set(Config.EQUITY_WATCHLIST + Config.FNO_WATCHLIST))


    # ============ MASTER SWITCH ============
    OPTION_TRADING_ENABLED: bool = True  # This will be controlled by trading mode
    
    # ============ STRIKE SELECTION ============
    OPTION_OTM_COUNT: int = 2  # 1 OTM (safer)
    OPTION_EXPIRY: int = 0
    
    # ============ RISK MANAGEMENT (CONSERVATIVE FOR OPTIONS) ============
    OPTION_SL_MULTIPLIER: float = 0.20  # 20% stop (was 30%)
    OPTION_THETA_STOP_PERCENT: float = 0.10  # 10% theta stop
    OPTION_FIXED_STOP_RUPEE: float = 10.0  # ₹10 max loss
    OPTION_MAX_LOSS_PERCENT: float = 0.15  # Max 15% loss per trade
    
    # ============ PROFIT TARGETS ============
    OPTION_TARGET_MULTIPLIER: float = 2.5  # 250% target (reduced from 300%)
    OPTION_STRETCH_TARGET_MULTIPLIER: float = 4.0  # 400% stretch
    
    # ============ POSITION SIZING (CONSERVATIVE) ============
    OPTION_MAX_LOTS_PER_TRADE: int = 1  # Max 2 lots (reduced from 5)
    OPTION_RISK_PER_TRADE_PERCENT: float = 0.10  # 10% of capital (reduced from 1%)
    OPTION_MIN_PREMIUM_FOR_TRADE: float = 15.0  # Minimum ₹15 premium
    
    # ============ GREEKS FILTERS ============
    MIN_DELTA_FOR_ENTRY: float = 0.35
    MAX_DELTA_FOR_ENTRY: float = 0.65  # New - avoid deep ITM/OTM
    MAX_THETA_PER_DAY: float = -8
    MIN_IV_PERCENT: float = 12
    MAX_IV_PERCENT: float = 40
    
    # ============ TIME-BASED EXITS ============
    OPTION_MAX_HOLDING_HOURS: int = 2  # Reduced from 4
    OPTION_EARLY_EXIT_PROFIT_PERCENT: float = 40
    
    # ============ SAFETY FILTERS ============
    OPTION_AVOID_EXPIRY_WEEK: bool = True
    OPTION_CHAIN_CACHE_SECONDS: int = 30
    OPTION_ALERTS_ENABLED: bool = True
    
    # ============ COPY TRADING ============
    COPY_OPTION_TRADES: bool = False

    # Strategy to option type mapping
    STRATEGY_OPTION_MAPPING = {
        'EMA_RSI': 'INDEX',
        'MACD_Bollinger': 'INDEX',
        'RSI_50_Crossover': 'INDEX',
        'VWAP_Reversion': 'INDEX',
        'MA_Crossover_50_200': 'INDEX',
        'ORB_30min': 'INDEX'
    }

    # Option alerts
    OPTION_ALERTS_ENABLED = True


    
# ============ SET LEGACY WATCHLIST AFTER CLASS DEFINITION ============
# This must be AFTER the class is fully defined to avoid NameError
Config.WATCHLIST = Config.get_active_watchlist()
