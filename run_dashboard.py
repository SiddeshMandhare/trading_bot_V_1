# run_dashboard.py
import os
import sys
import subprocess

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Bot folder path
bot_folder = r"e:\siddesh\Trading\Sublime\code\Test\option\trading_bot"

print("="*50)
print("  📈 Trading Bot Dashboard Launcher")
print("="*50)
print()

# Check if bot folder exists
if not os.path.exists(bot_folder):
    print(f"❌ ERROR: Bot folder not found!")
    print(f"   Path: {bot_folder}")
    print()
    input("Press Enter to exit...")
    sys.exit(1)

# Check if dashboard.py exists
dashboard_path = os.path.join(bot_folder, "dashboard_api.py") ###############################
if not os.path.exists(dashboard_path):
    print(f"❌ ERROR: dashboard.py not found in bot folder!")
    print(f"   Path: {dashboard_path}")
    print()
    input("Press Enter to exit...")
    sys.exit(1)

# Change to bot folder
os.chdir(bot_folder)
print(f"📁 Changed to: {os.getcwd()}")
print()

# Check if streamlit is installed
try:
    import streamlit
    print("✅ Streamlit found")
except ImportError:
    print("⚠️ Streamlit not found! Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "plotly", "pandas"])
    print()

# Get IP address
try:
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"🌐 Your PC IP: {ip_address}")
    print(f"📱 Access from phone: http://{ip_address}:8501")
except:
    print("📱 Access from phone using your PC's IP address on port 8501")

print()
print("🚀 Starting dashboard...")
print("Press Ctrl+C to stop")
print("="*50)
print()

# Run streamlit
subprocess.run(["streamlit", "run", "dashboard.py", "--server.address", "0.0.0.0"])