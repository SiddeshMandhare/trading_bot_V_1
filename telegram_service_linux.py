# telegram_service_linux.py - Fixed for Linux/Ubuntu
import threading
import requests
import json
from datetime import datetime, timedelta
from config import Config
import logging

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, bot_token: str, chat_id: str, bot_instance):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = bot_instance
        self.last_message_time = {}
        self.min_interval = 1  # Minimum 1 second between messages to avoid rate limits
        
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send Telegram message with rate limiting"""
        try:
            # Check rate limiting
            now = datetime.now()
            if self.chat_id in self.last_message_time:
                time_diff = (now - self.last_message_time[self.chat_id]).total_seconds()
                if time_diff < self.min_interval:
                    return False
            
            # Send message using requests (no python-telegram-bot dependency)
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            self.last_message_time[self.chat_id] = now
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent: {message[:50]}...")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False
    
    def send_alert(self, message: str) -> bool:
        """Send trade alert"""
        return self.send_message(message)
    
    def send_startup_message(self):
        """Send startup notification"""
        msg = """🤖 *Trading Bot Started*

📊 Bot is now running and monitoring the market.

Commands are available via the Dashboard UI.

*Time:* {}
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        self.send_message(msg)
    
    def start_command_handler(self):
        """Start command handler (simplified for Linux)"""
        print("📱 Telegram service ready (command handler disabled on Linux)")
        # For Linux, we'll use webhook or polling in a separate thread
        # This is simplified to avoid the python-telegram-bot issues
        pass