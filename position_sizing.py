# position_sizing.py
from typing import Dict, List
from config import Config

class KellyPositionSizer:
    def __init__(self):
        self.strategy_stats = {}
    
    def calculate_kelly_size(self, strategy_name: str, current_capital: float,
                           atr_points: float, current_price: float,
                           completed_orders: List[Dict]) -> int:
        wins = 0
        losses = 0
        total_profit = 0
        total_loss = 0
        
        for trade in completed_orders:
            if trade.get('strategy') == strategy_name:
                pnl = trade.get('pnl', 0)
                if pnl > 0:
                    wins += 1
                    total_profit += pnl
                elif pnl < 0:
                    losses += 1
                    total_loss += abs(pnl)
        
        total_trades = wins + losses
        
        if total_trades < Config.MIN_KELlY_TRADES:
            risk_amount = current_capital * Config.BASE_CAPITAL_RISK_PERCENT
            return int(risk_amount / atr_points) if atr_points > 0 else 1
        
        win_rate = wins / total_trades
        avg_win = total_profit / wins if wins > 0 else 1
        avg_loss = total_loss / losses if losses > 0 else 1
        
        b = avg_win / avg_loss if avg_loss > 0 else 1
        kelly_fraction = (win_rate * b - (1 - win_rate)) / b
        
        if Config.HALF_KELLY:
            kelly_fraction = kelly_fraction * 0.5
        
        kelly_fraction = max(0.01, min(0.03, kelly_fraction))
        risk_amount = current_capital * kelly_fraction
        position_size = int(risk_amount / atr_points) if atr_points > 0 else 1
        
        return max(1, position_size)