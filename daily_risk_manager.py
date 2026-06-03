# daily_risk_manager.py - Professional Daily Risk Management
import datetime
import json
import os
from typing import Dict, Tuple

class DailyRiskManager:
    """
    Professional Daily Risk Manager with Drawdown-based limits
    Tracks peak profit and prevents trading when drawdown exceeds limit
    """
    
    def __init__(self, max_daily_loss=2500, max_position_size=5, 
                 max_daily_trades=10, mode="DRAWDOWN"):
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.max_daily_trades = max_daily_trades
        self.mode = mode  # "ABSOLUTE" or "DRAWDOWN"
        
        # Daily tracking variables
        self.today = None
        self.daily_pnl = 0
        self.peak_pnl = 0
        self.trade_count = 0
        self.current_positions = 0
        self.is_blocked = False
        self.block_reason = None
        
        # Load previous state
        self._load_state()
    
    def _get_state_file(self) -> str:
        """Get path to state file"""
        return "daily_risk_state.json"
    
    def _load_state(self):
        """Load previous day's state"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if os.path.exists(self._get_state_file()):
            try:
                with open(self._get_state_file(), 'r') as f:
                    data = json.load(f)
                    if data.get('date') == today:
                        self.daily_pnl = data.get('daily_pnl', 0)
                        self.peak_pnl = data.get('peak_pnl', 0)
                        self.trade_count = data.get('trade_count', 0)
                        self.current_positions = data.get('current_positions', 0)
                        self.is_blocked = data.get('is_blocked', False)
                        self.block_reason = data.get('block_reason', None)
                        return
            except:
                pass
        
        # Reset for new day
        self._reset_day()
    
    def _save_state(self):
        """Save current state"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        data = {
            'date': today,
            'daily_pnl': self.daily_pnl,
            'peak_pnl': self.peak_pnl,
            'trade_count': self.trade_count,
            'current_positions': self.current_positions,
            'is_blocked': self.is_blocked,
            'block_reason': self.block_reason
        }
        with open(self._get_state_file(), 'w') as f:
            json.dump(data, f)
    
    def _reset_day(self):
        """Reset daily counters"""
        self.daily_pnl = 0
        self.peak_pnl = 0
        self.trade_count = 0
        self.current_positions = 0
        self.is_blocked = False
        self.block_reason = None
        self._save_state()
    
    def check_new_day(self):
        """Check if it's a new day and reset if needed"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if self.today != today:
            self.today = today
            self._reset_day()
            return True
        return False
    
    def update_pnl(self, pnl: float):
        """Update daily P&L and check drawdown limits"""
        self.check_new_day()
        
        # Update daily P&L
        self.daily_pnl += pnl
        
        # Update peak P&L (only for positive moves)
        if self.daily_pnl > self.peak_pnl:
            self.peak_pnl = self.daily_pnl
        
        # Check if limit is hit
        self._check_limits()
        
        self._save_state()
        return not self.is_blocked
    
    def before_trade(self, lot_size: int = 1) -> Tuple[bool, str]:
        """
        Check if a new trade is allowed
        Returns: (is_allowed, reason)
        """
        self.check_new_day()
        
        # Check if already blocked
        if self.is_blocked:
            return False, self.block_reason
        
        # Check position size limit
        if lot_size > self.max_position_size:
            return False, f"Lot size {lot_size} exceeds max {self.max_position_size}"
        
        # Check max positions
        if self.current_positions >= self.max_position_size:
            return False, f"Max positions {self.max_position_size} reached"
        
        # Check max trades
        if self.trade_count >= self.max_daily_trades:
            return False, f"Max daily trades {self.max_daily_trades} reached"
        
        # Check loss limits based on mode
        if self.mode == "ABSOLUTE":
            if self.daily_pnl <= -self.max_daily_loss:
                self.is_blocked = True
                self.block_reason = f"Daily loss limit reached: ₹{self.daily_pnl:,.2f} (Limit: -₹{self.max_daily_loss:,.2f})"
                return False, self.block_reason
        
        elif self.mode == "DRAWDOWN":
            # Calculate current drawdown from peak
            drawdown = self.peak_pnl - self.daily_pnl
            
            if drawdown >= self.max_daily_loss:
                self.is_blocked = True
                self.block_reason = f"Daily drawdown limit reached: ₹{drawdown:,.2f} drawdown from peak ₹{self.peak_pnl:,.2f} (Limit: ₹{self.max_daily_loss:,.2f})"
                return False, self.block_reason
        
        return True, "OK"
    
    def after_trade_entry(self, lot_size: int = 1):
        """Update after trade entry"""
        self.trade_count += 1
        self.current_positions += lot_size
        self._save_state()
    
    def after_trade_exit(self, lot_size: int = 1):
        """Update after trade exit"""
        self.current_positions = max(0, self.current_positions - lot_size)
        self._save_state()
    
    def _check_limits(self):
        """Check if any limit is breached"""
        if self.mode == "ABSOLUTE":
            if self.daily_pnl <= -self.max_daily_loss:
                self.is_blocked = True
                self.block_reason = f"Daily loss limit reached: ₹{self.daily_pnl:,.2f}"
        
        elif self.mode == "DRAWDOWN":
            drawdown = self.peak_pnl - self.daily_pnl
            if drawdown >= self.max_daily_loss and self.peak_pnl > 0:
                self.is_blocked = True
                self.block_reason = f"Daily drawdown limit reached: ₹{drawdown:,.2f} from peak ₹{self.peak_pnl:,.2f}"
    
    def get_status(self) -> Dict:
        """Get current risk status"""
        self.check_new_day()
        
        drawdown = self.peak_pnl - self.daily_pnl
        remaining_loss = self.max_daily_loss - drawdown if self.mode == "DRAWDOWN" else self.max_daily_loss + self.daily_pnl
        
        return {
            'date': self.today,
            'daily_pnl': round(self.daily_pnl, 2),
            'peak_pnl': round(self.peak_pnl, 2),
            'drawdown': round(drawdown, 2),
            'trade_count': self.trade_count,
            'current_positions': self.current_positions,
            'is_blocked': self.is_blocked,
            'block_reason': self.block_reason,
            'remaining_daily_limit': round(remaining_loss, 2),
            'remaining_trades': max(0, self.max_daily_trades - self.trade_count),
            'mode': self.mode,
            'max_daily_loss': self.max_daily_loss,
            'max_daily_trades': self.max_daily_trades,
            'max_position_size': self.max_position_size
        }
    
    def reset_manually(self):
        """Manually reset risk manager (for admin)"""
        self._reset_day()
        return True, "Risk manager reset successfully"


# Global instance
_daily_risk_manager = None

def get_daily_risk_manager():
    global _daily_risk_manager
    if _daily_risk_manager is None:
        from config import Config
        
        max_loss = getattr(Config, 'MAX_DAILY_LOSS', 2500)
        max_size = getattr(Config, 'MAX_POSITION_SIZE', 5)
        max_trades = getattr(Config, 'MAX_DAILY_TRADES', 10)
        mode = getattr(Config, 'MAX_DAILY_LOSS_MODE', 'DRAWDOWN')
        
        _daily_risk_manager = DailyRiskManager(max_loss, max_size, max_trades, mode)
    return _daily_risk_manager
