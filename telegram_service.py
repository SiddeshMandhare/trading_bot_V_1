


# telegram_service.py - Fully Working with Button Callbacks + Enhanced Watchlist Management
import threading
import requests
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import Config
Config.OPTION_TRADING_ENABLED
import sys
import os


class TelegramService:
    def __init__(self, bot_token: str, chat_id: str, bot_instance):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = bot_instance
        self.application = None
        


    async def paper_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get paper trading status"""
        # Check if paper trading is enabled and available
        if not hasattr(self.bot, 'execution') or not hasattr(self.bot.execution, 'paper_trading') or not self.bot.execution.paper_trading:
            await update.message.reply_text("❌ Paper trading is not enabled or not available")
            return
        
        try:
            summary = self.bot.execution.paper_trading.get_account_summary()
            positions = self.bot.execution.paper_trading.get_positions()
            
            message = f"📝 *PAPER TRADING STATUS*\n\n"
            message += f"💰 Balance: ₹{summary['current_balance']:,.2f}\n"
            message += f"📈 Total P&L: ₹{summary['total_pnl']:+,.2f} ({summary['total_return']}%)\n"
            message += f"🎯 Win Rate: {summary['win_rate']}%\n"
            message += f"📊 Total Trades: {summary['total_trades']}\n"
            message += f"🔓 Active Positions: {summary['active_positions']}\n\n"
            
            if positions:
                message += "*Active Positions:*\n"
                for pos in positions[:10]:  # Limit to 10 positions
                    message += f"• {pos['symbol']} ({pos['position_type']}) @ ₹{pos['entry_price']:.2f}\n"
            else:
                message += "No active positions"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting paper trading status: {str(e)}")


    
    async def paper_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset paper trading"""
        if not hasattr(self.bot, 'execution') or not hasattr(self.bot.execution, 'paper_trading') or not self.bot.execution.paper_trading:
            await update.message.reply_text("❌ Paper trading is not enabled")
            return
        
        try:
            from paper_trading import PaperTradingManager
            self.bot.execution.paper_trading = PaperTradingManager()
            await update.message.reply_text("✅ Paper trading reset successfully!\n\nNew balance: ₹100,000.00")
        except Exception as e:
            await update.message.reply_text(f"❌ Error resetting paper trading: {str(e)}")
    
    def setup_paper_handlers(self, dispatcher):
        """Setup paper trading command handlers"""
        dispatcher.add_handler(CommandHandler("paper", self.paper_status))
        dispatcher.add_handler(CommandHandler("paper_reset", self.paper_reset))
    
    
        
    def send_alert(self, message: str) -> bool:
        """Send Telegram message"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage?chat_id={self.chat_id}&text={message}"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send failed: {e}")
            return False
    
##    def send_startup_message(self):
##        """Send startup message to Telegram - Split into multiple messages to avoid truncation"""
##        
##        # Part 1: Welcome and Trading Mode Commands
##        msg1 = (
##            "🤖 *Trading Bot Started with Interactive Commands!*\n\n"
##            "📊 *Trading Mode Commands:*\n"
##            "• `/tradingmode` - View/Change trading mode (EQUITY_ONLY/FNO_ONLY/BOTH)\n"
##            "• `/watchlists` - View both Equity and F&O watchlists\n"
##            "• `/add_equity SYMBOL` - Add to equity watchlist\n"
##            "• `/add_fno SYMBOL` - Add to F&O watchlist\n"
##            "• `/remove_watchlist SYMBOL` - Remove from any watchlist\n"
##            "⚙️ *Trading Parameters:*\n"
##            "• `/tradingparams` - Open trading parameters menu\n"
##            "• `/set_timeframe` - Change chart timeframe (1/5/15/30/60 min, Daily)\n"
##            "• `/set_otm` - Change OTM count for options (0-5 OTM)\n"
##            "• `/modeselect` - Interactive mode selection buttons"
##        
##        )
##        
##        # Part 2: Basic Commands
##        msg2 = (
##            "📋 *Basic Commands:*\n"
##            "• `/status` - Bot status\n"
##            "• `/balance` - Account balance\n"
##            "• `/positions` - Open positions\n"
##            "• `/watchlist` - View active symbols\n"
##            "• `/add_symbol SYMBOL` - Add to watchlist\n"
##            "• `/remove_symbol SYMBOL` - Remove from watchlist\n"
##            "• `/config` - View settings\n"
##            "• `/close_all` - Close all positions\n"
##            "• `/help` - All commands"
##        )
##        
##        # Part 3: Market and Settings
##        msg3 = (
##            "📈 *Market Commands:*\n"
##            "• `/market` - Live market data\n"
##            "• `/signals` - Current signals\n"
##            "• `/performance` - Performance report\n"
##            "• `/risk` - Risk metrics\n\n"
##            "⚙️ *Settings:*\n"
##            "• `/alerts on/off` - Toggle alerts\n"
##            "• `/set_threshold VALUE` - Set signal threshold\n"
##            "• `/edit_config` - Interactive config editor"
##        )
##        
##        # Part 4: Option Trading and Performance
##        msg4 = (
##            "🎯 *Option Trading Commands:*\n"
##            "• `/option_status` - Option trading status\n"
##            "• `/option_on` - Enable option trading\n"
##            "• `/option_off` - Disable option trading\n\n"
##            "📊 *Performance Commands:*\n"
##            "• `/profit_factor` - Profit factor analysis\n"
##            "• `/drawdown` - Drawdown analysis\n"
##            "• `/today` - Today's performance\n"
##            "• `/best` - Best trade ever\n"
##            "• `/worst` - Worst trade ever\n\n"
##            "Bot is now running and accepting commands!"
##        )
##        
##        # Send all parts
##        self.send_alert(msg1)
##        self.send_alert(msg2)
##        self.send_alert(msg3)
##        self.send_alert(msg4)



    def send_startup_message(self):
        """Send startup message to Telegram - Split into 5 organized messages"""
        
        # Message 1: Welcome & Trading Mode
        msg1 = (
            "🤖 *Trading Bot Started with Interactive Commands!*\n\n"
            "📊 *Trading Mode:*\n"
            "• `/tradingmode` - Change mode (EQUITY_ONLY/FNO_ONLY/BOTH)\n"
            "• `/modeselect` - Interactive mode buttons\n"
            "• `/watchlists` - View both watchlists\n"
            "• `/add_equity SYMBOL` - Add to equity\n"
            "• `/add_fno SYMBOL` - Add to F&O\n"
            "• `/remove_watchlist SYMBOL` - Remove from any"
        )
        
        # Message 2: Trading Parameters & Basic Commands
        msg2 = (
            "⚙️ *Trading Parameters:*\n"
            "• `/tradingparams` - Parameters menu\n"
            "• `/set_timeframe` - Change timeframe (1-60min, DAY)\n"
            "• `/set_otm` - Change OTM count (0-5)\n"
            "• `/set_threshold VALUE` - Signal strength\n\n"
            "📋 *Basic Commands:*\n"
            "• `/status` - Bot status\n"
            "• `/balance` - Account balance\n"
            "• `/positions` - Open positions\n"
            "• `/watchlist` - Active symbols"
        )
        
        # Message 3: Management & Market Commands
        msg3 = (
            "🛠️ *Management:*\n"
            "• `/config` - View settings\n"
            "• `/edit_config` - Interactive config\n"
            "• `/add_symbol SYMBOL` - Add symbol\n"
            "• `/remove_symbol SYMBOL` - Remove symbol\n"
            "• `/close_all` - Close all\n"
            "• `/help` - All commands\n"
            "• `/menu` - Interactive menu\n\n"
            "📈 *Market:*\n"
            "• `/market` - Live market data\n"
            "• `/signals` - Current signals\n"
            "• `/performance` - Performance report\n"
            "• `/risk` - Risk metrics"
        )
        
        # Message 4: Option Trading & Alerts
        msg4 = (
            "🎯 *Option Trading:*\n"
            "• `/option_status` - Option status\n"
            "• `/option_on` - Enable options\n"
            "• `/option_off` - Disable options\n\n"
            "🔔 *Alerts:*\n"
            "• `/alerts on` - Enable alerts\n"
            "• `/alerts off` - Disable alerts"
        )
        
        # Message 5: Performance & Tips
        msg5 = (
            "📊 *Performance:*\n"
            "• `/profit_factor` - Profit factor\n"
            "• `/drawdown` - Drawdown analysis\n"
            "• `/today` - Today's P&L\n"
            "• `/best` - Best trade\n"
            "• `/worst` - Worst trade\n\n"
            "💡 *Quick Tips:*\n"
            "• Market: 9:15 AM - 3:30 PM (Mon-Fri)\n"
            "• OTM count 1-2 recommended for options\n"
            "• Send `/menu` for interactive buttons\n\n"
            "Bot is now running and accepting commands!"
        )
        
        # Send all parts with small delay
        import time
        
        self.send_alert(msg1)
        time.sleep(0.1)
        self.send_alert(msg2)
        time.sleep(0.1)
        self.send_alert(msg3)
        time.sleep(0.1)
        self.send_alert(msg4)
        time.sleep(0.1)
        self.send_alert(msg5)
        time.sleep(0.1)
        


##    def send_startup_message(self):
##        """Send startup message to Telegram - With numbered prefixes"""
##        
##        import time
##        
##        msg1 = (
##            "📌 [1/5] 🤖 *Trading Bot Started!*\n\n"
##            "📊 *TRADING MODE COMMANDS*\n"
##            "• /tradingmode - Change mode\n"
##            "• /modeselect - Interactive mode buttons\n"
##            "• /watchlists - View both watchlists\n"
##            "• /add_equity SYMBOL - Add to equity\n"
##            "• /add_fno SYMBOL - Add to F&O\n"
##            "• /remove_watchlist SYMBOL - Remove"
##        )
##        
##        msg2 = (
##            "📌 [2/5] ⚙️ *TRADING PARAMETERS*\n"
##            "• /tradingparams - Parameters menu\n"
##            "• /set_timeframe - Change timeframe\n"
##            "• /set_otm - Change OTM count\n"
##            "• /set_threshold VALUE - Signal strength\n\n"
##            "📋 *BASIC COMMANDS*\n"
##            "• /status - Bot status\n"
##            "• /balance - Account balance\n"
##            "• /positions - Open positions\n"
##            "• /watchlist - Active symbols"
##        )
##        
##        msg3 = (
##            "📌 [3/5] 🛠️ *MANAGEMENT COMMANDS*\n"
##            "• /config - View settings\n"
##            "• /edit_config - Interactive config\n"
##            "• /add_symbol SYMBOL - Add symbol\n"
##            "• /remove_symbol SYMBOL - Remove\n"
##            "• /close_all - Close all\n"
##            "• /help - All commands\n"
##            "• /menu - Interactive menu"
##        )
##        
##        msg4 = (
##            "📌 [4/5] 📈 *MARKET & OPTION COMMANDS*\n"
##            "• /market - Live market data\n"
##            "• /signals - Current signals\n"
##            "• /performance - Performance report\n"
##            "• /risk - Risk metrics\n\n"
##            "🎯 *OPTION TRADING*\n"
##            "• /option_status - Option status\n"
##            "• /option_on - Enable options\n"
##            "• /option_off - Disable options\n\n"
##            "🔔 *ALERTS*\n"
##            "• /alerts on - Enable\n"
##            "• /alerts off - Disable"
##        )
##        
##        msg5 = (
##            "📌 [5/5] 📊 *PERFORMANCE & TIPS*\n"
##            "• /profit_factor - Profit factor\n"
##            "• /drawdown - Drawdown analysis\n"
##            "• /today - Today's P&L\n"
##            "• /best - Best trade\n"
##            "• /worst - Worst trade\n\n"
##            "💡 *QUICK TIPS*\n"
##
##            "• Market: 9:15 AM - 3:30 PM (Mon-Fri)\n"
##            "• OTM count 1-2 recommended\n"
##            "• Send /menu for interactive buttons\n\n"
##            "✅ Bot is now running and accepting commands!"
##        )
##        
##        self.send_alert(msg1)
##        time.sleep(2)
##        self.send_alert(msg2)
##        time.sleep(2)
##        self.send_alert(msg3)
##        time.sleep(2)
##        self.send_alert(msg4)
##        time.sleep(2)
##        self.send_alert(msg5)
##        time.sleep(2)
##


    
    
    def start_command_handler(self):
        """Start Telegram bot in separate thread"""
        def run_bot():
            try:
                print("🤖 Starting Telegram bot...")
                self.application = Application.builder().token(self.bot_token).build()
                
                # Command handlers
                self.application.add_handler(CommandHandler("start", self.start_command))
                self.application.add_handler(CommandHandler("help", self.help_command))
                self.application.add_handler(CommandHandler("menu", self.menu_command))
                self.application.add_handler(CommandHandler("status", self.status_command))
                self.application.add_handler(CommandHandler("balance", self.balance_command))
                self.application.add_handler(CommandHandler("positions", self.positions_command))
                self.application.add_handler(CommandHandler("watchlist", self.watchlist_command))
                self.application.add_handler(CommandHandler("add_symbol", self.add_symbol_command))
                self.application.add_handler(CommandHandler("remove_symbol", self.remove_symbol_command))
                self.application.add_handler(CommandHandler("close_all", self.close_all_command))
                self.application.add_handler(CommandHandler("strategies", self.strategies_command))
                self.application.add_handler(CommandHandler("stats", self.stats_command))
                self.application.add_handler(CommandHandler("config", self.config_command))
                self.application.add_handler(CommandHandler("edit_config", self.edit_config_command))
                self.application.add_handler(CommandHandler("option_status", self.option_status_command))
                self.application.add_handler(CommandHandler("option_on", self.option_on_command))
                self.application.add_handler(CommandHandler("option_off", self.option_off_command))
                self.application.add_handler(CommandHandler("market", self.market_command))
                self.application.add_handler(CommandHandler("signals", self.signals_command))
                self.application.add_handler(CommandHandler("performance", self.performance_command))
                self.application.add_handler(CommandHandler("risk", self.risk_command))
                self.application.add_handler(CommandHandler("alerts", self.alerts_command))
                self.application.add_handler(CommandHandler("set_threshold", self.set_threshold_command))
                self.application.add_handler(CommandHandler("profit_factor", self.profit_factor_command))
                self.application.add_handler(CommandHandler("drawdown", self.drawdown_command))
                self.application.add_handler(CommandHandler("today", self.today_command))
                self.application.add_handler(CommandHandler("best", self.best_trade_command))
                self.application.add_handler(CommandHandler("worst", self.worst_trade_command))
                self.application.add_handler(CommandHandler("tradingmode", self.tradingmode_command))
                self.application.add_handler(CommandHandler("modeselect", self.modeselect_command))
                self.application.add_handler(CommandHandler("set_timeframe", self.set_timeframe_command))
                self.application.add_handler(CommandHandler("set_otm", self.set_otm_command))
                self.application.add_handler(CommandHandler("tradingparams", self.tradingparams_command))
                self.application.add_handler(CommandHandler("tradingparams", self.tradingparams_command))
                self.application.add_handler(CommandHandler("set_timeframe", self.set_timeframe_command))
                self.application.add_handler(CommandHandler("set_otm", self.set_otm_command))
                    
                # NEW COMMAND HANDLERS
                self.application.add_handler(CommandHandler("watchlists", self.watchlists_command))
                self.application.add_handler(CommandHandler("add_equity", self.add_equity_command))
                self.application.add_handler(CommandHandler("add_fno", self.add_fno_command))
                self.application.add_handler(CommandHandler("remove_watchlist", self.remove_watchlist_command))

                # ============ ADD PAPER TRADING COMMAND HANDLERS ============
                self.application.add_handler(CommandHandler("paper", self.paper_status))
                self.application.add_handler(CommandHandler("paper_reset", self.paper_reset))
                # ============================================================
                                
                self.application.add_handler(CallbackQueryHandler(self.button_callback))
                
                print("✅ Telegram bot started! Send /start to your bot on Telegram")
                self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            except Exception as e:
                print(f"❌ Telegram bot error: {e}")
                import traceback
                traceback.print_exc()
        
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        print("📱 Telegram command handler thread started")



    async def modeselect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trading mode selection buttons"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 EQUITY ONLY", callback_data="mode_equity"),
                InlineKeyboardButton("🎯 FNO ONLY", callback_data="mode_fno"),
            ],
            [
                InlineKeyboardButton("🔄 BOTH", callback_data="mode_both"),
                InlineKeyboardButton("❌ Cancel", callback_data="mode_cancel"),
            ],
            [
                InlineKeyboardButton("📋 Current Status", callback_data="mode_status"),
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get current mode
        from config import Config
        current_mode = Config.TRADING_MODE
        
        # Get active watchlist info
        if current_mode == "EQUITY_ONLY":
            watchlist = Config.EQUITY_WATCHLIST
            mode_icon = "📊"
        elif current_mode == "FNO_ONLY":
            watchlist = Config.FNO_WATCHLIST
            mode_icon = "🎯"
        else:
            watchlist = Config.get_active_watchlist()
            mode_icon = "🔄"
        
        watchlist_display = ', '.join(watchlist[:5])
        if len(watchlist) > 5:
            watchlist_display += f"... (+{len(watchlist)-5} more)"
        
        message = f"""{mode_icon} *Trading Mode Selection*

    Current Mode: `{current_mode}`

    *Active Symbols ({len(watchlist)}):*
    `{watchlist_display}`

    Select a new trading mode below:"""
        
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)




    async def _update_timeframe(self, update: Update, new_timeframe: str):
        """Update timeframe configuration"""
        from config import Config
        
        query = update.callback_query
        old_timeframe = Config.TIMEFRAME
        
        # Update config
        Config.TIMEFRAME = new_timeframe
        
        # Update bot if needed
        if hasattr(self.bot, 'update_timeframe'):
            self.bot.update_timeframe(new_timeframe)
        
        # Get display name
        timeframe_names = {
            "1": "1 Minute",
            "5": "5 Minutes",
            "15": "15 Minutes",
            "30": "30 Minutes",
            "60": "1 Hour",
            "DAY": "Daily"
        }
        display_name = timeframe_names.get(new_timeframe, new_timeframe)
        
        message = f"""✅ *Timeframe Updated!*

    Old: `{old_timeframe}` ({timeframe_names.get(old_timeframe, old_timeframe)})
    New: `{new_timeframe}` ({display_name})

    *What changed:*
    • Bot will now scan every {new_timeframe} minute(s)
    • Indicators will use {new_timeframe} minute candles
    • Trade frequency will {'increase' if int(new_timeframe) < int(old_timeframe) else 'decrease' if old_timeframe != 'DAY' else 'change'}

    ⚙️ The bot will use the new timeframe on next scan cycle."""
        
        # Show timeframe selection again
        keyboard = [[InlineKeyboardButton("🔄 Change Again", callback_data="set_timeframe"),
                     InlineKeyboardButton("🔙 Back to Params", callback_data="tradingparams")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        
        # Send alert
        self.send_alert(f"⏱️ Timeframe changed from {old_timeframe} to {new_timeframe} minutes")

    async def _update_otm(self, update: Update, new_otm: int):
        """Update OTM count configuration"""
        from config import Config
        
        query = update.callback_query
        old_otm = Config.OTM_COUNT
        
        # Update config
        Config.OTM_COUNT = new_otm
        
        # Also update option_config if exists
        try:
            from config import Config
            option_config.OPTION_OTM_COUNT = new_otm
        except:
            pass
        
        # OTM descriptions
        otm_descriptions = {
            0: "ATM - Trades at the money options",
            1: "1 OTM - One strike out of the money (Recommended)",
            2: "2 OTM - Two strikes out of the money",
            3: "3 OTM - Three strikes out of the money",
            4: "4 OTM - Four strikes out of the money",
            5: "5 OTM - Five strikes out of the money (Aggressive)"
        }
        
        message = f"""✅ *OTM Count Updated!*

    Old: `{old_otm}` OTM
    New: `{new_otm}` OTM

    *{otm_descriptions.get(new_otm, 'Custom setting')}*

    *Effect on trading:*
    • Premium cost will {'decrease' if new_otm > old_otm else 'increase'}
    • Probability of profit will {'decrease' if new_otm > old_otm else 'increase'}
    • Leverage will {'increase' if new_otm > old_otm else 'decrease'}

    ⚙️ Future option trades will use {new_otm} OTM strikes."""
        
        # Show OTM selection again
        keyboard = [[InlineKeyboardButton("🔄 Change Again", callback_data="set_otm"),
                     InlineKeyboardButton("🔙 Back to Params", callback_data="tradingparams")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        
        # Send alert
        self.send_alert(f"🎯 OTM count changed from {old_otm} to {new_otm}")

    async def _show_trading_params(self, update: Update):
        """Show current trading parameters"""
        from config import Config
        
        query = update.callback_query
        
        timeframe_names = {
            "1": "1 Minute",
            "5": "5 Minutes",
            "15": "15 Minutes",
            "30": "30 Minutes",
            "60": "1 Hour",
            "DAY": "Daily"
        }
        
        otm_descriptions = {
            0: "ATM - At The Money",
            1: "1 OTM - One strike out",
            2: "2 OTM - Two strikes out",
            3: "3 OTM - Three strikes out",
            4: "4 OTM - Four strikes out",
            5: "5 OTM - Five strikes out"
        }
        
        current_timeframe = Config.TIMEFRAME
        current_otm = Config.OTM_COUNT
        
        message = f"""📊 *Current Trading Parameters*

    ⏱️ *Timeframe:* `{current_timeframe}` ({timeframe_names.get(current_timeframe, current_timeframe)})
    🎯 *OTM Count:* `{current_otm}` ({otm_descriptions.get(current_otm, 'Custom')})

    *Other Settings:*
    • Signal Threshold: `{Config.MIN_SIGNAL_STRENGTH}`/100
    • Max Orders/Day: `{Config.MAX_ORDERS_PER_DAY}`
    • Risk/Reward: `1:{Config.RISK_REWARD_RATIO}`

    *Quick Actions:*
    • `/set_timeframe` - Change timeframe
    • `/set_otm` - Change OTM count
    • `/tradingparams` - Open parameters menu"""
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Parameters", callback_data="tradingparams")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)



    async def tradingparams_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trading parameters selection buttons"""
        
        from config import Config
        
        current_timeframe = Config.TIMEFRAME
        current_otm = Config.OTM_COUNT
        
        # Timeframe options with display names
        timeframe_options = {
            "1": "1 Minute",
            "5": "5 Minutes", 
            "15": "15 Minutes",
            "30": "30 Minutes",
            "60": "1 Hour",
            "DAY": "Daily"
        }
        
        # OTM options
        otm_options = [0, 1, 2, 3, 4, 5]
        
        # Build Timeframe keyboard
        timeframe_buttons = []
        row = []
        for tf, name in timeframe_options.items():
            is_current = " ✅" if tf == current_timeframe else ""
            row.append(InlineKeyboardButton(f"{name}{is_current}", callback_data=f"tf_{tf}"))
            if len(row) == 2:  # 2 buttons per row
                timeframe_buttons.append(row)
                row = []
        if row:
            timeframe_buttons.append(row)
        
        # Build OTM keyboard
        otm_buttons = []
        row = []
        for otm in otm_options:
            is_current = " ✅" if otm == current_otm else ""
            row.append(InlineKeyboardButton(f"{otm} OTM{is_current}", callback_data=f"otm_{otm}"))
            if len(row) == 3:  # 3 buttons per row
                otm_buttons.append(row)
                row = []
        if row:
            otm_buttons.append(row)
        
        # Main keyboard
        keyboard = [
            [InlineKeyboardButton("⏱️ TIMEFRAME", callback_data="show_timeframe")],
            [InlineKeyboardButton("🎯 OTM COUNT", callback_data="show_otm")],
            [InlineKeyboardButton("📊 Current Settings", callback_data="show_trading_params")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get timeframe display name
        tf_display = timeframe_options.get(current_timeframe, current_timeframe)
        
        message = f"""⚙️ *Trading Parameters*

    ⏱️ *Timeframe:* `{current_timeframe}` ({tf_display})
    🎯 *OTM Count:* `{current_otm}`

    *What these do:*
    • **Timeframe** - Chart interval for signals (1-60 min or Daily)
    • **OTM Count** - How far OTM options to trade (0=ATM, 1=1 OTM, etc.)

    Select an option below:"""
        
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def set_timeframe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show timeframe selection buttons"""
        
        from config import Config
        
        timeframe_options = {
            "1": "1 Minute",
            "5": "5 Minutes", 
            "15": "15 Minutes",
            "30": "30 Minutes",
            "60": "1 Hour",
            "DAY": "Daily"
        }
        
        current = Config.TIMEFRAME
        
        keyboard = []
        for tf, name in timeframe_options.items():
            is_current = " ✅ CURRENT" if tf == current else ""
            keyboard.append([InlineKeyboardButton(f"{name}{is_current}", callback_data=f"tf_{tf}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="tradingparams")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""⏱️ *Select Timeframe*

    Current: `{current}` ({timeframe_options.get(current, current)})

    *Timeframe affects:*
    • How often bot checks for signals
    • Sensitivity of indicators (EMA, RSI, MACD)
    • Trade frequency

    *Recommendations:*
    • `1-5 min` - Very active, many signals
    • `15 min` - Balanced (default)
    • `30-60 min` - Fewer but stronger signals
    • `Daily` - End of day trading

    Select new timeframe:"""
        
        await self._send_response(update, message, reply_markup=reply_markup)

    async def set_otm_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show OTM count selection buttons"""
        
        from config import Config
        
        current = Config.OTM_COUNT
        
        # OTM options with explanations
        otm_options = {
            0: "ATM (At The Money) - Lower risk, lower premium",
            1: "1 OTM - Moderate risk, balanced premium (Default)",
            2: "2 OTM - Higher risk, cheaper premium",
            3: "3 OTM - Aggressive, very cheap premium",
            4: "4 OTM - Very aggressive, high leverage",
            5: "5 OTM - Maximum leverage, highest risk"
        }
        
        keyboard = []
        for otm, desc in otm_options.items():
            is_current = " ✅" if otm == current else ""
            keyboard.append([InlineKeyboardButton(f"{otm} OTM{is_current}", callback_data=f"otm_{otm}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="tradingparams")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Find current description
        current_desc = otm_options.get(current, "Unknown")
        
        message = f"""🎯 *Select OTM Count*

    Current: `{current}` OTM
    *{current_desc}*

    *How OTM affects trades:*
    • Higher OTM = Cheaper premium but lower probability
    • Lower OTM = Higher premium but better probability
    • ATM (0 OTM) moves closest with underlying

    *Risk vs Reward:*
    • 0 OTM: Lower leverage, higher win rate
    • 1-2 OTM: Balanced (Recommended)
    • 3-5 OTM: High leverage, lower win rate

    Select new OTM count:"""
        
        await self._send_response(update, message, reply_markup=reply_markup)






    async def _change_trading_mode(self, update: Update, new_mode: str):
        """Change trading mode and update response"""
        from config import Config
        from config import Config
        
        query = update.callback_query
        old_mode = Config.TRADING_MODE
        
        # Update Config
        Config.TRADING_MODE = new_mode
        Config.WATCHLIST = Config.get_active_watchlist()
        
        # Update option_config
        if new_mode == "EQUITY_ONLY":
            Config.OPTION_TRADING_ENABLED = False
        else:
            Config.OPTION_TRADING_ENABLED = True
        
        # Update bot instance
        if hasattr(self.bot, 'option_active'):
            self.bot.option_active = Config.OPTION_TRADING_ENABLED
        
        if hasattr(self.bot, 'update_active_watchlist'):
            self.bot.update_active_watchlist()
        
        # Get new watchlist info
        if new_mode == "EQUITY_ONLY":
            watchlist = Config.EQUITY_WATCHLIST
            mode_icon = "📊"
            mode_name = "EQUITY ONLY"
        elif new_mode == "FNO_ONLY":
            watchlist = Config.FNO_WATCHLIST
            mode_icon = "🎯"
            mode_name = "FNO ONLY"
        else:
            watchlist = Config.get_active_watchlist()
            mode_icon = "🔄"
            mode_name = "BOTH"
        
        watchlist_display = ', '.join(watchlist[:5])
        if len(watchlist) > 5:
            watchlist_display += f"... (+{len(watchlist)-5} more)"
        
        message = f"""{mode_icon} *Trading Mode Changed!*

    Old Mode: `{old_mode}`
    New Mode: `{new_mode}`

    *Active Symbols ({len(watchlist)}):*
    `{watchlist_display}`

    ✅ Bot will now scan these symbols for trades."""
        
        # Create button to go back to mode selection
        keyboard = [[InlineKeyboardButton("🔄 Change Mode Again", callback_data="modeselect")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        
        # Send alert to chat
        self.send_alert(f"🔄 Trading mode changed from {old_mode} to {new_mode}")

    async def _show_mode_status(self, update: Update):
        """Show current mode status"""
        from config import Config
        
        query = update.callback_query
        current_mode = Config.TRADING_MODE
        
        if current_mode == "EQUITY_ONLY":
            watchlist = Config.EQUITY_WATCHLIST
            mode_icon = "📊"
            mode_desc = "Trading only equities/stocks"
        elif current_mode == "FNO_ONLY":
            watchlist = Config.FNO_WATCHLIST
            mode_icon = "🎯"
            mode_desc = "Trading only F&O options"
        else:
            watchlist = Config.get_active_watchlist()
            mode_icon = "🔄"
            mode_desc = "Trading both equities and options"
        
        watchlist_display = '\n'.join([f"• {s}" for s in watchlist[:10]])
        if len(watchlist) > 10:
            watchlist_display += f"\n• ... and {len(watchlist)-10} more"
        
        message = f"""{mode_icon} *Current Trading Mode Status*

    *Mode:* `{current_mode}`
    *Description:* {mode_desc}

    *Active Watchlist ({len(watchlist)} symbols):*
    {watchlist_display}

    *Option Trading:* {'🟢 ENABLED' if Config.OPTION_TRADING_ENABLED else '🔴 DISABLED'}
    *OTM Count:* {Config.OPTION_OTM_COUNT}
    *Max Lots:* {Config.OPTION_MAX_LOTS_PER_TRADE}

    Use `/modeselect` to change trading mode."""
        
        keyboard = [[InlineKeyboardButton("🔄 Change Mode", callback_data="modeselect")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)




        

    

    async def _send_response(self, update: Update, text: str, parse_mode=None, reply_markup=None):
        """Send response handling both direct messages and callbacks - with optional markdown"""
        if update.callback_query:
            try:
                if reply_markup:
                    await update.callback_query.edit_message_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
                else:
                    await update.callback_query.edit_message_text(text, parse_mode=parse_mode)
            except Exception as e:
                print(f"Could not edit message: {e}")
                if reply_markup:
                    await update.callback_query.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
                else:
                    await update.callback_query.message.reply_text(text, parse_mode=parse_mode)
        else:
            if reply_markup:
                await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, parse_mode=parse_mode)

    # ============ NEW WATCHLIST MANAGEMENT COMMANDS ============
    
    async def watchlists_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show both equity and F&O watchlists"""
        from config import Config
        
        msg = f"""📋 *Watchlist Configuration*

*📊 EQUITY WATCHLIST ({len(Config.EQUITY_WATCHLIST)} symbols):*
`{', '.join(Config.EQUITY_WATCHLIST)}`

*🎯 F&O WATCHLIST ({len(Config.FNO_WATCHLIST)} symbols):*
`{', '.join(Config.FNO_WATCHLIST)}`

*🔄 Current Active Watchlist ({Config.TRADING_MODE} mode):*
`{', '.join(Config.get_active_watchlist()[:10])}{'...' if len(Config.get_active_watchlist()) > 10 else ''}`

*Commands:*
• `/tradingmode` - Change trading mode
• `/add_equity SYMBOL` - Add to equity watchlist
• `/add_fno SYMBOL` - Add to F&O watchlist
• `/remove_watchlist SYMBOL` - Remove from watchlist"""
        
        await self._send_response(update, msg)

    async def add_equity_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add symbol to equity watchlist"""
        args = context.args
        if not args:
            await self._send_response(update, "❌ *Usage:* `/add_equity SYMBOL`\nExample: `/add_equity WIPRO`")
            return
        
        symbol = args[0].upper()
        from config import Config
        
        if symbol in Config.EQUITY_WATCHLIST:
            await self._send_response(update, f"⚠️ *{symbol}* is already in EQUITY watchlist!")
            return
        
        Config.EQUITY_WATCHLIST.append(symbol)
        
        # Update active watchlist if in EQUITY_ONLY or BOTH mode
        if Config.TRADING_MODE in ["EQUITY_ONLY", "BOTH"]:
            if hasattr(self.bot, 'update_active_watchlist'):
                self.bot.update_active_watchlist()
        
        # Also update Config.WATCHLIST for compatibility
        Config.WATCHLIST = Config.get_active_watchlist()
        
        msg = f"""✅ Added *{symbol}* to EQUITY watchlist!

*Updated Equity Watchlist ({len(Config.EQUITY_WATCHLIST)} symbols):*
{', '.join(Config.EQUITY_WATCHLIST[-5:])}

💡 Current mode: {Config.TRADING_MODE}
   Active watchlist will reflect this change."""
        
        await self._send_response(update, msg)

    async def add_fno_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add symbol to F&O watchlist"""
        args = context.args
        if not args:
            await self._send_response(update, "❌ *Usage:* `/add_fno SYMBOL`\nExample: `/add_fno MIDCPNIFTY`")
            return
        
        symbol = args[0].upper()
        from config import Config
        
        if symbol in Config.FNO_WATCHLIST:
            await self._send_response(update, f"⚠️ *{symbol}* is already in F&O watchlist!")
            return
        
        Config.FNO_WATCHLIST.append(symbol)
        
        # Also add to OPTION_SYMBOLS if it's an index
        if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'MIDCPNIFTY']:
            if symbol not in Config.OPTION_SYMBOLS:
                Config.OPTION_SYMBOLS.append(symbol)
        
        # Update active watchlist if in FNO_ONLY or BOTH mode
        if Config.TRADING_MODE in ["FNO_ONLY", "BOTH"]:
            if hasattr(self.bot, 'update_active_watchlist'):
                self.bot.update_active_watchlist()
        
        # Also update Config.WATCHLIST for compatibility
        Config.WATCHLIST = Config.get_active_watchlist()
        
        msg = f"""✅ Added *{symbol}* to F&O watchlist!

*Updated F&O Watchlist ({len(Config.FNO_WATCHLIST)} symbols):*
{', '.join(Config.FNO_WATCHLIST)}

💡 Current mode: {Config.TRADING_MODE}
   Active watchlist will reflect this change."""
        
        await self._send_response(update, msg)

    async def remove_watchlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove symbol from watchlist (checks both lists)"""
        args = context.args
        if not args:
            await self._send_response(update, "❌ *Usage:* `/remove_watchlist SYMBOL`\nExample: `/remove_watchlist ITC`")
            return
        
        symbol = args[0].upper()
        from config import Config
        
        removed_from = []
        
        if symbol in Config.EQUITY_WATCHLIST:
            Config.EQUITY_WATCHLIST.remove(symbol)
            removed_from.append("EQUITY")
        
        if symbol in Config.FNO_WATCHLIST:
            Config.FNO_WATCHLIST.remove(symbol)
            removed_from.append("F&O")
            # Also remove from OPTION_SYMBOLS
            if symbol in Config.OPTION_SYMBOLS:
                Config.OPTION_SYMBOLS.remove(symbol)
        
        if not removed_from:
            await self._send_response(update, f"⚠️ *{symbol}* not found in any watchlist!")
            return
        
        # Update active watchlist
        if hasattr(self.bot, 'update_active_watchlist'):
            self.bot.update_active_watchlist()
        
        # Also update Config.WATCHLIST for compatibility
        Config.WATCHLIST = Config.get_active_watchlist()
        
        msg = f"""✅ Removed *{symbol}* from {', '.join(removed_from)} watchlist!

*Updated Equity Watchlist:* {len(Config.EQUITY_WATCHLIST)} symbols
*Updated F&O Watchlist:* {len(Config.FNO_WATCHLIST)} symbols

💡 Current mode: {Config.TRADING_MODE}"""
        
        await self._send_response(update, msg)

    # ============ CONFIG EDITOR COMMAND ============
    
    async def edit_config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Interactive config editor"""
        from config import Config
        from config import Config
        
        keyboard = [
            [InlineKeyboardButton("📊 Trading Mode", callback_data="edit_trading_mode")],
            [InlineKeyboardButton("💰 Base Capital", callback_data="edit_base_capital")],
            [InlineKeyboardButton("⚠️ Risk per Trade %", callback_data="edit_risk_percent")],
            [InlineKeyboardButton("🎯 Signal Threshold", callback_data="edit_signal_threshold")],
            [InlineKeyboardButton("📊 Max Orders/Day", callback_data="edit_max_orders")],
            [InlineKeyboardButton("⚖️ Risk/Reward Ratio", callback_data="edit_rr_ratio")],
            [InlineKeyboardButton("🎯 Option OTM Count", callback_data="edit_otm_count")],
            [InlineKeyboardButton("📦 Option Max Lots", callback_data="edit_max_lots")],
            [InlineKeyboardButton("🛑 Option SL %", callback_data="edit_sl_percent")],
            [InlineKeyboardButton("🎯 Option Target %", callback_data="edit_target_percent")],
            [InlineKeyboardButton("📊 Timeframe", callback_data="edit_timeframe")],
            [InlineKeyboardButton("🔄 View Current Config", callback_data="view_config")],
            [InlineKeyboardButton("❌ Close", callback_data="close_editor")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = "⚙️ *Configuration Editor*\n\nSelect a setting to modify:"
        
        await self._send_response(update, msg, reply_markup=reply_markup)

    # ============ UPDATED TRADING MODE COMMAND ============

    async def tradingmode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show or change trading mode with watchlist info"""
        args = context.args
        
        # Dynamically import current config values
        from config import Config
        from config import Config
        
        if not args:
            current_mode = Config.TRADING_MODE
            
            # Get watchlist info based on current mode
            if current_mode == "EQUITY_ONLY":
                watchlist = Config.EQUITY_WATCHLIST
                watchlist_type = "📊 Equity Symbols"
                watchlist_icon = "📊"
            elif current_mode == "FNO_ONLY":
                watchlist = Config.FNO_WATCHLIST
                watchlist_type = "🎯 F&O Symbols"
                watchlist_icon = "🎯"
            else:  # BOTH
                watchlist = Config.get_active_watchlist()
                watchlist_type = "🔄 Equity + F&O Symbols"
                watchlist_icon = "🔄"
            
            # Format watchlist display
            if len(watchlist) > 10:
                watchlist_display = ', '.join(watchlist[:10]) + f"... (+{len(watchlist)-10} more)"
            else:
                watchlist_display = ', '.join(watchlist)
            
            msg = f"""{watchlist_icon} *Current Trading Mode:* `{current_mode}`

*Active Watchlist ({watchlist_type}):*
`{watchlist_display}`

*Available Modes:*
• `EQUITY_ONLY` - Trade only equities
  → Uses: {', '.join(Config.EQUITY_WATCHLIST[:3])}{'...' if len(Config.EQUITY_WATCHLIST) > 3 else ''}
  
• `FNO_ONLY` - Trade only F&O options  
  → Uses: {', '.join(Config.FNO_WATCHLIST)}
  
• `BOTH` - Trade both equities and options
  → Uses: Combined watchlist

*Usage:*
`/tradingmode EQUITY_ONLY`
`/tradingmode FNO_ONLY`
`/tradingmode BOTH`

*Current Option Settings:*
• OTM Count: {getattr(Config, 'OPTION_OTM_COUNT', 1)}
• Max Lots: {getattr(Config, 'OPTION_MAX_LOTS_PER_TRADE', 2)}
• Stop Loss: {getattr(Config, 'OPTION_SL_MULTIPLIER', 0.2)*100}%
• Target: {getattr(Config, 'OPTION_TARGET_MULTIPLIER', 2.5)*100}%

*Commands:*
• `/watchlists` - View both watchlists
• `/add_equity SYMBOL` - Add to equity watchlist
• `/add_fno SYMBOL` - Add to F&O watchlist"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        new_mode = args[0].upper()
        if new_mode in ['EQUITY_ONLY', 'FNO_ONLY', 'BOTH']:
            # Update Config dynamically
            Config.TRADING_MODE = new_mode
            
            # Update Config.WATCHLIST for compatibility
            Config.WATCHLIST = Config.get_active_watchlist()
            
            # Also update option_config
            if new_mode == 'EQUITY_ONLY':
                Config.OPTION_TRADING_ENABLED = False
                await update.message.reply_text("✅ Trading mode changed to EQUITY_ONLY\n🔴 Option trading DISABLED", parse_mode='Markdown')
            elif new_mode == 'FNO_ONLY':
                Config.OPTION_TRADING_ENABLED = True
                await update.message.reply_text("✅ Trading mode changed to FNO_ONLY\n🟢 Option trading ENABLED", parse_mode='Markdown')
            else:  # BOTH
                Config.OPTION_TRADING_ENABLED = True
                await update.message.reply_text("✅ Trading mode changed to BOTH\n🟢 Option trading ENABLED", parse_mode='Markdown')
            
            # Update the bot instance's option_active flag and watchlist
            if hasattr(self.bot, 'option_active'):
                self.bot.option_active = Config.OPTION_TRADING_ENABLED
            
            if hasattr(self.bot, 'update_active_watchlist'):
                self.bot.update_active_watchlist()
            
            # Send updated watchlist info
            active_watchlist = Config.get_active_watchlist()
            watchlist_display = ', '.join(active_watchlist[:5]) + ('...' if len(active_watchlist) > 5 else '')
            
            await update.message.reply_text(
                f"✅ Trading mode changed to {new_mode}\n\n📋 Active Symbols ({len(active_watchlist)}):\n`{watchlist_display}`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid mode. Use EQUITY_ONLY, FNO_ONLY, or BOTH", parse_mode='Markdown')

    # ============ UPDATED START COMMAND ============
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message with all commands"""
        welcome_msg = """🤖 *Trading Bot - Advanced Trading System*

    📊 *Features:*
    • Real-time market scanning
    • Multiple professional strategies
    • Risk management with Kelly sizing
    • Super orders with automatic SL/TP
    • Telegram command & control
    • **Interactive Config Editor**
    • **Separate watchlists for Equity & F&O**

    📋 *Commands:*

    *Basic:*
    `/status` - Bot status
    `/balance` - Account balance
    `/positions` - Open positions
    `/watchlist` - View active symbols
    `/watchlists` - View both watchlists
    `/market` - Live market data
    `/signals` - Current signals

    *Configuration:*
    `/config` - View current config
    `/edit_config` - **Interactive config editor**
    `/tradingmode` - Change trading mode
    `/modeselect` - **Mode selection buttons**
    `/set_threshold VALUE` - Set signal threshold
    `/add_equity SYMBOL` - Add to equity watchlist
    `/add_fno SYMBOL` - Add to F&O watchlist
    `/remove_watchlist SYMBOL` - Remove symbol

    *Performance:*
    `/performance` - Performance report
    `/profit_factor` - Profit factor
    `/drawdown` - Drawdown analysis
    `/today` - Today's P&L
    `/best` - Best trade
    `/worst` - Worst trade

    *Risk Management:*
    `/risk` - Risk metrics

    *Option Trading:*
    `/option_status` - Option status
    `/option_on` - Enable options
    `/option_off` - Disable options

    *Management:*
    `/add_symbol RELIANCE` - Add symbol
    `/remove_symbol ITC` - Remove symbol
    `/close_all` - Close all positions
    `/alerts on/off` - Toggle alerts
    `/help` - All commands

    💡 *Quick Start:* Send `/menu` for interactive buttons

    Bot is now running and accepting commands!"""
        
        # Create inline keyboard - FIX INDENTATION HERE
        keyboard = [
                    [InlineKeyboardButton("📊 Status", callback_data="status"),
                     InlineKeyboardButton("💰 Balance", callback_data="balance")],
                    [InlineKeyboardButton("📈 Positions", callback_data="positions"),
                     InlineKeyboardButton("📋 Watchlist", callback_data="watchlist")],
                    [InlineKeyboardButton("📊 Watchlists", callback_data="watchlists"),
                     InlineKeyboardButton("🎮 Mode Select", callback_data="modeselect")],
                    [InlineKeyboardButton("⚙️ Trading Params", callback_data="tradingparams"),
                     InlineKeyboardButton("🎯 Option Status", callback_data="option_status")],
                    [InlineKeyboardButton("📊 Market", callback_data="market"),
                     InlineKeyboardButton("📡 Signals", callback_data="signals")],
                    [InlineKeyboardButton("📈 Performance", callback_data="performance"),
                     InlineKeyboardButton("⚠️ Risk", callback_data="risk")],
                    [InlineKeyboardButton("⚙️ Config", callback_data="config"),
                     InlineKeyboardButton("🎯 Strategies", callback_data="strategies")],
                    [InlineKeyboardButton("✅ Option On", callback_data="option_on"),
                     InlineKeyboardButton("❌ Option Off", callback_data="option_off")],
                    [InlineKeyboardButton("📈 Profit Factor", callback_data="profit_factor"),
                     InlineKeyboardButton("📉 Drawdown", callback_data="drawdown")],
                    [InlineKeyboardButton("📅 Today", callback_data="today"),
                     InlineKeyboardButton("🏆 Best Trade", callback_data="best")],
                    [InlineKeyboardButton("💀 Worst Trade", callback_data="worst"),
                     InlineKeyboardButton("🛑 Close All", callback_data="close_all")],
                    [InlineKeyboardButton("📊 Stats", callback_data="stats"),
                     InlineKeyboardButton("❓ Help", callback_data="help")]
                ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)
    
    # ============ UPDATED MENU COMMAND ============
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show interactive menu"""
        keyboard = [
            [InlineKeyboardButton("📊 Status", callback_data="status"),
             InlineKeyboardButton("💰 Balance", callback_data="balance")],
            [InlineKeyboardButton("📈 Positions", callback_data="positions"),
             InlineKeyboardButton("📋 Watchlist", callback_data="watchlist")],
            [InlineKeyboardButton("📊 Watchlists", callback_data="watchlists"),
             InlineKeyboardButton("🔄 Trading Mode", callback_data="tradingmode")],
            [InlineKeyboardButton("⚙️ Edit Config", callback_data="edit_config"),
             InlineKeyboardButton("📊 Market", callback_data="market")],
            [InlineKeyboardButton("📡 Signals", callback_data="signals"),
             InlineKeyboardButton("📈 Performance", callback_data="performance")],
            [InlineKeyboardButton("⚠️ Risk", callback_data="risk"),
             InlineKeyboardButton("🎯 Option Status", callback_data="option_status")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats"),
             InlineKeyboardButton("🛑 Close All", callback_data="close_all")],
            [InlineKeyboardButton("🔔 Alerts", callback_data="alerts"),
             InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self._send_response(update, "📋 *Main Menu* - Select an option:", parse_mode='Markdown', reply_markup=reply_markup)
    
    # ============ UPDATED HELPER METHODS FOR BUTTON CALLBACK ============
    
    async def _handle_edit_callback(self, update: Update, setting: str):
        """Handle edit config button callbacks"""
        query = update.callback_query
        from config import Config
        
        settings_info = {
            "trading_mode": {"current": Config.TRADING_MODE, "type": "select", "options": ["EQUITY_ONLY", "FNO_ONLY", "BOTH"]},
            "base_capital": {"current": Config.BASE_CAPITAL, "type": "number", "range": (10000, 10000000)},
            "risk_percent": {"current": Config.BASE_CAPITAL_RISK_PERCENT * 100, "type": "number", "range": (0.1, 5.0)},
            "signal_threshold": {"current": Config.MIN_SIGNAL_STRENGTH, "type": "number", "range": (10, 100)},
            "max_orders": {"current": Config.MAX_ORDERS_PER_DAY, "type": "number", "range": (1, 50)},
            "rr_ratio": {"current": Config.RISK_REWARD_RATIO, "type": "number", "range": (1, 10)},
            "otm_count": {"current": Config.OPTION_OTM_COUNT, "type": "number", "range": (0, 5)},
            "max_lots": {"current": Config.OPTION_MAX_LOTS_PER_TRADE, "type": "number", "range": (1, 10)},
            "sl_percent": {"current": Config.OPTION_SL_MULTIPLIER * 100, "type": "number", "range": (5, 50)},
            "target_percent": {"current": Config.OPTION_TARGET_MULTIPLIER * 100, "type": "number", "range": (50, 500)},
            "timeframe": {"current": Config.TIMEFRAME, "type": "select", "options": ["1", "5", "15", "30", "60", "DAY"]}
        }
        
        info = settings_info.get(setting)
        if not info:
            await query.answer("Invalid setting")
            return
        
        if info["type"] == "select":
            keyboard = []
            for option in info["options"]:
                is_current = " ✅" if option == info["current"] else ""
                keyboard.append([InlineKeyboardButton(f"{option}{is_current}", callback_data=f"set_{setting}_{option}")])
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="edit_config")])
            keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_editor")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            msg = f"📊 *{setting.replace('_', ' ').title()}*\n\nCurrent: `{info['current']}`\n\nSelect new value:"
            await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            range_msg = f"Range: {info['range'][0]} - {info['range'][1]}"
            msg = f"📊 *{setting.replace('_', ' ').title()}*\n\nCurrent: `{info['current']}`\n{range_msg}\n\nPlease type the new value in chat:"
            await query.edit_message_text(msg, parse_mode='Markdown')

    # ============ REST OF THE EXISTING METHODS (keep all your original methods below) ============
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all available commands"""
        help_msg = """🤖 *Trading Bot - Complete Command Guide*

    *📊 Information Commands*
    • /status - Bot status and health
    • /balance - Account balance
    • /positions - List open positions
    • /watchlist - View current watchlist
    • /watchlists - View both equity and F&O watchlists
    • /strategies - Show active strategies
    • /stats - Trading statistics
    • /config - View bot configuration
    • /market - Live market data (NIFTY, BANKNIFTY)
    • /signals - Current signal strengths

    *⚙️ Trading Parameters*
    • /tradingparams - Open trading parameters menu
    • /set_timeframe - Change chart timeframe (1/5/15/30/60 min, Daily)
    • /set_otm - Change OTM count for options (0-5 OTM)

    *🎯 Trading Mode*
    • /tradingmode - Change trading mode (EQUITY_ONLY/FNO_ONLY/BOTH)
    • /modeselect - Interactive mode selection buttons

    *📊 Watchlist Management*
    • /add_equity SYMBOL - Add to equity watchlist
    • /add_fno SYMBOL - Add to F&O watchlist
    • /remove_watchlist SYMBOL - Remove from any watchlist
    • /add_symbol SYMBOL - Add to active watchlist
    • /remove_symbol SYMBOL - Remove from active watchlist

    *📈 Performance Commands*
    • /performance - Detailed performance report
    • /profit_factor - Profit factor analysis
    • /drawdown - Drawdown analysis
    • /today - Today's performance
    • /best - Best trade ever
    • /worst - Worst trade ever

    *⚠️ Risk Commands*
    • /risk - Risk metrics and position sizing
    • /set_threshold VALUE - Set signal threshold (10-100)

    *🔔 Alert Commands*
    • /alerts on - Enable trade alerts
    • /alerts off - Disable trade alerts

    *🛑 Management Commands*
    • /close_all - Close all open positions
    • /menu - Show interactive menu
    • /edit_config - Interactive config editor

    *🎯 Option Trading*
    • /option_status - Option trading status
    • /option_on - Enable option trading
    • /option_off - Disable option trading

    *📝 Examples*
    • /add_symbol RELIANCE - Add RELIANCE
    • /add_equity WIPRO - Add to equity watchlist
    • /add_fno MIDCPNIFTY - Add to F&O watchlist
    • /set_threshold 25 - Set threshold to 25
    • /set_timeframe 15 - Set chart to 15 minutes
    • /set_otm 2 - Set OTM count to 2
    • /alerts on - Enable alerts

    *💡 Quick Tips*
    • Market hours: 9:15 AM - 3:30 PM (Mon-Fri)
    • Bot scans watchlist every timeframe minutes
    • Signal threshold: Higher = fewer but stronger trades
    • OTM count: 1-2 is recommended for options
    • Use /menu for interactive buttons"""
        
        await self._send_response(update, help_msg)

    # ============ KEEP ALL YOUR EXISTING METHODS BELOW (option_status_command, option_on_command, option_off_command, status_command, balance_command, positions_command, watchlist_command, health_command, journal_command, journal_emotions_command, add_symbol_command, remove_symbol_command, config_command, close_all_command, strategies_command, stats_command, market_command, _send_fallback_market_data, signals_command, performance_command, risk_command, alerts_command, set_threshold_command, profit_factor_command, drawdown_command, today_command, best_trade_command, worst_trade_command, button_callback, calculate_streak, get_profit_factor_rating, get_drawdown_level) ============
    
    # ... (all your existing methods below this line remain exactly as they are)

    async def option_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show option trading status"""
        from config import Config
        status = "🟢 ACTIVE" if getattr(Config, 'OPTION_TRADING_ENABLED', False) else "🔴 INACTIVE"
        symbols = getattr(Config, 'OPTION_SYMBOLS', [])
        msg = f"""🎯 *Option Trading Status*
        
Status: {status}
Symbols: {', '.join(symbols) if symbols else 'None'}
OTM Count: {getattr(Config, 'OPTION_OTM_COUNT', 1)}
Max Lots: {getattr(Config, 'OPTION_MAX_LOTS_PER_TRADE', 5)}
Stop Loss: {getattr(Config, 'OPTION_SL_MULTIPLIER', 0.3)*100}%
Target: {getattr(Config, 'OPTION_TARGET_MULTIPLIER', 1.5)*100}%

*Commands:*
/option_on - Enable option trading
/option_off - Disable option trading"""
        
        await self._send_response(update, msg)
    
    async def option_on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable option trading"""
        from config import Config
        Config.OPTION_TRADING_ENABLED = True
        await self._send_response(update, "✅ *Option Trading ENABLED*")
    
    async def option_off_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable option trading"""
        from config import Config
        Config.OPTION_TRADING_ENABLED = False
        await self._send_response(update, "🔴 *Option Trading DISABLED*")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot status"""
        market_status = "🟢 OPEN" if self.bot.is_market_open() else "🔴 CLOSED"
        current_time = Config.get_current_time()
        
        msg = f"""🤖 *Bot Status*

🟢 *Status:* RUNNING
🕐 *Time:* {current_time.strftime('%H:%M:%S')}
📈 *Market:* {market_status}
📋 *Open Positions:* {len(self.bot.orderbook)}
💰 *Balance:* ₹{self.bot.get_available_capital():,.2f}
🎯 *Active Strategies:* {len(self.bot.strategies)}
📊 *Completed Trades:* {len(self.bot.completed_orders)}

⚙️ *Settings:*
• Signal Threshold: {Config.MIN_SIGNAL_STRENGTH}/100
• Super Orders: {'ON' if Config.USE_SUPER_ORDERS else 'OFF'}
• Kelly Sizing: {'ON' if Config.USE_Kelly_SIZING else 'OFF'}"""
        
        await self._send_response(update, msg)
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show account balance"""
        balance = self.bot.get_available_capital()
        
        risk_percent = Config.BASE_CAPITAL_RISK_PERCENT * 100
        max_capital_percent = Config.MAX_CAPITAL_PER_TRADE * 100
        
        msg = f"""💰 *Account Balance*

*Available:* ₹{balance:,.2f}

*Risk Settings:*
• Risk per Trade: {risk_percent:.2f}%
• Max Capital per Trade: {max_capital_percent:.1f}%
• Max Orders/Day: {Config.MAX_ORDERS_PER_DAY}

*Margin Info:*
• Multiplier: {Config.BROKER_MARGIN_MULTIPLIER}x
• Min Trade Value: ₹{Config.Minimum_trading_capital}"""
        
        await self._send_response(update, msg)
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show open positions"""
        if not self.bot.orderbook:
            await self._send_response(update, "📭 *No open positions*")
            return
        
        msg = "📈 *Open Positions*\n\n"
        for symbol, order in self.bot.orderbook.items():
            current_price = self.bot.data_service.get_current_price(symbol) or order.get('entry_price', 0)
            entry_price = order.get('entry_price', 0)
            qty = order.get('qty', 0)
            
            if order.get('position_type') == 'LONG':
                pnl = (current_price - entry_price) * qty
                pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            else:
                pnl = (entry_price - current_price) * qty
                pnl_percent = ((entry_price - current_price) / entry_price * 100) if entry_price > 0 else 0
            
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            
            msg += f"*{symbol}*\n"
            msg += f"  • Type: {order.get('position_type', 'LONG')}\n"
            msg += f"  • Qty: {qty}\n"
            msg += f"  • Entry: ₹{entry_price:.2f}\n"
            msg += f"  • Current: ₹{current_price:.2f}\n"
            msg += f"  • P&L: {pnl_emoji} ₹{pnl:+,.2f} ({pnl_percent:+.1f}%)\n"
            msg += f"  • SL: ₹{order.get('sl', 0):.2f}\n"
            msg += f"  • Target: ₹{order.get('target', 0):.2f}\n"
            msg += f"  • Strategy: {order.get('strategy', 'N/A')}\n\n"
        
        await self._send_response(update, msg)



    

    




    
    async def watchlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current active watchlist"""
        from config import Config
        active_watchlist = Config.get_active_watchlist()
        
        msg = "📋 Active Watchlist\n\n"
        for symbol in active_watchlist:
            price = self.bot.data_service.get_current_price(symbol)
            price_str = f"₹{price:.2f}" if price else "N/A"
            msg += f"• {symbol} - {price_str}\n"
        
        msg += f"\n📊 Total: {len(active_watchlist)} symbols\n"
        msg += f"🎯 Mode: {Config.TRADING_MODE}\n"
        msg += "\n➕ Add: /add_symbol SYMBOL\n"
        msg += "➖ Remove: /remove_symbol SYMBOL\n"
        msg += "📋 View both: /watchlists"
        
        # Send WITHOUT markdown parsing (parse_mode=None)
        await self._send_response(update, msg, parse_mode=None)

    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot health status"""
        status = self.bot.health_checker.get_status()
        
        health_emoji = "🟢" if status.is_healthy else "🔴"
        api_emoji = "🟢" if status.api_status == "OK" else ("🟡" if status.api_status == "DEGRADED" else "🔴")
        
        msg = f"""{health_emoji} *Bot Health Status*

*System:*
• CPU: {status.cpu_percent}%
• Memory: {status.memory_percent}%
• Disk: {status.disk_usage}%
• Uptime: {status.uptime_seconds/3600:.1f} hours

*Trading:*
• Open Positions: {status.open_positions}
• DB Size: {status.db_size_mb} MB
• Last Trade: {status.last_trade_time}

*API:*
• Dhan Status: {api_emoji} {status.api_status}
• Errors (1h): {status.errors_last_hour}

*Overall: {'✅ HEALTHY' if status.is_healthy else '⚠️ ISSUES DETECTED'}"""
        
        await self._send_response(update, msg)

    async def journal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trade journal statistics"""
        stats = self.bot.trade_journal.get_performance_stats()
        
        if not stats or stats.get('total_trades', 0) == 0:
            await self._send_response(update, "📔 *Trade Journal*\n\nNo trades recorded yet.")
            return
        
        msg = f"""📔 *Trade Journal Statistics*

*Performance:*
• Total Trades: {stats.get('total_trades', 0)}
• Win Rate: {stats.get('win_rate', 0):.1f}%
• Total P&L: ₹{stats.get('total_pnl', 0):+,.2f}
• Avg P&L: ₹{stats.get('avg_pnl', 0):+,.2f}

*Extremes:*
• Best Trade: ₹{stats.get('best_trade', 0):+,.2f}
• Worst Trade: ₹{stats.get('worst_trade', 0):+,.2f}

💡 Use `/journal_emotions` to see emotional state breakdown"""
        
        await self._send_response(update, msg)

    async def journal_emotions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trade breakdown by emotional state"""
        emotions = ['Confident', 'Satisfied', 'Cautious', 'Disappointed', 'Anxious', 'Frustrated']
        
        msg = "🎭 *Trades by Emotional State*\n\n"
        
        for emotion in emotions:
            trades = self.bot.trade_journal.get_trades_by_emotion(emotion)
            if trades:
                total_pnl = sum(t.get('pnl', 0) for t in trades)
                msg += f"• {emotion}: {len(trades)} trades | P&L: ₹{total_pnl:+,.2f}\n"
        
        await self._send_response(update, msg)

    async def add_symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add symbol to active watchlist"""
        args = context.args
        if not args:
            await self._send_response(update, "❌ *Usage:* `/add_symbol SYMBOL`\nExample: `/add_symbol RELIANCE`")
            return
        
        symbol = args[0].upper()
        from config import Config
        
        # Determine which watchlist to add to based on current mode
        if Config.TRADING_MODE == "EQUITY_ONLY":
            if symbol in Config.EQUITY_WATCHLIST:
                await self._send_response(update, f"⚠️ *{symbol}* is already in watchlist!")
                return
            Config.EQUITY_WATCHLIST.append(symbol)
        elif Config.TRADING_MODE == "FNO_ONLY":
            if symbol in Config.FNO_WATCHLIST:
                await self._send_response(update, f"⚠️ *{symbol}* is already in watchlist!")
                return
            Config.FNO_WATCHLIST.append(symbol)
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX'] and symbol not in Config.OPTION_SYMBOLS:
                Config.OPTION_SYMBOLS.append(symbol)
        else:  # BOTH mode - add to both? Or ask? For simplicity, add to equity
            if symbol in Config.EQUITY_WATCHLIST:
                await self._send_response(update, f"⚠️ *{symbol}* is already in watchlist!")
                return
            Config.EQUITY_WATCHLIST.append(symbol)
        
        # Update active watchlist
        Config.WATCHLIST = Config.get_active_watchlist()
        if hasattr(self.bot, 'update_active_watchlist'):
            self.bot.update_active_watchlist()
        
        price = self.bot.data_service.get_current_price(symbol)
        price_str = f" at ₹{price:.2f}" if price else ""
        
        watchlist_str = ', '.join(Config.WATCHLIST[:10])
        await self._send_response(update, f"✅ Added *{symbol}*{price_str} to watchlist!\n\n📋 Updated Watchlist ({len(Config.WATCHLIST)} symbols):\n{watchlist_str}{'...' if len(Config.WATCHLIST) > 10 else ''}")
    
    async def remove_symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove symbol from active watchlist"""
        args = context.args
        if not args:
            await self._send_response(update, "❌ *Usage:* `/remove_symbol SYMBOL`\nExample: `/remove_symbol ITC`")
            return
        
        symbol = args[0].upper()
        from config import Config
        
        removed = False
        if symbol in Config.EQUITY_WATCHLIST:
            Config.EQUITY_WATCHLIST.remove(symbol)
            removed = True
        if symbol in Config.FNO_WATCHLIST:
            Config.FNO_WATCHLIST.remove(symbol)
            if symbol in Config.OPTION_SYMBOLS:
                Config.OPTION_SYMBOLS.remove(symbol)
            removed = True
        
        if not removed:
            await self._send_response(update, f"⚠️ *{symbol}* is not in watchlist!")
            return
        
        # Update active watchlist
        Config.WATCHLIST = Config.get_active_watchlist()
        if hasattr(self.bot, 'update_active_watchlist'):
            self.bot.update_active_watchlist()
        
        watchlist_str = ', '.join(Config.WATCHLIST[:10])
        await self._send_response(update, f"✅ Removed *{symbol}* from watchlist!\n\n📋 Updated Watchlist ({len(Config.WATCHLIST)} symbols):\n{watchlist_str}{'...' if len(Config.WATCHLIST) > 10 else ''}")
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot configuration - FIXED to read current values"""
        # Read fresh config values
        from config import Config
        
        risk_percent = Config.BASE_CAPITAL_RISK_PERCENT * 100
        max_capital_percent = Config.MAX_CAPITAL_PER_TRADE * 100
        
        msg = f"""⚙️ *Bot Configuration*

*Risk Management*
• Base Capital: ₹{Config.BASE_CAPITAL:,.2f}
• Risk per Trade: {risk_percent:.2f}%
• Max Capital/Trade: {max_capital_percent:.1f}%
• Max Orders/Day: {Config.MAX_ORDERS_PER_DAY}
• Risk/Reward Ratio: {Config.RISK_REWARD_RATIO}:1

*Trading Parameters*
• Signal Threshold: {Config.MIN_SIGNAL_STRENGTH}/100
• Super Orders: {'✅' if Config.USE_SUPER_ORDERS else '❌'}
• Kelly Sizing: {'✅' if Config.USE_Kelly_SIZING else '❌'}
• Adaptive Trailing: {'✅' if Config.ENABLE_ADAPTIVE_TRAILING else '❌'}

*Market Hours*
• Open: 9:15 AM
• Close: 3:30 PM
• Days: Monday-Friday"""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def close_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Close all open positions"""
        await self._send_response(update, "🛑 *Closing all positions...*")
        self.bot.close_all_positions()
        await self._send_response(update, "✅ *All positions closed successfully!*")
    
    async def strategies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show active strategies"""
        strategies = "\n".join([f"• {s.get_strategy_name()}" for s in self.bot.strategies])
        msg = f"""🎯 *Active Strategies*

{strategies}

*Strategy Weights:*
• EMA_RSI: 2%
• MACD_Bollinger: 20%
• VWAP_Reversion: 20%
• MA_Crossover: 20%
• RSI_50_Crossover: 20%
• ORB_30min: 0%

💡 All strategies run in parallel and vote for signals"""
        
        await self._send_response(update, msg)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trading statistics"""
        total_pnl = sum(t.get('pnl', 0) for t in self.bot.completed_orders)
        winning = len([t for t in self.bot.completed_orders if t.get('pnl', 0) > 0])
        total = len(self.bot.completed_orders)
        win_rate = (winning / total * 100) if total > 0 else 0
        
        best_trade = 0
        worst_trade = 0
        if self.bot.completed_orders:
            best_trade = max(t.get('pnl', 0) for t in self.bot.completed_orders)
            worst_trade = min(t.get('pnl', 0) for t in self.bot.completed_orders)
        
        avg_pnl = total_pnl / total if total > 0 else 0
        
        msg = f"""📊 *Trading Statistics*

*Summary*
• Total Trades: {total}
• Winning Trades: {winning}
• Losing Trades: {total - winning}
• Win Rate: {win_rate:.1f}%
• Total P&L: ₹{total_pnl:+,.2f}

*Performance*
• Avg P&L: ₹{avg_pnl:+,.2f}
• Best Trade: ₹{best_trade:+,.2f}
• Worst Trade: ₹{worst_trade:+,.2f}"""
        
        await self._send_response(update, msg)
    
    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show live market data with REAL prices from Dhan API"""
        try:
            from auth_service import get_token_storage
            
            storage = get_token_storage(Config.CLIENT_CODE)
            token = storage.get_token()
            
            if not token:
                await self._send_response(update, "⚠️ Unable to fetch market data. Token not available.")
                return
            
            # Define all indices with their security IDs
            indices = {
                "NIFTY 50": {"security_id": "13", "exchange": "IDX_I"},
                "BANKNIFTY": {"security_id": "25", "exchange": "IDX_I"},
                "FINNIFTY": {"security_id": "27", "exchange": "IDX_I"},
                "SENSEX": {"security_id": "51", "exchange": "IDX_I"},
                "INDIA VIX": {"security_id": "105", "exchange": "IDX_I"}
            }
            
            url = "https://api.dhan.co/v2/marketfeed/ohlc"
            headers = {
                "access-token": token,
                "client-id": Config.CLIENT_CODE,
                "Content-Type": "application/json"
            }
            
            # Batch request for ALL indices in one API call
            payload = {"IDX_I": [13, 25, 27, 51, 105]}
            
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    idx_data = data.get("data", {}).get("IDX_I", {})
                    
                    name_map = {
                        "13": "NIFTY 50",
                        "25": "BANKNIFTY",
                        "27": "FINNIFTY",
                        "51": "SENSEX",
                        "105": "INDIA VIX"
                    }
                    
                    msg = "📊 *Live Market Data*\n\n"
                    
                    for sec_id, sec_data in idx_data.items():
                        name = name_map.get(sec_id, sec_id)
                        ltp = sec_data.get("last_price", 0)
                        prev_close = sec_data.get("ohlc", {}).get("close", ltp)
                        change = ltp - prev_close if prev_close else 0
                        change_percent = (change / prev_close * 100) if prev_close else 0
                        
                        # Determine emoji based on change
                        if change > 0:
                            emoji = "🟢"
                            arrow = "▲"
                        elif change < 0:
                            emoji = "🔴"
                            arrow = "▼"
                        else:
                            emoji = "⚪"
                            arrow = "●"
                        
                        msg += f"{emoji} *{name}*\n"
                        msg += f"   • LTP: ₹{ltp:,.2f}\n"
                        msg += f"   • Change: {arrow} {abs(change):+.2f} ({change_percent:+.2f}%)\n\n"
                    
                    await self._send_response(update, msg)
                    return
                    
                else:
                    print(f"Market API error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Market API exception: {e}")
            
            # Fallback to sample data if API fails
            await self._send_fallback_market_data(update)
            
        except Exception as e:
            print(f"Market command error: {e}")
            await self._send_fallback_market_data(update)

    async def _send_fallback_market_data(self, update: Update):
        """Send fallback market data when API fails"""
        msg = (
            "📊 *Market Data (Sample - API Unavailable)*\n\n"
            "🟢 *NIFTY 50*\n"
            "   • LTP: ₹23,654.70\n"
            "   • Change: ▼ -4.30 (-0.02%)\n\n"
            "🟢 *BANKNIFTY*\n"
            "   • LTP: ₹53,439.40\n"
            "   • Change: ▼ -122.80 (-0.23%)\n\n"
            "🟢 *FINNIFTY*\n"
            "   • LTP: ₹25,814.00\n"
            "   • Change: ▲ +150.00 (+0.58%)\n\n"
            "🟢 *SENSEX*\n"
            "   • LTP: ₹75,183.36\n"
            "   • Change: ▼ -135.03 (-0.18%)\n\n"
            "🟡 *INDIA VIX*\n"
            "   • LTP: ₹17.82\n"
            "   • Change: ▼ -0.62 (-3.36%)\n\n"
            "⚠️ *Note:* Sample data shown. Real-time data will appear during market hours when API is available."
        )
        await self._send_response(update, msg)
        
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current signals for watchlist"""
        try:
            from risk_management import SignalStrength
            from config import Config
            
            active_watchlist = Config.get_active_watchlist()
            msg = "📡 *Current Signals*\n\n"
            
            for symbol in active_watchlist:
                chart = self.bot.data_service.get_symbol_data(symbol)
                if chart is not None:
                    buy_score = SignalStrength.calculate_signal_strength(chart, symbol, 'BUY')
                    sell_score = SignalStrength.calculate_signal_strength(chart, symbol, 'SELL')
                    
                    current_price = chart['close'].iloc[-1]
                    
                    msg += f"*{symbol}* - ₹{current_price:.2f}\n"
                    msg += f"   • Buy Signal: {buy_score['overall']}/100 ({SignalStrength.get_signal_grade(buy_score)})\n"
                    msg += f"   • Sell Signal: {sell_score['overall']}/100 ({SignalStrength.get_signal_grade(sell_score)})\n"
                    msg += f"   • Required: {Config.MIN_SIGNAL_STRENGTH}/100\n\n"
                else:
                    msg += f"*{symbol}* - No data available\n\n"
            
            msg += f"💡 *Tip:* Use `/set_threshold {Config.MIN_SIGNAL_STRENGTH}` to adjust signal strength requirement"
            
            await self._send_response(update, msg)
        except Exception as e:
            await self._send_response(update, f"❌ Error fetching signals: {str(e)}")
    
    async def performance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed performance report"""
        total_pnl = sum(t.get('pnl', 0) for t in self.bot.completed_orders)
        winning = len([t for t in self.bot.completed_orders if t.get('pnl', 0) > 0])
        total = len(self.bot.completed_orders)
        
        if total == 0:
            await self._send_response(update, "📊 *No trades yet.* Bot is waiting for signals.")
            return
        
        win_rate = (winning / total * 100)
        avg_pnl = total_pnl / total
        
        # Calculate Sharpe ratio
        if len(self.bot.completed_orders) > 1:
            returns = [t.get('pnl', 0) for t in self.bot.completed_orders]
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            sharpe = (mean_return / (variance ** 0.5) * (252 ** 0.5)) if variance > 0 else 0
        else:
            sharpe = 0
        
        msg = f"""📊 *Performance Report*

*Summary*
• Total Trades: {total}
• Winning Trades: {winning}
• Losing Trades: {total - winning}
• Win Rate: {win_rate:.1f}%
• Total P&L: ₹{total_pnl:+,.2f}
• Avg P&L per Trade: ₹{avg_pnl:+,.2f}

*Risk Metrics*
• Sharpe Ratio: {sharpe:.2f}
• Profit Factor: {abs(total_pnl / (total_pnl - winning * avg_pnl)) if winning > 0 else 0:.2f}

*Strategy Distribution*
"""
        
        # Strategy breakdown
        strategy_pnl = {}
        for trade in self.bot.completed_orders:
            strategy = trade.get('strategy', 'Unknown')
            strategy_pnl[strategy] = strategy_pnl.get(strategy, 0) + trade.get('pnl', 0)
        
        for strategy, pnl in sorted(strategy_pnl.items(), key=lambda x: x[1], reverse=True):
            emoji = "📈" if pnl >= 0 else "📉"
            msg += f"• {emoji} {strategy}: ₹{pnl:+,.2f}\n"
        
        await self._send_response(update, msg)
    

    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show risk metrics including daily drawdown limits"""
        
        # Get risk manager status from bot
        if hasattr(self.bot, 'risk_manager') and self.bot.risk_manager:
            status = self.bot.risk_manager.get_status()
            
            msg = f"""⚠️ *DAILY RISK STATUS*

    📅 *Date:* {status['date']}
    📈 *Daily P&L:* ₹{status['daily_pnl']:,.2f}
    🏔️ *Peak P&L:* ₹{status['peak_pnl']:,.2f}
    📉 *Drawdown:* ₹{status['drawdown']:,.2f}
    🛡️ *Remaining Limit:* ₹{status['remaining_daily_limit']:,.2f}

    📊 *Trades Today:* {status['trade_count']}
    📌 *Open Positions:* {status['current_positions']}

    🎯 *Limits:*
    • Max Daily Loss/Drawdown: ₹{status['max_daily_loss']:,.2f}
    • Max Position Size: {status['max_position_size']} lots
    • Max Daily Trades: {status['max_daily_trades']}
    • Mode: {status['mode']}

    {status['block_reason'] if status['is_blocked'] else '🟢 TRADING ACTIVE'}
    """
            
            await self._send_response(update, msg)
        else:
            # Fallback to regular risk metrics
            capital = self.bot.get_available_capital()
            risk_amount = capital * Config.BASE_CAPITAL_RISK_PERCENT
            
            msg = f"""⚠️ *Risk Management Dashboard*

    *Current Position*
    • Available Capital: ₹{capital:,.2f}
    • Risk per Trade: ₹{risk_amount:,.2f} ({Config.BASE_CAPITAL_RISK_PERCENT*100}%)
    • Max Capital/Trade: ₹{capital * Config.MAX_CAPITAL_PER_TRADE:,.2f}

    *Risk Limits*
    • Max Orders/Day: {Config.MAX_ORDERS_PER_DAY}
    • Risk/Reward Ratio: {Config.RISK_REWARD_RATIO}:1
    • Signal Threshold: {Config.MIN_SIGNAL_STRENGTH}/100

    💡 *Daily Risk Limits (New)*
    • Max Daily Loss/Drawdown: ₹{getattr(Config, 'MAX_DAILY_LOSS', 2500):,.2f}
    • Max Position Size: {getattr(Config, 'MAX_POSITION_SIZE', 5)} lots
    • Max Daily Trades: {getattr(Config, 'MAX_DAILY_TRADES', 10)}

    Use `/tradingparams` to adjust limits"""
            
            await self._send_response(update, msg)

    
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle or show alerts status"""
        args = context.args
        
        if not args:
            status = "ON" if getattr(self.bot, 'alerts_enabled', True) else "OFF"
            await self._send_response(update, f"🔔 *Alerts are {status}*\n\nUse `/alerts on` or `/alerts off` to change.")
        elif args[0].lower() == 'on':
            self.bot.alerts_enabled = True
            await self._send_response(update, "🔔 *Alerts ENABLED* - You will receive trade notifications.")
        elif args[0].lower() == 'off':
            self.bot.alerts_enabled = False
            await self._send_response(update, "🔕 *Alerts DISABLED* - You will not receive trade notifications.")
        else:
            await self._send_response(update, "❌ Usage: `/alerts on` or `/alerts off`")
    
    async def set_threshold_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set signal strength threshold"""
        args = context.args
        if not args:
            await self._send_response(update, f"📊 *Current Signal Threshold:* {Config.MIN_SIGNAL_STRENGTH}/100\n\nUsage: `/set_threshold VALUE` (10-100)")
            return
        
        try:
            new_threshold = int(args[0])
            if 10 <= new_threshold <= 100:
                Config.MIN_SIGNAL_STRENGTH = new_threshold
                await self._send_response(update, f"✅ *Signal threshold updated to {new_threshold}/100*\n\nHigher = fewer but stronger signals")
            else:
                await self._send_response(update, "❌ Threshold must be between 10 and 100")
        except ValueError:
            await self._send_response(update, "❌ Please provide a number: `/set_threshold 30`")
    
    async def profit_factor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show profit factor analysis"""
        total_pnl = sum(t.get('pnl', 0) for t in self.bot.completed_orders)
        winning = [t.get('pnl', 0) for t in self.bot.completed_orders if t.get('pnl', 0) > 0]
        losing = [abs(t.get('pnl', 0)) for t in self.bot.completed_orders if t.get('pnl', 0) < 0]
        
        gross_profit = sum(winning) if winning else 0
        gross_loss = sum(losing) if losing else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        msg = f"""📈 *Profit Factor Analysis*

*Profit Factor:* {profit_factor:.2f}
• Gross Profit: ₹{gross_profit:+,.2f}
• Gross Loss: ₹{gross_loss:+,.2f}

*Interpretation:*
• > 2.0: 🟢 Excellent strategy
• 1.5 - 2.0: 🟡 Good
• 1.0 - 1.5: 🟠 Average
• < 1.0: 🔴 Needs improvement

*Your Strategy:* {self.get_profit_factor_rating(profit_factor)}"""
        
        await self._send_response(update, msg)
    
    async def drawdown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show drawdown analysis"""
        if not self.bot.completed_orders:
            await self._send_response(update, "📊 *No trades yet.* Drawdown analysis not available.")
            return
        
        cumulative = 0
        peak = 0
        max_dd = 0
        current_dd = 0
        
        for trade in self.bot.completed_orders:
            cumulative += trade.get('pnl', 0)
            if cumulative > peak:
                peak = cumulative
            current_dd = (peak - cumulative) / peak * 100 if peak > 0 else 0
            if current_dd > max_dd:
                max_dd = current_dd
        
        msg = f"""📉 *Drawdown Analysis*

*Maximum Drawdown:* {max_dd:.2f}%
*Current Drawdown:* {current_dd:.2f}%
*Peak Equity:* ₹{peak:,.2f}
*Current Equity:* ₹{cumulative:,.2f}

*Risk Levels:*
• 🟢 Low Risk: < 10% drawdown
• 🟡 Medium Risk: 10-20% drawdown
• 🔴 High Risk: > 20% drawdown

*Your Current Risk Level:* {self.get_drawdown_level(max_dd)}"""
        
        await self._send_response(update, msg)
    
    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show today's performance"""
        today = datetime.now().date()
        today_trades = [t for t in self.bot.completed_orders 
                       if datetime.fromisoformat(t.get('entry_time', '')).date() == today]
        
        if not today_trades:
            await self._send_response(update, "📊 *No trades today.* Bot is waiting for signals.")
            return
        
        total_pnl = sum(t.get('pnl', 0) for t in today_trades)
        winning = len([t for t in today_trades if t.get('pnl', 0) > 0])
        
        msg = f"""📅 *Today's Performance* ({today.strftime('%Y-%m-%d')})

*Trades Today:* {len(today_trades)}
• Winning: {winning}
• Losing: {len(today_trades) - winning}
• Win Rate: {(winning/len(today_trades)*100):.1f}%
• Total P&L: ₹{total_pnl:+,.2f}

*Trades:*
"""
        for trade in today_trades[-5:]:  # Last 5 trades
            emoji = "✅" if trade.get('pnl', 0) > 0 else "❌"
            msg += f"• {emoji} {trade.get('symbol')}: ₹{trade.get('pnl', 0):+,.2f}\n"
        
        await self._send_response(update, msg)
    
    async def best_trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show best trade ever"""
        if not self.bot.completed_orders:
            await self._send_response(update, "📊 *No trades yet.*")
            return
        
        best_trade = max(self.bot.completed_orders, key=lambda x: x.get('pnl', 0))
        
        msg = f"""🏆 *Best Trade Ever*

• Symbol: {best_trade.get('symbol')}
• P&L: ₹{best_trade.get('pnl', 0):+,.2f}
• Strategy: {best_trade.get('strategy')}
• Entry: ₹{best_trade.get('entry_price', 0):.2f}
• Exit: ₹{best_trade.get('exit_price', 0):.2f}
• Quantity: {best_trade.get('qty', 0)}
• Date: {best_trade.get('entry_time', 'N/A')[:10]}

🏆 This is your all-time winning trade!"""
        
        await self._send_response(update, msg)
    
    async def worst_trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show worst trade ever"""
        if not self.bot.completed_orders:
            await self._send_response(update, "📊 *No trades yet.*")
            return
        
        worst_trade = min(self.bot.completed_orders, key=lambda x: x.get('pnl', 0))
        
        msg = f"""💀 *Worst Trade Ever*

• Symbol: {worst_trade.get('symbol')}
• P&L: ₹{worst_trade.get('pnl', 0):+,.2f}
• Strategy: {worst_trade.get('strategy')}
• Entry: ₹{worst_trade.get('entry_price', 0):.2f}
• Exit: ₹{worst_trade.get('exit_price', 0):.2f}
• Quantity: {worst_trade.get('qty', 0)}
• Date: {worst_trade.get('entry_time', 'N/A')[:10]}

💡 Learn from this trade to improve your strategy!"""
        
        await self._send_response(update, msg)


    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data


        class FakeUpdate:
            def __init__(self, message):
                self.message = message
                self.callback_query = query

        fake_update = FakeUpdate(query.message, query)
        
        # Handle edit config callbacks
        if data.startswith("edit_"):
            setting = data.replace("edit_", "")
            if setting == "config":
                await self.edit_config_command(update, context)
            else:
                await self._handle_edit_callback(update, setting)
            return

        # Handle mode selection buttons
        if data == "modeselect":
            await self.modeselect_command(fake_update, context)
            return
        elif data == "tradingparams":
            await self.tradingparams_command(fake_update, context)  # ❌ fake_update not defined!
            return
        elif data == "show_timeframe":
            await self.set_timeframe_command(fake_update, context)  # ❌ fake_update not defined!
            return
        elif data == "show_otm":
            await self.set_otm_command(fake_update, context)  # ❌ fake_update not defined!
            return

        
        elif data == "mode_equity":
            await self._change_trading_mode(update, "EQUITY_ONLY")
            return
        elif data == "mode_fno":
            await self._change_trading_mode(update, "FNO_ONLY")
            return
        elif data == "mode_both":
            await self._change_trading_mode(update, "BOTH")
            return
        elif data == "mode_cancel":
            await query.edit_message_text("✅ Mode selection cancelled")
            return
        elif data == "mode_status":
            await self._show_mode_status(update)
            return

        # Add these in the button_callback method
        elif data == "tradingparams":
            await self.tradingparams_command(fake_update, context)
            return
        elif data == "show_timeframe":
            await self.set_timeframe_command(fake_update, context)
            return
        elif data == "show_otm":
            await self.set_otm_command(fake_update, context)
            return
        elif data == "show_trading_params":
            await self._show_trading_params(update)
            return
        elif data.startswith("tf_"):
            new_timeframe = data.replace("tf_", "")
            await self._update_timeframe(update, new_timeframe)
            return
        elif data.startswith("otm_"):
            new_otm = int(data.replace("otm_", ""))
            await self._update_otm(update, new_otm)
            return

        
        # Handle set_ callbacks (select options)
        if data.startswith("set_"):
            parts = data.split("_", 2)
            if len(parts) >= 3:
                setting = parts[1]
                value = parts[2]
                # Update the config value
                from config import Config
                from config import Config
                
                # Handle different setting types
                if setting == "trading_mode":
                    Config.TRADING_MODE = value
                    Config.WATCHLIST = Config.get_active_watchlist()
                    if hasattr(self.bot, 'update_active_watchlist'):
                        self.bot.update_active_watchlist()
                    await query.edit_message_text(f"✅ Trading mode changed to {value}")
                elif setting == "base_capital":
                    Config.BASE_CAPITAL = float(value)
                    await query.edit_message_text(f"✅ Base capital updated to ₹{float(value):,.2f}")
                elif setting == "risk_percent":
                    Config.BASE_CAPITAL_RISK_PERCENT = float(value) / 100
                    await query.edit_message_text(f"✅ Risk per trade updated to {value}%")
                elif setting == "signal_threshold":
                    Config.MIN_SIGNAL_STRENGTH = int(value)
                    await query.edit_message_text(f"✅ Signal threshold updated to {value}/100")
                elif setting == "max_orders":
                    Config.MAX_ORDERS_PER_DAY = int(value)
                    await query.edit_message_text(f"✅ Max orders per day updated to {value}")
                elif setting == "rr_ratio":
                    Config.RISK_REWARD_RATIO = float(value)
                    await query.edit_message_text(f"✅ Risk/Reward ratio updated to 1:{value}")
                elif setting == "otm_count":
                    Config.OPTION_OTM_COUNT = int(value)
                    await query.edit_message_text(f"✅ Option OTM count updated to {value}")
                elif setting == "max_lots":
                    Config.OPTION_MAX_LOTS_PER_TRADE = int(value)
                    await query.edit_message_text(f"✅ Option max lots updated to {value}")
                elif setting == "sl_percent":
                    Config.OPTION_SL_MULTIPLIER = float(value) / 100
                    await query.edit_message_text(f"✅ Option stop loss updated to {value}%")
                elif setting == "target_percent":
                    Config.OPTION_TARGET_MULTIPLIER = float(value) / 100
                    await query.edit_message_text(f"✅ Option target updated to {value}%")
                elif setting == "timeframe":
                    Config.TIMEFRAME = value
                    await query.edit_message_text(f"✅ Timeframe updated to {value} minutes")
                
                # Show config editor again
                await self.edit_config_command(update, context)
            return
        
        # Handle view_config
        if data == "view_config":
            await self.config_command(update, context)
            return
        
        # Handle close_editor
        if data == "close_editor":
            await query.edit_message_text("✅ Configuration editor closed")
            return
        
        
               
        commands = {
            "status": self.status_command,
            "balance": self.balance_command,
            "positions": self.positions_command,
            "watchlist": self.watchlist_command,
            "watchlists": self.watchlists_command,
            "strategies": self.strategies_command,
            "stats": self.stats_command,
            "config": self.config_command,
            "market": self.market_command,
            "signals": self.signals_command,
            "performance": self.performance_command,
            "risk": self.risk_command,
            "alerts": self.alerts_command,
            "help": self.help_command,
            "close_all": self.close_all_command,
            "tradingmode": self.tradingmode_command,
            "option_status": self.option_status_command,
            "option_on": self.option_on_command,
            "option_off": self.option_off_command,
            "profit_factor": self.profit_factor_command,
            "drawdown": self.drawdown_command,
            "today": self.today_command,
            "best": self.best_trade_command,
            "worst": self.worst_trade_command,
        }
        
        if data in commands:
            await commands[data](fake_update, context)
        else:
            await query.edit_message_text(f"❌ Unknown command: {data}")
    
    # Helper methods
    def calculate_streak(self) -> str:
        """Calculate current win/loss streak"""
        if not self.bot.completed_orders:
            return "No trades yet"
        
        streak = 0
        current_type = None
        
        for trade in reversed(self.bot.completed_orders):
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                if current_type == 'loss':
                    break
                current_type = 'win'
                streak += 1
            elif pnl < 0:
                if current_type == 'win':
                    break
                current_type = 'loss'
                streak += 1
        
        if current_type == 'win':
            return f"📈 {streak} consecutive wins"
        elif current_type == 'loss':
            return f"📉 {streak} consecutive losses"
        return "No streak"
    
    def get_profit_factor_rating(self, pf: float) -> str:
        """Get rating for profit factor"""
        if pf >= 2.0:
            return "🟢 Excellent - Keep going!"
        elif pf >= 1.5:
            return "🟡 Good - Room for improvement"
        elif pf >= 1.0:
            return "🟠 Average - Optimize strategy"
        else:
            return "🔴 Poor - Review and adjust"
    
    def get_drawdown_level(self, dd: float) -> str:
        """Get risk level based on drawdown"""
        if dd < 10:
            return "🟢 Low Risk"
        elif dd < 20:
            return "🟡 Medium Risk"
        else:
            return "🔴 High Risk - Consider reducing position size"





######################################################################################################################################################










