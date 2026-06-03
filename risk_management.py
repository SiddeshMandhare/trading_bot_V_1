# risk_management.py
import pandas as pd
import talib
import datetime
from typing import Dict, Optional
from collections import defaultdict
from config import Config

class SignalStrength:
    @staticmethod
    def calculate_signal_strength(chart: pd.DataFrame, symbol: str, direction: str = 'BUY') -> Dict[str, float]:
        scores = {'trend': 0, 'momentum': 0, 'volume': 0, 'volatility': 0, 'overall': 0}
        
        if len(chart) < 20:
            return scores
        
        cc = chart.iloc[-1]
        
        # Trend Score
        trend_score = 0
        if 'ema_9' in chart and 'ema_15' in chart:
            if direction == 'BUY':
                if cc['ema_9'] > cc['ema_15']:
                    trend_score += 10
            else:
                if cc['ema_9'] < cc['ema_15']:
                    trend_score += 10
        
        if 'adx' in chart and not pd.isna(cc['adx']):
            if cc['adx'] > 30:
                trend_score += 10
            elif cc['adx'] > 25:
                trend_score += 5
        scores['trend'] = min(30, trend_score)
        
        # Momentum Score
        momentum_score = 0
        if 'rsi' in chart and not pd.isna(cc['rsi']):
            if direction == 'BUY' and 50 < cc['rsi'] < 70:
                momentum_score += 15
            elif direction == 'SELL' and 30 < cc['rsi'] < 50:
                momentum_score += 15
        scores['momentum'] = min(30, momentum_score)
        
        # Volume Score
        volume_score = 0
        if 'volume_ma' in chart and not pd.isna(cc['volume_ma']) and cc['volume_ma'] > 0:
            vol_ratio = cc['volume'] / cc['volume_ma']
            if vol_ratio > 1.5:
                volume_score = 15
            elif vol_ratio > 1.2:
                volume_score = 10
        scores['volume'] = volume_score
        
        # Volatility Score
        volatility_score = 0
        if 'atr' in chart and not pd.isna(cc['atr']) and cc['close'] > 0:
            atr_ratio = cc['atr'] / cc['close']
            if 0.01 < atr_ratio < 0.03:
                volatility_score = 20
        scores['volatility'] = volatility_score
        
        scores['overall'] = scores['trend'] + scores['momentum'] + scores['volume'] + scores['volatility']
        return scores
    
    @staticmethod
    def should_trade(scores: Dict[str, float]) -> bool:
        return scores['overall'] >= Config.MIN_SIGNAL_STRENGTH
    
    @staticmethod
    def get_signal_grade(scores: Dict[str, float]) -> str:
        overall = scores['overall']
        if overall >= 80: return 'A+'
        elif overall >= 70: return 'A'
        elif overall >= 60: return 'B'
        elif overall >= 50: return 'C'
        elif overall >= 40: return 'D'
        else: return 'F'


class MarketRegime:
    @staticmethod
    def detect_regime(chart: pd.DataFrame) -> str:
        if len(chart) < 200:
            return 'ranging'
        
        chart_copy = chart.copy()
        chart_copy['sma_50'] = talib.SMA(chart_copy['close'], timeperiod=50)
        chart_copy['sma_200'] = talib.SMA(chart_copy['close'], timeperiod=200)
        
        cc = chart_copy.iloc[-1]
        if pd.isna(cc['sma_50']) or pd.isna(cc['sma_200']):
            return 'ranging'
        
        if cc['sma_50'] > cc['sma_200'] and cc['close'] > cc['sma_50']:
            return 'trending_up'
        elif cc['sma_50'] < cc['sma_200'] and cc['close'] < cc['sma_50']:
            return 'trending_down'
        else:
            return 'ranging'
    
    @staticmethod
    def get_bias(regime: str) -> str:
        biases = {'trending_up': 'LONG_ONLY', 'trending_down': 'SHORT_ONLY', 'ranging': 'BOTH', 'volatile': 'REDUCE_SIZE'}
        return biases.get(regime, 'BOTH')


class SignalCooldown:
    def __init__(self):
        self.last_signal_time = {}
        self.last_signal_price = {}
        self.signal_count = defaultdict(lambda: defaultdict(int))
    
    def can_take_signal(self, symbol: str, current_price: float, current_time: datetime.datetime) -> bool:
        if symbol in self.last_signal_time:
            minutes_since = (current_time - self.last_signal_time[symbol]).total_seconds() / 60
            if minutes_since < Config.SIGNAL_COOLDOWN_MINUTES:
                return False
        
        if symbol in self.last_signal_price and self.last_signal_price[symbol] > 0:
            price_change = abs(current_price - self.last_signal_price[symbol]) / self.last_signal_price[symbol]
            if price_change < 0.003:
                return False
        
        hour_key = current_time.strftime('%Y-%m-%d %H')
        if self.signal_count[symbol][hour_key] >= Config.MAX_SIGNALS_PER_HOUR:
            return False
        
        return True
    
    def record_signal(self, symbol: str, price: float, time: datetime.datetime):
        self.last_signal_time[symbol] = time
        self.last_signal_price[symbol] = price
        hour_key = time.strftime('%Y-%m-%d %H')
        self.signal_count[symbol][hour_key] += 1


class DynamicExitCalculator:
    @staticmethod
    def calculate_exit_levels(chart: pd.DataFrame, entry_price: float, position_type: str, atr_points: float) -> Dict[str, float]:
        levels = {}
        
        if position_type == 'LONG':
            levels['sl'] = entry_price - atr_points
            levels['target'] = entry_price + (atr_points * Config.RISK_REWARD_RATIO)
        else:
            levels['sl'] = entry_price + atr_points
            levels['target'] = entry_price - (atr_points * Config.RISK_REWARD_RATIO)
        
        return levels


class AdaptiveTrailingStop:
    def __init__(self):
        self.highest_price = {}
        self.lowest_price = {}
        self.breakeven_activated = {}
    
    def calculate_new_stop(self, symbol: str, position_type: str, current_price: float, 
                          entry_price: float, atr_points: float) -> Optional[float]:
        if symbol not in self.highest_price:
            self.highest_price[symbol] = entry_price
            self.lowest_price[symbol] = entry_price
            self.breakeven_activated[symbol] = False
        
        if position_type == 'LONG':
            if current_price > self.highest_price[symbol]:
                self.highest_price[symbol] = current_price
        else:
            if current_price < self.lowest_price[symbol]:
                self.lowest_price[symbol] = current_price
        
        if position_type == 'LONG':
            profit = current_price - entry_price
            profit_pct = profit / entry_price if entry_price > 0 else 0
        else:
            profit = entry_price - current_price
            profit_pct = profit / entry_price if entry_price > 0 else 0
        
        new_stop = None
        
        if not self.breakeven_activated[symbol] and profit >= atr_points:
            new_stop = entry_price
            self.breakeven_activated[symbol] = True
        elif position_type == 'LONG' and profit_pct >= 0.03:
            trail_percent = max(0.01, min(0.05, profit_pct * 0.3))  # Dynamic trail
            new_stop = current_price * (1 - trail_percent)
        elif position_type == 'SHORT' and profit_pct >= 0.03:
            new_stop = current_price * 1.02
        
        return new_stop
