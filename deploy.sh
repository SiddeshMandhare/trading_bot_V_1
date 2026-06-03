#!/bin/bash

# ============================================
# 🤖 AlgoTrader Pro - Complete Deployment Script
# ============================================
# For AWS Lightsail Ubuntu 22.04 LTS
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Banner
echo ""
echo "========================================="
echo "🤖 AlgoTrader Pro - Cloud Deployment"
echo "========================================="
echo ""

# ============================================
# STEP 1: Update System
# ============================================
print_status "Step 1/9: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# ============================================
# STEP 2: Install Python and Dependencies
# ============================================
print_status "Step 2/9: Installing Python and build tools..."
sudo apt install -y python3-pip python3-dev python3-venv git screen build-essential curl wget
print_success "Python installed"

# ============================================
# STEP 3: Install TA-Lib (Technical Analysis Library)
# ============================================
print_status "Step 3/9: Installing TA-Lib..."
cd /tmp
wget -q https://github.com/ta-lib/ta-lib/releases/download/v0.6.0/ta-lib-0.6.0-src.tar.gz
tar -xzf ta-lib-0.6.0-src.tar.gz
cd ta-lib-0.6.0/
./configure --prefix=/usr
make
sudo make install
cd /
sudo ldconfig
pip3 install TA-Lib
print_success "TA-Lib installed"

# ============================================
# STEP 4: Install Python Packages
# ============================================
print_status "Step 4/9: Installing Python packages..."

# Upgrade pip
pip3 install --upgrade pip

# Install all required packages
pip3 install \
    Dhan-Tradehull>=3.3.0 \
    dhanhq>=2.0.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    requests>=2.31.0 \
    pytz>=2023.3 \
    plotly>=5.14.0 \
    streamlit>=1.28.0 \
    websocket-client>=1.5.0 \
    python-dotenv>=1.0.0 \
    python-telegram-bot>=20.0 \
    pyotp>=2.9.0 \
    mibian>=0.1.6

print_success "Python packages installed"

# ============================================
# STEP 5: Create Directory Structure
# ============================================
print_status "Step 5/9: Creating directory structure..."
mkdir -p ~/trading_bot
mkdir -p ~/trading_bot/strategies
mkdir -p ~/trading_bot/Dependencies
mkdir -p ~/trading_bot/logs
mkdir -p ~/trading_bot/backups
mkdir -p ~/trading_bot/NIFTY
print_success "Directories created"

# ============================================
# STEP 6: Create Configuration Files
# ============================================
print_status "Step 6/9: Creating configuration files..."

# Create empty token cache
cat > ~/trading_bot/token_cache.json << 'EOF'
{}
EOF

# Create requirements.txt
cat > ~/trading_bot/requirements.txt << 'EOF'
# AlgoTrader Pro - Complete Requirements
Dhan-Tradehull>=3.3.0
dhanhq>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
TA-Lib>=0.4.28
pytz>=2023.3
plotly>=5.14.0
streamlit>=1.28.0
websocket-client>=1.5.0
python-dotenv>=1.0.0
python-telegram-bot>=20.0
pyotp>=2.9.0
mibian>=0.1.6
EOF

# Create .env template
cat > ~/trading_bot/.env.template << 'EOF'
# Dhan API Credentials
DHAN_CLIENT_CODE=YOUR_CLIENT_CODE
DHAN_PIN=YOUR_PIN
DHAN_TOTP_SECRET=YOUR_TOTP_SECRET

# Telegram Alerts (Optional)
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID

# Trading Settings
BASE_CAPITAL=10000
MIN_SIGNAL_STRENGTH=10
RISK_PER_TRADE=0.5
MAX_ORDERS_PER_DAY=5
EOF

# Create logging configuration
cat > ~/trading_bot/logging_config.py << 'EOF'
import logging
import os

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'trading_bot.log')),
        logging.StreamHandler()
    ]
)

trading_logger = logging.getLogger('TradingBot')
EOF

print_success "Configuration files created"

# ============================================
# STEP 7: Create Helper Scripts
# ============================================
print_status "Step 7/9: Creating helper scripts..."

# Backup script
cat > ~/trading_bot/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/trading_bot/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -f /home/ubuntu/trading_bot/trading_bot.db ]; then
    cp /home/ubuntu/trading_bot/trading_bot.db $BACKUP_DIR/trading_bot_$TIMESTAMP.db
    echo "✅ Database backed up: trading_bot_$TIMESTAMP.db"
fi

if [ -f /home/ubuntu/trading_bot/token_cache.json ]; then
    cp /home/ubuntu/trading_bot/token_cache.json $BACKUP_DIR/token_cache_$TIMESTAMP.json
    echo "✅ Token cache backed up: token_cache_$TIMESTAMP.json"
fi

# Keep only last 30 backups
ls -t $BACKUP_DIR/trading_bot_*.db 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null
ls -t $BACKUP_DIR/token_cache_*.json 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null

echo "📦 Backup completed: $TIMESTAMP"
EOF
chmod +x ~/trading_bot/backup.sh

# Monitoring script
cat > ~/trading_bot/monitor.sh << 'EOF'
#!/bin/bash
echo ""
echo "========================================="
echo "📊 AlgoTrader Pro - System Monitor"
echo "========================================="
echo "Time: $(date)"
echo ""

# Check bot status
if systemctl is-active --quiet trading-bot; then
    echo "✅ Trading Bot: RUNNING"
else
    echo "❌ Trading Bot: STOPPED"
fi

# Check dashboard status
if systemctl is-active --quiet dashboard; then
    echo "✅ Dashboard: RUNNING"
else
    echo "❌ Dashboard: STOPPED"
