# health_check.py - ADD THESE IMPORTS
import psutil
import threading
import time
import os
import sqlite3
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

@dataclass
class HealthStatus:
    is_healthy: bool
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    db_size_mb: float
    open_positions: int
    uptime_seconds: float
    last_trade_time: str
    api_status: str
    errors_last_hour: int

class HealthChecker:
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.start_time = time.time()
        self.error_count = defaultdict(int)
        self.error_window = []  # (timestamp, error)
        self._init_db()
    
    def _init_db(self):
        """Create health check database table"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    is_healthy BOOLEAN,
                    cpu_percent REAL,
                    memory_percent REAL,
                    open_positions INTEGER,
                    api_status TEXT,
                    errors_last_hour INTEGER
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Health check DB init error: {e}")
    
    def get_status(self) -> HealthStatus:
        """Get comprehensive health status"""
        
        # System metrics
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
        except Exception as e:
            print(f"System metrics error: {e}")
            cpu = memory = disk = 0
        
        # Database size
        db_size = 0
        try:
            if os.path.exists('trading_bot.db'):
                db_size = os.path.getsize('trading_bot.db') / (1024 * 1024)
        except:
            pass
        
        # API status - test Dhan connection
        api_status = "OK"
        try:
            if self.bot and hasattr(self.bot, 'tsl'):
                test = self.bot.tsl.get_ltp_data(names=["NIFTY"])
                if not test or test.get("NIFTY", 0) == 0:
                    api_status = "DEGRADED"
            else:
                api_status = "UNKNOWN"
        except Exception as e:
            api_status = f"FAILED: {str(e)[:50]}"
        
        # Count errors in last hour
        now = time.time()
        self.error_window = [(ts, e) for ts, e in self.error_window if now - ts < 3600]
        errors_last_hour = len(self.error_window)
        
        # Get open positions count
        open_positions = 0
        if self.bot and hasattr(self.bot, 'orderbook'):
            open_positions = len(self.bot.orderbook)
        
        # Determine health
        is_healthy = (
            cpu < 80 and
            memory < 85 and
            disk < 90 and
            api_status == "OK" and
            errors_last_hour < 50
        )
        
        # Last trade time
        last_trade = "Never"
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(entry_time) FROM trades")
            row = cursor.fetchone()
            if row and row[0]:
                last_trade = row[0]
            conn.close()
        except:
            pass
        
        # Log health check to database
        self._log_health_check(is_healthy, cpu, memory, open_positions, api_status, errors_last_hour)
        
        return HealthStatus(
            is_healthy=is_healthy,
            cpu_percent=round(cpu, 1),
            memory_percent=round(memory, 1),
            disk_usage=round(disk, 1),
            db_size_mb=round(db_size, 2),
            open_positions=open_positions,
            uptime_seconds=round(time.time() - self.start_time),
            last_trade_time=last_trade,
            api_status=api_status,
            errors_last_hour=errors_last_hour
        )
    
    def _log_health_check(self, is_healthy, cpu, memory, open_positions, api_status, errors):
        """Log health check to database"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO health_checks 
                (timestamp, is_healthy, cpu_percent, memory_percent, open_positions, api_status, errors_last_hour)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                is_healthy,
                cpu,
                memory,
                open_positions,
                api_status,
                errors
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Log health check error: {e}")
    
    def record_error(self, error: str):
        """Record an error for tracking"""
        self.error_window.append((time.time(), error))
        
        # Log error to database
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO errors (timestamp, error_message)
                VALUES (?, ?)
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), error[:500]))
            conn.commit()
            conn.close()
        except:
            pass
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent errors from database"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            
            # Check if errors table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='errors'")
            if not cursor.fetchone():
                conn.close()
                return []
            
            cursor.execute('''
                SELECT timestamp, error_message FROM errors 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{'timestamp': r[0], 'message': r[1]} for r in rows]
        except Exception as e:
            print(f"Get recent errors error: {e}")
            return []
    
    def get_health_history(self, hours: int = 24) -> List[Dict]:
        """Get health check history"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, is_healthy, cpu_percent, memory_percent, open_positions, api_status
                FROM health_checks 
                WHERE timestamp >= datetime('now', ?)
                ORDER BY timestamp DESC
            ''', (f'-{hours} hours',))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'timestamp': r[0],
                'is_healthy': bool(r[1]),
                'cpu_percent': r[2],
                'memory_percent': r[3],
                'open_positions': r[4],
                'api_status': r[5]
            } for r in rows]
        except Exception as e:
            print(f"Get health history error: {e}")
            return []
    
    def get_summary(self) -> Dict:
        """Get health summary as dictionary"""
        status = self.get_status()
        return {
            'is_healthy': status.is_healthy,
            'cpu': status.cpu_percent,
            'memory': status.memory_percent,
            'disk': status.disk_usage,
            'open_positions': status.open_positions,
            'uptime_hours': round(status.uptime_seconds / 3600, 1),
            'api_status': status.api_status,
            'db_size_mb': status.db_size_mb,
            'last_trade': status.last_trade_time,
            'errors_last_hour': status.errors_last_hour
        }
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start background monitoring thread"""
        def monitor():
            while True:
                try:
                    time.sleep(interval_seconds)
                    status = self.get_status()
                    
                    # Alert if unhealthy
                    if not status.is_healthy:
                        print(f"⚠️ HEALTH ALERT: CPU={status.cpu_percent}%, Memory={status.memory_percent}%, API={status.api_status}")
                        
                        # Could send Telegram alert here
                        if self.bot and hasattr(self.bot, 'telegram'):
                            alert_msg = f"⚠️ *Health Alert*\nCPU: {status.cpu_percent}%\nMemory: {status.memory_percent}%\nAPI: {status.api_status}"
                            self.bot.telegram.send_alert(alert_msg)
                    
                except Exception as e:
                    print(f"Monitor error: {e}")
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        print(f"✅ Health monitoring started (interval: {interval_seconds}s)")
