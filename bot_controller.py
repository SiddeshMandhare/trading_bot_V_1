# bot_controller.py - Fixed for your project structure
import subprocess
import os
import signal
import time
import json
from pathlib import Path

class BotController:
    def __init__(self, bot_path=None):
        # Get the correct path - use current directory or specified path
        if bot_path is None:
            # Try to find main.py in current or parent directories
            possible_paths = [
                os.path.dirname(os.path.abspath(__file__)),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'),
                os.getcwd()
            ]
            for path in possible_paths:
                if os.path.exists(os.path.join(path, 'main.py')):
                    bot_path = path
                    break
            else:
                bot_path = os.path.dirname(os.path.abspath(__file__))
        
        self.bot_path = bot_path
        self.pid_file = os.path.join(self.bot_path, 'bot.pid')
        self.process = None
        self.running = False
        
        # Ensure logs directory exists
        logs_dir = os.path.join(self.bot_path, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
    def start_bot(self):
        """Start the trading bot as a background process"""
        try:
            # Check if already running
            if self.is_running():
                return {'success': False, 'message': 'Bot is already running'}
            
            # Path to main.py
            bot_script = os.path.join(self.bot_path, 'main.py')
            
            if not os.path.exists(bot_script):
                return {'success': False, 'message': f'Bot script not found: {bot_script}'}
            
            # Log file
            log_file = os.path.join(self.bot_path, 'logs', 'bot_output.log')
            
            # Start process
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Bot started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*60}\n")
                
                self.process = subprocess.Popen(
                    ['python3', bot_script],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=self.bot_path,
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.process.pid))
            
            self.running = True
            return {'success': True, 'message': f'Bot started with PID: {self.process.pid}'}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def stop_bot(self):
        """Stop the trading bot gracefully"""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Try graceful termination first
                try:
                    # Send SIGTERM
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)
                    
                    # Check if still running
                    if self.is_pid_running(pid):
                        # Force kill
                        os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Process already gone
                except Exception as e:
                    print(f"Error killing process: {e}")
                
                # Remove PID file
                try:
                    os.remove(self.pid_file)
                except:
                    pass
                
                self.running = False
                return {'success': True, 'message': 'Bot stopped'}
            
            return {'success': False, 'message': 'Bot not running'}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def is_running(self):
        """Check if bot is running"""
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                try:
                    pid = int(f.read().strip())
                    return self.is_pid_running(pid)
                except:
                    return False
        return False
    
    def is_pid_running(self, pid):
        """Check if a PID is running"""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def get_status(self):
        """Get detailed bot status"""
        running = self.is_running()
        status = {
            'running': running,
            'pid': None,
            'message': 'Bot is running' if running else 'Bot is stopped'
        }
        
        if running and os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                try:
                    status['pid'] = int(f.read().strip())
                except:
                    pass
        
        return status
    

    def get_bot_pid(self):
        """Get bot PID if running"""
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                try:
                    pid = int(f.read().strip())
                    if self.is_pid_running(pid):
                        return pid
                except:
                    pass
        return None

    def get_status(self):
        """Get detailed bot status"""
        running = self.is_running()
        pid = self.get_bot_pid()
        
        status = {
            'running': running,
            'pid': pid,
            'message': f'Bot is running (PID: {pid})' if running else 'Bot is stopped'
        }
        
        return status