fi

echo ""
echo "💾 Memory Usage:"
free -h

echo ""
echo "💿 Disk Space:"
df -h /home

echo ""
echo "📝 Last 5 Log Entries:"
tail -5 /home/ubuntu/trading_bot/logs/trading_bot.log 2>/dev/null || echo "No logs yet"

echo ""
echo "🌐 Dashboard URL: http://$(curl -s ifconfig.me):8080"
echo "========================================="
EOF
chmod +x ~/trading_bot/monitor.sh

# Quick commands script
cat > ~/trading_bot/quick_commands.sh << 'EOF'
#!/bin/bash
echo ""
echo "🤖 AlgoTrader Pro - Quick Commands"
echo "========================================="
echo "1. Start Bot:     sudo systemctl start trading-bot"
echo "2. Stop Bot:      sudo systemctl stop trading-bot"
echo "3. Restart Bot:   sudo systemctl restart trading-bot"
echo "4. Bot Status:    sudo systemctl status trading-bot"
echo "5. Dashboard Status: sudo systemctl status dashboard"
echo "6. View Logs:     tail -f /home/ubuntu/trading_bot/logs/trading_bot.log"
echo "7. Run Monitor:   /home/ubuntu/trading_bot/monitor.sh"
echo "8. Run Backup:    /home/ubuntu/trading_bot/backup.sh"
echo "9. Dashboard URL: http://$(curl -s ifconfig.me):8080"
echo "========================================="
EOF
chmod +x ~/trading_bot/quick_commands.sh

print_success "Helper scripts created"

# ============================================
# STEP 8: Create Systemd Services
# ============================================
print_status "Step 8/9: Creating systemd services..."

# Trading Bot Service
sudo cat > /etc/systemd/system/trading-bot.service << 'EOF'
[Unit]
Description=Trading Bot Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/trading_bot
ExecStart=/usr/bin/python3 /home/ubuntu/trading_bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/trading_bot/logs/trading_bot.log
StandardError=append:/home/ubuntu/trading_bot/logs/errors.log

[Install]
WantedBy=multi-user.target
EOF

# Dashboard Service
sudo cat > /etc/systemd/system/dashboard.service << 'EOF'
[Unit]
Description=Trading Dashboard Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/trading_bot
ExecStart=/usr/bin/python3 /home/ubuntu/trading_bot/dashboard_api.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/trading_bot/logs/dashboard.log
StandardError=append:/home/ubuntu/trading_bot/logs/errors.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
print_success "Systemd services created"

# ============================================
# STEP 9: Configure Firewall and Cron Jobs
# ============================================
print_status "Step 9/9: Configuring firewall and cron jobs..."

# Configure UFW firewall
sudo ufw --force disable
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 8080/tcp comment 'Trading Dashboard'
sudo ufw --force enable
print_success "Firewall configured (ports: 22, 8080)"

# Setup automatic backup cron job (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/trading_bot/backup.sh") | crontab -
print_success "Cron job configured for daily backups at 2 AM"

# ============================================
# Create Deployment Info File
# ============================================
cat > ~/trading_bot/DEPLOYMENT_INFO.txt << 'EOF'
===========================================
🤖 AlgoTrader Pro - Deployment Complete
===========================================

📁 Project Location: /home/ubuntu/trading_bot

📊 Services:
   - Trading Bot: trading-bot.service
   - Dashboard: dashboard.service

🌐 Dashboard URL: http://YOUR_INSTANCE_IP:8080

📋 Useful Commands:
   - Check all services: /home/ubuntu/trading_bot/quick_commands.sh
   - View monitor: /home/ubuntu/trading_bot/monitor.sh
   - View logs: tail -f /home/ubuntu/trading_bot/logs/trading_bot.log

📁 Important Files:
   - Configuration: /home/ubuntu/trading_bot/config.py
   - Token cache: /home/ubuntu/trading_bot/token_cache.json
   - Database: /home/ubuntu/trading_bot/trading_bot.db
   - Logs: /home/ubuntu/trading_bot/logs/

🔄 Backup: Daily at 2 AM (manual: /home/ubuntu/trading_bot/backup.sh)

===========================================
EOF

# ============================================
# COMPLETION
# ============================================
echo ""
echo "========================================="
print_success "DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "📋 Summary:"
echo "   ✅ System updated"
echo "   ✅ TA-Lib installed"
echo "   ✅ Python packages installed (including Dhan-Tradehull)"
echo "   ✅ Directories created"
echo "   ✅ Helper scripts created"
echo "   ✅ Services configured"
echo "   ✅ Firewall configured"
echo "   ✅ Cron jobs configured"
echo ""
echo "🌐 Dashboard will be available at: http://$(curl -s ifconfig.me):8080"
echo ""
print_warning "⚠️  IMPORTANT - Next Steps:"
echo ""
echo "1. UPLOAD YOUR CODE:"
echo "   scp -i your-key.pem -r * ubuntu@YOUR_IP:~/trading_bot/"
echo ""
echo "2. UPDATE CONFIGURATION:"
echo "   nano ~/trading_bot/config.py"
echo "   nano ~/trading_bot/token_cache.json"
echo ""
echo "3. COPY YOUR STRATEGIES:"
echo "   Make sure strategies/ folder is uploaded"
echo "   Make sure Dhan_Tradehull_V3.py is NOT needed (using PyPI version)"
echo ""
echo "4. START SERVICES:"
echo "   sudo systemctl start trading-bot"
echo "   sudo systemctl start dashboard"
echo ""
echo "5. VERIFY:"
echo "   /home/ubuntu/trading_bot/monitor.sh"
echo ""
echo "========================================="