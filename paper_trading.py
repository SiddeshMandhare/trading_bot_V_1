# paper_trading.py
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from config import Config

@dataclass
class PaperPosition:
    symbol: str
    position_type: str  # LONG or SHORT
    entry_price: float
    quantity: int
    stop_loss: float
    target: float
    entry_time: str
    strategy: str
    pnl: float = 0.0
    status: str = 'open'

class PaperTradingManager:
    def __init__(self):
        self.initial_balance = getattr(Config, 'PAPER_BALANCE', 1000000)
        self.current_balance = self.initial_balance
        self.positions: Dict[str, PaperPosition] = {}
        self.trade_history: List[Dict] = []
        self._init_database()

        # Check if paper trading is enabled
        self.is_enabled = getattr(Config, 'PAPER_TRADING_ENABLED', True)
        
        if self.is_enabled:
            self._init_database()
        else:
            print("📝 Paper trading is DISABLED in config")

    
    def _init_database(self):
        """Initialize paper trading database"""
        conn = sqlite3.connect('paper_trading.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                position_type TEXT,
                entry_price REAL,
                exit_price REAL,
                quantity INTEGER,
                stop_loss REAL,
                target REAL,
                pnl REAL,
                strategy TEXT,
                status TEXT,
                entry_time DATETIME,
                exit_time DATETIME
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_balance (
                id INTEGER PRIMARY KEY,
                balance REAL,
                last_updated DATETIME
            )
        ''')
        # Initialize balance if not exists
        cursor.execute("SELECT * FROM paper_balance")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO paper_balance (id, balance, last_updated) VALUES (1, ?, ?)",
                          (self.initial_balance, datetime.now()))
        conn.commit()
        conn.close()


    def is_paper_trading_enabled(self) -> bool:
        """Check if paper trading is enabled"""
        return getattr(Config, 'PAPER_TRADING_ENABLED', True)


    
    def place_paper_order(self, symbol: str, action: str, quantity: int, 
                          entry_price: float, stop_loss: float, target: float,
                          strategy: str) -> Optional[PaperPosition]:
        """Place a paper trade - only if enabled"""

        # Check if paper trading is enabled
        if not self.is_paper_trading_enabled():
            print("❌ Paper trading is disabled. Enable in config to use paper trading.")
            return None
        
        # Check if we already have a position
        if symbol in self.positions:
            print(f"⚠️ Already have a paper position for {symbol}")
            return None
        
        position_type = "LONG" if action == "BUY" else "SHORT"
        
        # Calculate margin required
        margin = entry_price * quantity * 0.2  # 20% margin for paper trading
        if margin > self.current_balance:
            print(f"❌ Insufficient paper balance. Need ₹{margin:.2f}, Available: ₹{self.current_balance:.2f}")
            return None
        
        # Deduct margin
        self.current_balance -= margin
        
        position = PaperPosition(
            symbol=symbol,
            position_type=position_type,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            target=target,
            entry_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            strategy=strategy
        )
        
        self.positions[symbol] = position
        
        # Save to database
        self._save_trade(position)
        
        print(f"\n📝 PAPER TRADE EXECUTED:")
        print(f"   Symbol: {symbol}")
        print(f"   Action: {action}")
        print(f"   Quantity: {quantity}")
        print(f"   Entry: ₹{entry_price:.2f}")
        print(f"   Stop Loss: ₹{stop_loss:.2f}")
        print(f"   Target: ₹{target:.2f}")
        print(f"   Margin Used: ₹{margin:.2f}")
        print(f"   Remaining Balance: ₹{self.current_balance:.2f}")
        
        return position
    
    def close_paper_position(self, symbol: str, exit_price: float, reason: str) -> Optional[float]:
        """Close a paper position and calculate P&L"""
        
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        # Calculate P&L
        if position.position_type == "LONG":
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity
        
        # Return margin + profit/loss
        margin_used = position.entry_price * position.quantity * 0.2
        self.current_balance += margin_used + pnl
        
        # Update position
        position.pnl = pnl
        position.status = 'closed'
        
        # Update database
        self._update_trade_close(symbol, exit_price, pnl, reason)
        
        print(f"\n🔴 PAPER POSITION CLOSED:")
        print(f"   Symbol: {symbol}")
        print(f"   Exit Price: ₹{exit_price:.2f}")
        print(f"   P&L: ₹{pnl:+,.2f}")
        print(f"   Reason: {reason}")
        print(f"   New Balance: ₹{self.current_balance:.2f}")
        
        # Remove from active positions
        del self.positions[symbol]
        
        return pnl
    
    def get_account_summary(self) -> Dict:
        """Get paper trading account summary"""
        total_pnl = sum(t.get('pnl', 0) for t in self.trade_history)
        winning_trades = len([t for t in self.trade_history if t.get('pnl', 0) > 0])
        total_trades = len(self.trade_history)
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': round(self.current_balance, 2),
            'total_pnl': round(total_pnl, 2),
            'total_return': round((self.current_balance - self.initial_balance) / self.initial_balance * 100, 2),
            'active_positions': len(self.positions),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': round(winning_trades / total_trades * 100, 2) if total_trades > 0 else 0
        }
    
    def _save_trade(self, position: PaperPosition):
        """Save paper trade to database"""
        conn = sqlite3.connect('paper_trading.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO paper_trades 
            (symbol, position_type, entry_price, quantity, stop_loss, target, strategy, status, entry_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (position.symbol, position.position_type, position.entry_price, 
              position.quantity, position.stop_loss, position.target, 
              position.strategy, position.status, position.entry_time))
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add to history
        self.trade_history.append({
            'trade_id': trade_id,
            'symbol': position.symbol,
            'position_type': position.position_type,
            'entry_price': position.entry_price,
            'quantity': position.quantity,
            'pnl': 0,
            'strategy': position.strategy,
            'status': 'open',
            'entry_time': position.entry_time
        })
    
    def _update_trade_close(self, symbol: str, exit_price: float, pnl: float, reason: str):
        """Update trade with exit details"""
        conn = sqlite3.connect('paper_trading.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE paper_trades 
            SET exit_price=?, pnl=?, status='closed', exit_time=?, exit_reason=?
            WHERE symbol=? AND status='open'
        ''', (exit_price, pnl, datetime.now(), reason, symbol))
        conn.commit()
        conn.close()
        
        # Update history
        for trade in self.trade_history:
            if trade['symbol'] == symbol and trade['status'] == 'open':
                trade['exit_price'] = exit_price
                trade['pnl'] = pnl
                trade['status'] = 'closed'
                trade['exit_reason'] = reason
                break
    
    def get_positions(self) -> List[Dict]:
        """Get active paper positions"""
        return [asdict(pos) for pos in self.positions.values()]
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get paper trade history"""
        conn = sqlite3.connect('paper_trading.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT trade_id, symbol, position_type, entry_price, exit_price, 
                   quantity, pnl, strategy, status, entry_time, exit_time
            FROM paper_trades 
            ORDER BY trade_id DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'trade_id': r[0],
            'symbol': r[1],
            'type': r[2],
            'entry_price': r[3],
            'exit_price': r[4] or 0,
            'quantity': r[5],
            'pnl': r[6] or 0,
            'strategy': r[7],
            'status': r[8],
            'entry_time': r[9],
            'exit_time': r[10]
        } for r in rows]
