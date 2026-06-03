# trade_journal.py - ADD THESE IMPORTS AT THE TOP
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class TradeJournalEntry:
    trade_id: int
    symbol: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    strategy: str
    entry_reason: str
    exit_reason: str
    emotional_state: str
    mistakes: str
    lessons: str
    screenshot_path: str
    tags: List[str]

class TradeJournal:
    def __init__(self, db_path: str = "trade_journal.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                symbol TEXT,
                entry_time DATETIME,
                exit_time DATETIME,
                entry_price REAL,
                exit_price REAL,
                quantity INTEGER,
                pnl REAL,
                strategy TEXT,
                entry_reason TEXT,
                exit_reason TEXT,
                emotional_state TEXT,
                mistakes TEXT,
                lessons TEXT,
                screenshot_path TEXT,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_entry(self, trade_data: Dict, trade_result: Dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tags_json = json.dumps(trade_result.get('tags', []))
        
        cursor.execute('''
            INSERT INTO trade_journal (
                trade_id, symbol, entry_time, exit_time, entry_price, exit_price,
                quantity, pnl, strategy, entry_reason, exit_reason,
                emotional_state, mistakes, lessons, screenshot_path, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('trade_id'),
            trade_data.get('symbol'),
            trade_data.get('entry_time'),
            trade_result.get('exit_time'),
            trade_data.get('entry_price'),
            trade_result.get('exit_price'),
            trade_data.get('quantity'),
            trade_result.get('pnl'),
            trade_data.get('strategy'),
            trade_result.get('entry_reason', 'Signal generated'),
            trade_result.get('exit_reason'),
            trade_result.get('emotional_state', 'Neutral'),
            trade_result.get('mistakes', ''),
            trade_result.get('lessons', ''),
            trade_result.get('screenshot_path', ''),
            tags_json
        ))
        
        conn.commit()
        journal_id = cursor.lastrowid
        conn.close()
        return journal_id
    
    def get_performance_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                MAX(pnl) as best_trade,
                MIN(pnl) as worst_trade
            FROM trade_journal
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            return {
                'total_trades': row[0],
                'winning_trades': row[1],
                'losing_trades': row[0] - row[1],
                'win_rate': (row[1] / row[0] * 100) if row[0] > 0 else 0,
                'total_pnl': row[2] or 0,
                'avg_pnl': row[3] or 0,
                'best_trade': row[4] or 0,
                'worst_trade': row[5] or 0
            }
        
        return {}
    
    def get_trades_by_emotion(self, emotion: str) -> List[Dict]:
        """Get trades filtered by emotional state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM trade_journal WHERE emotional_state = ?
            ORDER BY created_at DESC
        ''', (emotion,))
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def update_lesson(self, trade_id: int, lesson: str, mistakes: str = None):
        """Update lessons learned for a trade"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if mistakes:
            cursor.execute('''
                UPDATE trade_journal 
                SET lessons = ?, mistakes = ?
                WHERE trade_id = ?
            ''', (lesson, mistakes, trade_id))
        else:
            cursor.execute('''
                UPDATE trade_journal 
                SET lessons = ?
                WHERE trade_id = ?
            ''', (lesson, trade_id))
        
        conn.commit()
        conn.close()
