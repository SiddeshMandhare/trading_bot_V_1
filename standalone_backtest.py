# standalone_backtest.py
"""
Standalone Backtest Module - No circular imports
This module contains its own strategy implementations for backtesting
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class BacktestTrade:
    entry_time: str
    exit_time: str
    symbol: str
    action: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_percent: float
    strategy: str
    exit_reason: str

# ============================================
# STRATEGY IMPLEMENTATIONS (Copied from strategies)
# ============================================

class BacktestEMA_RSI:
    def get_strategy_name(self): return "EMA_RSI"
    
    def calculate_indicators(self, chart):
        if len(chart) < 20:
            return
        chart['ema_9'] = chart['close'].ewm(span=9, adjust=False).mean()
        chart['ema_15'] = chart['close'].ewm(span=15, adjust=False).mean()
        chart['rsi'] = self._calculate_rsi(chart['close'], 14)
        chart['sma_20'] = chart['close'].rolling(20).mean()
    
    def _calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, chart, symbol):
        if len(chart) < 2:
            return {'buy_call': False, 'buy_put': False}
        
        cc = chart.iloc[-1]
        prev = chart.iloc[-2]
        
        bullish = prev['ema_9'] < prev['ema_15'] and cc['ema_9'] > cc['ema_15']
        bearish = prev['ema_9'] > prev['ema_15'] and cc['ema_9'] < cc['ema_15']
        
        buy_call = cc['rsi'] > 50 and bullish
        buy_put = cc['rsi'] < 50 and bearish
        
        return {'buy_call': buy_call, 'buy_put': buy_put}


class BacktestMACD_Bollinger:
    def get_strategy_name(self): return "MACD_Bollinger"
    
    def calculate_indicators(self, chart):
        if len(chart) < 26:
            return
        # Calculate MACD
        exp1 = chart['close'].ewm(span=12, adjust=False).mean()
        exp2 = chart['close'].ewm(span=26, adjust=False).mean()
        chart['macd'] = exp1 - exp2
        chart['macd_signal'] = chart['macd'].ewm(span=9, adjust=False).mean()
        chart['macd_hist'] = chart['macd'] - chart['macd_signal']
        
        # Calculate Bollinger Bands
        chart['sma_20'] = chart['close'].rolling(20).mean()
        chart['std_20'] = chart['close'].rolling(20).std()
        chart['upper_band'] = chart['sma_20'] + (chart['std_20'] * 2)
        chart['lower_band'] = chart['sma_20'] - (chart['std_20'] * 2)
        
        # Volume MA
        chart['volume_ma'] = chart['volume'].rolling(20).mean()
    
    def generate_signals(self, chart, symbol):
        if len(chart) < 2:
            return {'buy_call': False, 'buy_put': False}
        
        cc = chart.iloc[-1]
        
        buy_call = (cc['macd'] > cc['macd_signal'] and 
                   cc['close'] > cc['upper_band'] and
                   cc['volume'] > cc['volume_ma'] * 1.5)
        
        sell_signal = (cc['macd'] < cc['macd_signal'] and 
                      cc['close'] < cc['lower_band'] and
                      cc['volume'] > cc['volume_ma'] * 1.5)
        
        return {'buy_call': buy_call, 'buy_put': sell_signal}


class BacktestRSI_Crossover:
    def get_strategy_name(self): return "RSI_Crossover"
    
    def calculate_indicators(self, chart):
        if len(chart) < 15:
            return
        delta = chart['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        chart['rsi'] = 100 - (100 / (1 + rs))
        chart['volume_ma'] = chart['volume'].rolling(20).mean()
    
    def generate_signals(self, chart, symbol):
        if len(chart) < 2:
            return {'buy_call': False, 'buy_put': False}
        
        cc = chart.iloc[-1]
        prev = chart.iloc[-2]
        
        buy_call = cc['rsi'] > 50 and prev['rsi'] <= 50
        buy_put = cc['rsi'] < 50 and prev['rsi'] >= 50
        
        return {'buy_call': buy_call, 'buy_put': buy_put}


class BacktestMA_Crossover:
    def get_strategy_name(self): return "MA_Crossover"
    
    def calculate_indicators(self, chart):
        if len(chart) < 200:
            return
        chart['ma_50'] = chart['close'].rolling(50).mean()
        chart['ma_200'] = chart['close'].rolling(200).mean()
        chart['volume_ma'] = chart['volume'].rolling(20).mean()
    
    def generate_signals(self, chart, symbol):
        if len(chart) < 2:
            return {'buy_call': False, 'buy_put': False}
        
        cc = chart.iloc[-1]
        prev = chart.iloc[-2]
        
        golden_cross = prev['ma_50'] < prev['ma_200'] and cc['ma_50'] > cc['ma_200']
        death_cross = prev['ma_50'] > prev['ma_200'] and cc['ma_50'] < cc['ma_200']
        
        buy_signal = golden_cross and cc['volume'] > cc['volume_ma'] * 1.5
        sell_signal = death_cross and cc['volume'] > cc['volume_ma'] * 1.5
        
        return {'buy_call': buy_signal, 'buy_put': sell_signal}


# Strategy registry
BACKTEST_STRATEGIES = {
    'EMA_RSI': BacktestEMA_RSI,
    'MACD_Bollinger': BacktestMACD_Bollinger,
    'RSI_Crossover': BacktestRSI_Crossover,
    'MA_Crossover': BacktestMA_Crossover,
}

STRATEGY_DISPLAY_NAMES = {
    'EMA_RSI': 'EMA/RSI Strategy',
    'MACD_Bollinger': 'MACD + Bollinger Bands',
    'RSI_Crossover': 'RSI 50 Crossover',
    'MA_Crossover': 'MA Crossover (50/200)',
}


# ============================================
# BACKTEST ENGINE
# ============================================

class StandaloneBacktestEngine:
    def __init__(self, tsl, initial_capital: float = 100000):
        self.tsl = tsl
        self.initial_capital = initial_capital
        self.results = {}
    
    def get_strategy_class(self, strategy_name):
        """Get strategy class by name"""
        return BACKTEST_STRATEGIES.get(strategy_name)
    
    def get_all_strategies(self):
        """Get all available strategies"""
        return list(BACKTEST_STRATEGIES.keys())
    
    def run_backtest(self, symbol: str, strategy_name: str, start_date: str, 
                     end_date: str, timeframe: str = '15') -> Dict:
        """Run backtest for a strategy"""
        
        print(f"\n{'='*60}")
        print(f"📊 BACKTEST STARTED")
        print(f"{'='*60}")
        print(f"   Symbol: {symbol}")
        print(f"   Strategy: {strategy_name}")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Timeframe: {timeframe}")
        print(f"{'='*60}\n")
        
        # Get strategy class
        strategy_class = self.get_strategy_class(strategy_name)
        if not strategy_class:
            return {'error': f'Strategy {strategy_name} not found'}
        
        strategy = strategy_class()
        
        # Fetch historical data
        data = self._fetch_historical_data(symbol, start_date, end_date, timeframe)
        
        if data is None or data.empty:
            print(f"❌ No data available for {symbol}")
            return {'error': 'No data available'}
        
        print(f"✅ Loaded {len(data)} candles")
        
        # Run simulation
        portfolio = self._run_simulation(data, strategy, symbol)
        
        # Calculate metrics
        metrics = self._calculate_metrics(portfolio)
        
        return {
            'metrics': metrics,
            'trades': [asdict(t) for t in portfolio['trades'][-50:]],
            'equity_curve': portfolio['equity_curve']
        }
    
    def _fetch_historical_data(self, symbol, start_date, end_date, timeframe):
        """Fetch historical data using tsl"""
        try:
            # Determine exchange
            indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']
            exchange = 'INDEX' if symbol.upper() in indices else 'NSE'
            
            # Try long-term data first
            data = self.tsl.get_long_term_historical_data(
                tradingsymbol=symbol,
                exchange=exchange,
                timeframe=timeframe,
                from_date=start_date,
                to_date=end_date
            )
            
            if data is not None and not data.empty:
                return data
            
            # Fallback to regular historical
            data = self.tsl.get_historical_data(
                tradingsymbol=symbol,
                exchange=exchange,
                timeframe=timeframe
            )
            
            return data
            
        except Exception as e:
            print(f"⚠️ Data fetch error: {e}")
            return None
    
    def _run_simulation(self, data: pd.DataFrame, strategy, symbol: str) -> Dict:
        """Run the actual simulation"""
        
        portfolio = {
            'capital': self.initial_capital,
            'positions': [],
            'trades': [],
            'equity_curve': []
        }
        
        peak_capital = self.initial_capital
        
        for i in range(len(data)):
            current_data = data.iloc[:i+1].copy()
            current_price = current_data['close'].iloc[-1]
            current_time = current_data.index[i] if hasattr(current_data, 'index') else str(i)
            
            # Calculate indicators
            try:
                strategy.calculate_indicators(current_data)
                signals = strategy.generate_signals(current_data, symbol)
            except Exception as e:
                signals = {'buy_call': False, 'buy_put': False}
            
            # Check existing positions
            for pos in portfolio['positions'][:]:
                if pos['position_type'] == 'LONG':
                    if current_price <= pos['stop_loss']:
                        self._close_position(portfolio, pos, current_price, current_time, 'SL_HIT')
                    elif current_price >= pos['target']:
                        self._close_position(portfolio, pos, current_price, current_time, 'TARGET_HIT')
                else:
                    if current_price >= pos['stop_loss']:
                        self._close_position(portfolio, pos, current_price, current_time, 'SL_HIT')
                    elif current_price <= pos['target']:
                        self._close_position(portfolio, pos, current_price, current_time, 'TARGET_HIT')
            
            # Enter new positions
            if len(portfolio['positions']) == 0:
                if signals.get('buy_call'):
                    self._enter_position(portfolio, current_price, current_time, 'BUY', symbol, strategy.get_strategy_name())
                elif signals.get('buy_put'):
                    self._enter_position(portfolio, current_price, current_time, 'SELL', symbol, strategy.get_strategy_name())
            
            # Track equity curve
            current_equity = portfolio['capital'] + self._calculate_unrealized_pnl(portfolio, current_price)
            portfolio['equity_curve'].append({
                'time': current_time,
                'equity': current_equity
            })
            
            # Track peak for drawdown
            if current_equity > peak_capital:
                peak_capital = current_equity
        
        return portfolio
    
    def _enter_position(self, portfolio: Dict, price: float, time, action: str, 
                        symbol: str, strategy_name: str):
        """Enter a new position"""
        
        atr_points = price * 0.02
        
        if action == 'BUY':
            stop_loss = price - (atr_points * 5)
            target = price + (atr_points * 5 * 3)
            position_type = 'LONG'
        else:
            stop_loss = price + (atr_points * 5)
            target = price - (atr_points * 5 * 3)
            position_type = 'SHORT'
        
        # Calculate position size
        risk_amount = portfolio['capital'] * 0.01
        position_size = max(1, int(risk_amount / (abs(price - stop_loss))))
        
        position = {
            'symbol': symbol,
            'position_type': position_type,
            'entry_price': price,
            'entry_time': time,
            'quantity': position_size,
            'stop_loss': stop_loss,
            'target': target,
            'strategy': strategy_name
        }
        
        portfolio['positions'].append(position)
        
        # Deduct margin
        margin = price * position_size * 0.2
        portfolio['capital'] -= margin
        
        print(f"   📈 ENTRY: {action} {position_size} {symbol} @ ₹{price:.2f}")
    
    def _close_position(self, portfolio: Dict, position: Dict, price: float, 
                        time, reason: str):
        """Close an existing position"""
        
        if position['position_type'] == 'LONG':
            pnl = (price - position['entry_price']) * position['quantity']
        else:
            pnl = (position['entry_price'] - price) * position['quantity']
        
        # Return margin + profit/loss
        margin = position['entry_price'] * position['quantity'] * 0.2
        portfolio['capital'] += margin + pnl
        
        trade = BacktestTrade(
            entry_time=str(position['entry_time']),
            exit_time=str(time),
            symbol=position['symbol'],
            action=position['position_type'],
            entry_price=position['entry_price'],
            exit_price=price,
            quantity=position['quantity'],
            pnl=pnl,
            pnl_percent=(pnl / (position['entry_price'] * position['quantity']) * 100) if position['entry_price'] > 0 else 0,
            strategy=position['strategy'],
            exit_reason=reason
        )
        
        portfolio['trades'].append(trade)
        portfolio['positions'].remove(position)
        
        print(f"   🔴 EXIT: {position['symbol']} @ ₹{price:.2f} | P&L: ₹{pnl:+,.2f} | Reason: {reason}")
    
    def _calculate_unrealized_pnl(self, portfolio: Dict, current_price: float) -> float:
        """Calculate unrealized P&L for open positions"""
        total_pnl = 0
        for pos in portfolio['positions']:
            if pos['position_type'] == 'LONG':
                pnl = (current_price - pos['entry_price']) * pos['quantity']
            else:
                pnl = (pos['entry_price'] - current_price) * pos['quantity']
            total_pnl += pnl
        return total_pnl
    
    def _calculate_metrics(self, portfolio: Dict) -> Dict:
        """Calculate performance metrics"""
        
        trades = portfolio['trades']
        equity_curve = [e['equity'] for e in portfolio['equity_curve']]
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        pnls = [t.pnl for t in trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        
        total_trades = len(trades)
        winning_count = len(winning_trades)
        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(pnls)
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Calculate drawdown
        peak = max(equity_curve) if equity_curve else portfolio['capital']
        trough = min(equity_curve) if equity_curve else portfolio['capital']
        max_drawdown = (peak - trough) / peak * 100 if peak > 0 else 0
        
        # Calculate returns
        if len(equity_curve) > 1:
            returns = np.diff(equity_curve) / equity_curve[:-1]
            if len(returns) > 1 and np.std(returns) > 0:
                sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        total_return = ((equity_curve[-1] - self.initial_capital) / self.initial_capital * 100) if equity_curve else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_count,
            'losing_trades': total_trades - winning_count,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_return': round(total_return, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'best_trade': round(max(pnls), 2) if pnls else 0,
            'worst_trade': round(min(pnls), 2) if pnls else 0,
            'final_equity': round(equity_curve[-1], 2) if equity_curve else self.initial_capital
        }