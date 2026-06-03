# logging_config.py
import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path

class TradingLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Setup main logger
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for all logs (rotating)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'trading_bot.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=30
        )
        file_handler.setLevel(logging.DEBUG)
        
        # File handler for errors only
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': record.levelname,
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'message': record.getMessage()
                }
                
                # Add extra fields if present
                if hasattr(record, 'trade_data'):
                    log_entry['trade_data'] = record.trade_data
                if hasattr(record, 'performance_metrics'):
                    log_entry['performance_metrics'] = record.performance_metrics
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry)
        
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
        error_handler.setFormatter(json_formatter)
        
        # Simple console formatter
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Trade logger (separate file)
        trade_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'trades.log',
            maxBytes=5*1024*1024,
            backupCount=20
        )
        trade_handler.setLevel(logging.INFO)
        trade_handler.setFormatter(console_formatter)
        self.trade_logger = logging.getLogger('Trades')
        self.trade_logger.setLevel(logging.INFO)
        self.trade_logger.addHandler(trade_handler)
        
        # Performance logger
        perf_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'performance.log',
            maxBytes=5*1024*1024,
            backupCount=12
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(json_formatter)
        self.perf_logger = logging.getLogger('Performance')
        self.perf_logger.setLevel(logging.INFO)
        self.perf_logger.addHandler(perf_handler)
    
    def log_trade(self, trade_data: dict):
        """Log trade execution"""
        self.trade_logger.info(f"TRADE: {json.dumps(trade_data)}")
        self.logger.info(
            f"Trade executed: {trade_data.get('action')} {trade_data.get('quantity')} {trade_data.get('symbol')}",
            extra={'trade_data': trade_data}
        )
    
    def log_error(self, error: str, context: dict = None):
        """Log error with context"""
        self.logger.error(f"{error} | Context: {json.dumps(context) if context else 'N/A'}", exc_info=True)
    
    def log_performance(self, metrics: dict, period: str = 'daily'):
        """Log performance metrics"""
        self.perf_logger.info(json.dumps({
            'period': period,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }))
    
    def log_signal(self, symbol: str, strategy: str, signal: dict, strength: int):
        """Log trading signal"""
        self.logger.info(
            f"Signal: {symbol} | {strategy} | {signal} | Strength: {strength}",
            extra={'trade_data': {'symbol': symbol, 'strategy': strategy, 'signal': signal, 'strength': strength}}
        )
    
    def get_latest_trades(self, limit: int = 20) -> list:
        """Read latest trades from log"""
        try:
            with open('logs/trades.log', 'r') as f:
                lines = f.readlines()
                return [json.loads(line.split('TRADE: ')[1]) for line in lines[-limit:] if 'TRADE:' in line]
        except:
            return []

# Singleton instance
trading_logger = TradingLogger()