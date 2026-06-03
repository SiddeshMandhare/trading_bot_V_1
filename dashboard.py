# # dashboard.py
# import streamlit as st
# import pandas as pd
# import sqlite3
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import datetime

# st.set_page_config(page_title="Trading Bot Dashboard", layout="wide", page_icon="📈")

# st.title("📈 Trading Bot Dashboard")
# st.markdown("---")

# # Connect to database
# @st.cache_resource
# def get_connection():
#     conn = sqlite3.connect('trading_bot.db', check_same_thread=False)
#     # Create table if it doesn't exist
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS trades (
#             trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             symbol TEXT,
#             entry_time DATETIME,
#             entry_price REAL,
#             quantity INTEGER,
#             stop_loss REAL,
#             pnl REAL,
#             strategy TEXT,
#             status TEXT
#         )
#     ''')
#     conn.commit()
#     return conn

# # Load trades
# @st.cache_data(ttl=5)
# def load_trades():
#     try:
#         conn = get_connection()
#         df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_id DESC", conn)
#         conn.close()
#         return df if not df.empty else pd.DataFrame()
#     except Exception as e:
#         return pd.DataFrame()

# # Sidebar
# with st.sidebar:
#     st.header("📊 Controls")
#     auto_refresh = st.checkbox("Auto Refresh (every 10s)", value=True)
    
#     st.markdown("---")
#     st.header("🤖 Bot Commands")
#     st.code("""
# /status - Bot status
# /balance - Account balance
# /positions - Open positions
# /watchlist - Current watchlist
# /close_all - Close all
#     """)
    
#     st.markdown("---")
#     st.header("ℹ️ Info")
#     trades_df = load_trades()
#     if trades_df.empty:
#         st.info("No trades yet. Bot is waiting for signals...")
#     else:
#         st.success(f"{len(trades_df)} trades recorded")

# # Main content - 3 columns
# col1, col2, col3 = st.columns(3)

# trades_df = load_trades()

# with col1:
#     st.metric("📊 Total Trades", len(trades_df))
    
# with col2:
#     total_pnl = trades_df['pnl'].sum() if not trades_df.empty else 0
#     st.metric("💰 Total P&L", f"₹{total_pnl:,.2f}", 
#               delta=f"{total_pnl:+,.2f}" if total_pnl != 0 else None)

# with col3:
#     if not trades_df.empty:
#         winning = len(trades_df[trades_df['pnl'] > 0])
#         win_rate = (winning / len(trades_df) * 100) if len(trades_df) > 0 else 0
#     else:
#         win_rate = 0
#     st.metric("🏆 Win Rate", f"{win_rate:.1f}%")

# st.markdown("---")

# # Bot Status Section
# st.subheader("🤖 Bot Status")

# # Check if bot is running (optional - shows placeholder)
# status_col1, status_col2, status_col3 = st.columns(3)

# with status_col1:
#     st.info("📊 **Market Hours**")
#     current_time = datetime.datetime.now().time()
#     market_open = datetime.time(9, 15)
#     market_close = datetime.time(15, 30)
#     is_market_open = market_open <= current_time <= market_close
#     st.metric("Market Status", "🟢 OPEN" if is_market_open else "🔴 CLOSED")

# with status_col2:
#     st.info("🎯 **Active Strategies**")
#     st.code("""
# EMA_RSI
# MACD_Bollinger
# RSI_50_Crossover
# VWAP_Reversion
# MA_Crossover_50_200
# ORB_30min
#     """)

# with status_col3:
#     st.info("📋 **Watchlist**")
#     from config import Config
#     st.code("\n".join(Config.WATCHLIST))

# st.markdown("---")

# # Trades Table
# st.subheader("📋 Recent Trades")

# if not trades_df.empty:
#     # Format for display
#     display_df = trades_df[['trade_id', 'symbol', 'entry_price', 'quantity', 'pnl', 'strategy', 'status']].copy()
#     display_df.columns = ['ID', 'Symbol', 'Entry Price', 'Qty', 'P&L', 'Strategy', 'Status']
    
#     # Color code P&L
#     def color_pnl(val):
#         if isinstance(val, (int, float)):
#             if val > 0:
#                 return 'color: green'
#             elif val < 0:
#                 return 'color: red'
#         return ''
    
#     st.dataframe(display_df.style.applymap(color_pnl, subset=['P&L']), use_container_width=True)
# else:
#     st.info("📭 No trades recorded yet. The bot is waiting for trading signals during market hours (9:15 AM - 3:30 PM).")
#     st.markdown("""
#     ### 📝 Next Steps:
#     1. Make sure market is open (Monday-Friday, 9:15 AM - 3:30 PM)
#     2. Bot will automatically scan your watchlist: """ + ", ".join(Config.WATCHLIST) + """
#     3. When signals are generated, trades will appear here
#     4. Check Telegram for real-time alerts
#     """)

# # Performance Chart
# if not trades_df.empty and len(trades_df) > 1:
#     st.subheader("📈 Equity Curve")
    
#     # Calculate cumulative P&L
#     trades_df_sorted = trades_df.sort_values('trade_id')
#     trades_df_sorted['cumulative_pnl'] = trades_df_sorted['pnl'].cumsum()
    
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=trades_df_sorted['trade_id'],
#         y=trades_df_sorted['cumulative_pnl'],
#         mode='lines+markers',
#         name='Cumulative P&L',
#         line=dict(color='green', width=2),
#         marker=dict(size=8)
#     ))
    
#     fig.update_layout(
#         title="Equity Curve Over Time",
#         xaxis_title="Trade Number",
#         yaxis_title="Cumulative P&L (₹)",
#         height=400
#     )
    
#     st.plotly_chart(fig, use_container_width=True)

# # Auto-refresh
# if auto_refresh:
#     import time
#     time.sleep(10)
#     st.rerun()



#######################################################################################



# # dashboard.py - Enhanced Full Version
# import streamlit as st
# import pandas as pd
# import sqlite3
# import plotly.graph_objects as go
# import plotly.express as px
# from plotly.subplots import make_subplots
# import datetime
# import os
# import json
# from collections import defaultdict

# st.set_page_config(
#     page_title="Trading Bot Dashboard", 
#     layout="wide", 
#     page_icon="📈",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS for better mobile view
# st.markdown("""
# <style>
#     .stMetric {
#         background-color: #f0f2f6;
#         border-radius: 10px;
#         padding: 10px;
#     }
#     .metric-card {
#         background-color: #262730;
#         border-radius: 10px;
#         padding: 15px;
#         margin: 10px 0;
#     }
#     .positive {
#         color: #00ff00;
#     }
#     .negative {
#         color: #ff4444;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ============================================
# # DATABASE FUNCTIONS
# # ============================================

# @st.cache_resource
# def get_connection():
#     conn = sqlite3.connect('trading_bot.db', check_same_thread=False)
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS trades (
#             trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             symbol TEXT,
#             entry_time DATETIME,
#             entry_price REAL,
#             quantity INTEGER,
#             stop_loss REAL,
#             target_price REAL,
#             exit_price REAL,
#             pnl REAL,
#             strategy TEXT,
#             position_type TEXT,
#             status TEXT,
#             exit_reason TEXT,
#             exit_time DATETIME
#         )
#     ''')
#     # Add missing columns if needed
#     cursor.execute("PRAGMA table_info(trades)")
#     columns = [col[1] for col in cursor.fetchall()]
#     if 'target_price' not in columns:
#         cursor.execute("ALTER TABLE trades ADD COLUMN target_price REAL")
#     if 'exit_reason' not in columns:
#         cursor.execute("ALTER TABLE trades ADD COLUMN exit_reason TEXT")
#     if 'position_type' not in columns:
#         cursor.execute("ALTER TABLE trades ADD COLUMN position_type TEXT")
#     conn.commit()
#     return conn

# @st.cache_data(ttl=5)
# def load_trades():
#     try:
#         conn = get_connection()
#         df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_id DESC", conn)
#         conn.close()
#         return df if not df.empty else pd.DataFrame()
#     except Exception as e:
#         return pd.DataFrame()

# @st.cache_data(ttl=5)
# def get_trade_stats():
#     df = load_trades()
#     if df.empty:
#         return {
#             'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
#             'total_pnl': 0, 'win_rate': 0, 'avg_win': 0, 'avg_loss': 0,
#             'profit_factor': 0, 'largest_win': 0, 'largest_loss': 0,
#             'avg_holding_minutes': 0, 'max_consecutive_wins': 0, 'max_consecutive_losses': 0
#         }
    
#     winning = df[df['pnl'] > 0]
#     losing = df[df['pnl'] < 0]
    
#     # Calculate consecutive wins/losses
#     consecutive_wins = 0
#     consecutive_losses = 0
#     max_consecutive_wins = 0
#     max_consecutive_losses = 0
    
#     for pnl in df.sort_values('trade_id')['pnl']:
#         if pnl > 0:
#             consecutive_wins += 1
#             consecutive_losses = 0
#             max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
#         elif pnl < 0:
#             consecutive_losses += 1
#             consecutive_wins = 0
#             max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
    
#     # Calculate holding time
#     avg_holding = 0
#     if 'entry_time' in df.columns and 'exit_time' in df.columns:
#         df['entry_dt'] = pd.to_datetime(df['entry_time'])
#         df['exit_dt'] = pd.to_datetime(df['exit_time'])
#         df['holding_min'] = (df['exit_dt'] - df['entry_dt']).dt.total_seconds() / 60
#         avg_holding = df['holding_min'].mean() if not df['holding_min'].isna().all() else 0
    
#     gross_profit = winning['pnl'].sum() if not winning.empty else 0
#     gross_loss = abs(losing['pnl'].sum()) if not losing.empty else 0
    
#     return {
#         'total_trades': len(df),
#         'winning_trades': len(winning),
#         'losing_trades': len(losing),
#         'total_pnl': df['pnl'].sum(),
#         'win_rate': (len(winning) / len(df) * 100) if len(df) > 0 else 0,
#         'avg_win': winning['pnl'].mean() if not winning.empty else 0,
#         'avg_loss': losing['pnl'].mean() if not losing.empty else 0,
#         'profit_factor': gross_profit / gross_loss if gross_loss > 0 else 0,
#         'largest_win': winning['pnl'].max() if not winning.empty else 0,
#         'largest_loss': losing['pnl'].min() if not losing.empty else 0,
#         'avg_holding_minutes': avg_holding,
#         'max_consecutive_wins': max_consecutive_wins,
#         'max_consecutive_losses': max_consecutive_losses
#     }

# @st.cache_data(ttl=5)
# def get_strategy_stats():
#     df = load_trades()
#     if df.empty:
#         return pd.DataFrame()
    
#     strategy_data = []
#     for strategy in df['strategy'].unique():
#         strat_df = df[df['strategy'] == strategy]
#         winning = strat_df[strat_df['pnl'] > 0]
#         strategy_data.append({
#             'Strategy': strategy,
#             'Trades': len(strat_df),
#             'Wins': len(winning),
#             'Win Rate %': (len(winning) / len(strat_df) * 100) if len(strat_df) > 0 else 0,
#             'Total P&L': strat_df['pnl'].sum(),
#             'Avg P&L': strat_df['pnl'].mean(),
#             'Profit Factor': (winning['pnl'].sum() / abs(strat_df[strat_df['pnl'] < 0]['pnl'].sum())) if len(strat_df[strat_df['pnl'] < 0]) > 0 else 0
#         })
#     return pd.DataFrame(strategy_data).sort_values('Total P&L', ascending=False)

# # ============================================
# # SIDEBAR
# # ============================================

# with st.sidebar:
#     st.image("https://img.icons8.com/color/96/000000/stock.png", width=80)
#     st.title("📊 Trading Bot")
#     st.markdown("---")
    
#     # Auto refresh
#     auto_refresh = st.checkbox("🔄 Auto Refresh", value=True)
#     if auto_refresh:
#         refresh_rate = st.selectbox("Refresh every:", ["5 seconds", "10 seconds", "30 seconds", "1 minute"], index=1)
#         refresh_seconds = {"5 seconds": 5, "10 seconds": 10, "30 seconds": 30, "1 minute": 60}[refresh_rate]
    
#     st.markdown("---")
    
#     # Bot Commands
#     st.subheader("🤖 Bot Commands")
#     st.code("""
# /status - Bot status
# /balance - Account balance
# /positions - Open positions
# /watchlist - View symbols
# /add_symbol SYMBOL
# /remove_symbol SYMBOL
# /close_all - Close all
#     """)
    
#     st.markdown("---")
    
#     # Bot Status
#     st.subheader("📡 Bot Status")
#     from config import Config
#     st.info(f"📋 Watchlist: {', '.join(Config.WATCHLIST)}")
    
#     # Check if bot is running (look for pid file)
#     bot_running = os.path.exists("bot.pid")
#     if bot_running:
#         st.success("🟢 Bot is RUNNING")
#     else:
#         st.warning("⚫ Bot is STOPPED")

# # ============================================
# # HEADER METRICS
# # ============================================

# st.title("📈 Trading Bot Dashboard")
# st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# # Top metrics row
# stats = get_trade_stats()
# col1, col2, col3, col4, col5 = st.columns(5)

# with col1:
#     st.metric("📊 Total Trades", stats['total_trades'])
# with col2:
#     color = "normal" if stats['total_pnl'] >= 0 else "inverse"
#     st.metric("💰 Total P&L", f"₹{stats['total_pnl']:,.2f}", 
#               delta=f"{stats['total_pnl']:+,.2f}" if stats['total_pnl'] != 0 else None)
# with col3:
#     st.metric("🏆 Win Rate", f"{stats['win_rate']:.1f}%")
# with col4:
#     st.metric("📈 Profit Factor", f"{stats['profit_factor']:.2f}")
# with col5:
#     current_time = datetime.datetime.now().time()
#     market_open = datetime.time(9, 15)
#     market_close = datetime.time(15, 30)
#     is_market_open = market_open <= current_time <= market_close
#     st.metric("🕐 Market", "🟢 OPEN" if is_market_open else "🔴 CLOSED")

# st.markdown("---")

# # ============================================
# # SECOND ROW METRICS
# # ============================================

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     st.metric("📈 Avg Win", f"₹{stats['avg_win']:,.2f}")
# with col2:
#     st.metric("📉 Avg Loss", f"₹{stats['avg_loss']:,.2f}")
# with col3:
#     st.metric("🏆 Biggest Win", f"₹{stats['largest_win']:,.2f}")
# with col4:
#     st.metric("💀 Biggest Loss", f"₹{stats['largest_loss']:,.2f}")

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     st.metric("📊 Win Streak", f"{stats['max_consecutive_wins']}")
# with col2:
#     st.metric("📉 Loss Streak", f"{stats['max_consecutive_losses']}")
# with col3:
#     st.metric("⏱️ Avg Hold Time", f"{stats['avg_holding_minutes']:.0f} min")
# with col4:
#     st.metric("📋 Open Positions", "0")  # You can populate this from your bot

# st.markdown("---")

# # ============================================
# # CHARTS SECTION
# # ============================================

# trades_df = load_trades()

# if not trades_df.empty:
#     # Create two columns for charts
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("📈 Equity Curve")
#         trades_sorted = trades_df.sort_values('trade_id')
#         trades_sorted['cumulative_pnl'] = trades_sorted['pnl'].cumsum()
        
#         fig = go.Figure()
#         fig.add_trace(go.Scatter(
#             x=trades_sorted['trade_id'],
#             y=trades_sorted['cumulative_pnl'],
#             mode='lines+markers',
#             name='Equity Curve',
#             line=dict(color='#00ff00', width=2),
#             marker=dict(size=6, color=trades_sorted['pnl'].apply(lambda x: 'green' if x > 0 else 'red'))
#         ))
#         fig.update_layout(title="Cumulative P&L", xaxis_title="Trade #", yaxis_title="₹", height=350)
#         st.plotly_chart(fig, use_container_width=True)
    
#     with col2:
#         st.subheader("📊 P&L Distribution")
#         fig = px.histogram(
#             trades_df, x='pnl', nbins=20,
#             title="P&L Distribution",
#             color_discrete_sequence=['#00ff00']
#         )
#         fig.update_layout(xaxis_title="P&L (₹)", yaxis_title="Frequency", height=350)
#         st.plotly_chart(fig, use_container_width=True)
    
#     # Strategy Performance
#     st.subheader("🎯 Strategy Performance")
#     strategy_df = get_strategy_stats()
#     if not strategy_df.empty:
#         # Format for display
#         strategy_display = strategy_df.copy()
#         strategy_display['Total P&L'] = strategy_display['Total P&L'].apply(lambda x: f"₹{x:+,.2f}")
#         strategy_display['Avg P&L'] = strategy_display['Avg P&L'].apply(lambda x: f"₹{x:+,.2f}")
#         st.dataframe(strategy_display, use_container_width=True)
        
#         # Strategy bar chart
#         fig = px.bar(
#             strategy_df, x='Strategy', y='Total P&L',
#             title="Strategy P&L Comparison",
#             color='Total P&L',
#             color_continuous_scale=['red', 'yellow', 'green']
#         )
#         st.plotly_chart(fig, use_container_width=True)
    
#     # Daily P&L
#     st.subheader("📅 Daily Performance")
#     if 'entry_time' in trades_df.columns:
#         trades_df['date'] = pd.to_datetime(trades_df['entry_time']).dt.date
#         daily_pnl = trades_df.groupby('date')['pnl'].sum().reset_index()
        
#         fig = px.bar(
#             daily_pnl, x='date', y='pnl',
#             title="Daily P&L",
#             color='pnl',
#             color_continuous_scale=['red', 'yellow', 'green']
#         )
#         fig.update_layout(xaxis_title="Date", yaxis_title="P&L (₹)", height=350)
#         st.plotly_chart(fig, use_container_width=True)

# else:
#     st.info("📭 No trades yet. Bot is waiting for trading signals during market hours (9:15 AM - 3:30 PM)")

# st.markdown("---")

# # ============================================
# # TRADES TABLE
# # ============================================

# st.subheader("📋 Recent Trades")

# if not trades_df.empty:
#     # Prepare display columns
#     display_cols = ['trade_id', 'symbol', 'entry_price', 'quantity', 'pnl', 'strategy', 'position_type', 'status']
#     available_cols = [col for col in display_cols if col in trades_df.columns]
    
#     display_df = trades_df[available_cols].copy()
    
#     # Rename columns
#     column_names = {
#         'trade_id': 'ID', 'symbol': 'Symbol', 'entry_price': 'Entry',
#         'quantity': 'Qty', 'pnl': 'P&L', 'strategy': 'Strategy',
#         'position_type': 'Type', 'status': 'Status'
#     }
#     display_df = display_df.rename(columns={k: v for k, v in column_names.items() if k in display_df.columns})
    
#     # Color code P&L
#     def color_pnl(val):
#         if isinstance(val, (int, float)):
#             if val > 0:
#                 return 'color: #00ff00'
#             elif val < 0:
#                 return 'color: #ff4444'
#         return ''
    
#     if 'P&L' in display_df.columns:
#         st.dataframe(display_df.style.applymap(color_pnl, subset=['P&L']), use_container_width=True)
#     else:
#         st.dataframe(display_df, use_container_width=True)
# else:
#     st.info("📭 No trades recorded yet")

# # ============================================
# # TOKEN STATUS (Optional)
# # ============================================

# st.markdown("---")
# with st.expander("🔐 Authentication Status"):
#     try:
#         from auth_service import get_token_status
#         status = get_token_status(Config.CLIENT_CODE)
#         if status and status.get('has_token'):
#             st.success(f"✅ Token valid until: {status.get('expires_at')}")
#         else:
#             st.warning("⚠️ No valid token found")
#     except:
#         st.info("Auth status not available")

# # ============================================
# # AUTO REFRESH
# # ============================================

# if auto_refresh:
#     import time
#     time.sleep(refresh_seconds)
#     st.rerun()


#########################################################################################################################################






# # dashboard.py - Complete All-in-One Trading Dashboard
# # Just run: streamlit run dashboard.py --server.address 0.0.0.0

# import streamlit as st
# import pandas as pd
# import sqlite3
# import plotly.graph_objects as go
# import plotly.express as px
# import datetime
# import os
# import time
# import requests
# from collections import defaultdict
# from config import Config

# st.set_page_config(
#     page_title="Trading Bot Dashboard", 
#     layout="wide", 
#     page_icon="📈",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS
# st.markdown("""
# <style>
#     .stMetric { background-color: #f0f2f6; border-radius: 10px; padding: 10px; }
#     .positive { color: #00ff00; }
#     .negative { color: #ff4444; }
#     .market-card { background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin: 5px; }
#     .gain { color: #00ff00; font-weight: bold; }
#     .loss { color: #ff4444; font-weight: bold; }
#     .neutral { color: #ffaa00; }
# </style>
# """, unsafe_allow_html=True)

# # ============================================
# # DATABASE FUNCTIONS
# # ============================================

# @st.cache_resource
# def get_connection():
#     conn = sqlite3.connect('trading_bot.db', check_same_thread=False)
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS trades (
#             trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             symbol TEXT, entry_time DATETIME, entry_price REAL,
#             quantity INTEGER, stop_loss REAL, target_price REAL,
#             exit_price REAL, pnl REAL, strategy TEXT,
#             position_type TEXT, status TEXT, exit_reason TEXT, exit_time DATETIME
#         )
#     ''')
#     # Add missing columns
#     cursor.execute("PRAGMA table_info(trades)")
#     columns = [col[1] for col in cursor.fetchall()]
#     for col in ['target_price', 'exit_reason', 'position_type']:
#         if col not in columns:
#             cursor.execute(f"ALTER TABLE trades ADD COLUMN {col} TEXT")
#     conn.commit()
#     return conn

# @st.cache_data(ttl=5)
# def load_trades():
#     try:
#         conn = get_connection()
#         df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_id DESC", conn)
#         conn.close()
#         return df if not df.empty else pd.DataFrame()
#     except:
#         return pd.DataFrame()

# # ============================================
# # MARKET DATA FUNCTIONS (Built-in, no extra files)
# # ============================================

# @st.cache_data(ttl=10)
# def get_token_from_cache():
#     """Get token from cache file"""
#     try:
#         token_file = "token_cache.json"
#         if os.path.exists(token_file):
#             import json
#             with open(token_file, 'r') as f:
#                 data = json.load(f)
#                 client_data = data.get(Config.CLIENT_CODE, {})
#                 return client_data.get('access_token')
#     except:
#         pass
#     return None

# @st.cache_data(ttl=10)
# def get_index_prices():
#     """Get NIFTY, BANKNIFTY, FINNIFTY prices"""
#     indices = {
#         "NIFTY 50": {"security_id": "13", "exchange": "IDX_I"},
#         "BANKNIFTY": {"security_id": "25", "exchange": "IDX_I"},
#         "FINNIFTY": {"security_id": "27", "exchange": "IDX_I"},
#         "SENSEX": {"security_id": "51", "exchange": "IDX_I"}
#     }
    
#     results = {}
#     token = get_token_from_cache()
    
#     if not token:
#         return {name: {"ltp": 0, "change": 0, "change_percent": 0, "error": "No token"} for name in indices}
    
#     for name, info in indices.items():
#         try:
#             url = "https://api.dhan.co/v2/marketfeed/ohlc"
#             payload = {info["exchange"]: [int(info["security_id"])]}
#             headers = {"access-token": token, "client-id": Config.CLIENT_CODE}
#             response = requests.post(url, json=payload, headers=headers, timeout=10)
            
#             if response.status_code == 200:
#                 data = response.json()
#                 sec_data = data.get("data", {}).get(info["exchange"], {}).get(info["security_id"], {})
#                 ltp = sec_data.get("last_price", 0)
#                 prev_close = sec_data.get("ohlc", {}).get("close", ltp)
#                 change = ltp - prev_close if prev_close else 0
#                 change_percent = (change / prev_close * 100) if prev_close else 0
                
#                 results[name] = {
#                     "ltp": ltp, "change": change, "change_percent": change_percent,
#                     "open": sec_data.get("ohlc", {}).get("open", 0),
#                     "high": sec_data.get("ohlc", {}).get("high", 0),
#                     "low": sec_data.get("ohlc", {}).get("low", 0)
#                 }
#             else:
#                 results[name] = {"ltp": 0, "change": 0, "change_percent": 0, "error": "API error"}
#         except Exception as e:
#             results[name] = {"ltp": 0, "change": 0, "change_percent": 0, "error": str(e)}
    
#     return results

# @st.cache_data(ttl=30)
# def get_top_stocks():
#     """Get sample top stocks data (uses fallback if API fails)"""
#     # Sample stocks with simulated data for dashboard visualization
#     stocks = [
#         {"name": "RELIANCE", "sector": "Energy", "price": 2850, "change": 2.5, "volume": "12.4M"},
#         {"name": "TCS", "sector": "IT", "price": 3850, "change": 1.8, "volume": "8.2M"},
#         {"name": "HDFC BANK", "sector": "Banking", "price": 1680, "change": -0.5, "volume": "15.1M"},
#         {"name": "INFOSYS", "sector": "IT", "price": 1520, "change": 2.1, "volume": "9.3M"},
#         {"name": "ICICI BANK", "sector": "Banking", "price": 1180, "change": 1.2, "volume": "11.7M"},
#         {"name": "ITC", "sector": "FMCG", "price": 445, "change": -0.8, "volume": "22.5M"},
#         {"name": "SBIN", "sector": "Banking", "price": 820, "change": 0.9, "volume": "18.3M"},
#         {"name": "BHARTIARTL", "sector": "Telecom", "price": 1150, "change": 3.2, "volume": "7.8M"},
#         {"name": "HINDUNILVR", "sector": "FMCG", "price": 2680, "change": -1.1, "volume": "5.2M"},
#         {"name": "WIPRO", "sector": "IT", "price": 490, "change": 1.5, "volume": "6.7M"},
#     ]
    
#     # Sort by change percentage
#     gainers = sorted(stocks, key=lambda x: x["change"], reverse=True)[:5]
#     losers = sorted(stocks, key=lambda x: x["change"])[:5]
    
#     return {"gainers": gainers, "losers": losers, "all": stocks}

# # ============================================
# # STRATEGY ANALYSIS FUNCTIONS
# # ============================================

# def get_strategy_performance():
#     """Get detailed strategy performance analysis"""
#     df = load_trades()
#     if df.empty:
#         return pd.DataFrame()
    
#     strategy_data = []
#     for strategy in df['strategy'].unique():
#         strat_df = df[df['strategy'] == strategy]
#         winning = strat_df[strat_df['pnl'] > 0]
#         losing = strat_df[strat_df['pnl'] < 0]
        
#         # Calculate metrics
#         total_trades = len(strat_df)
#         wins = len(winning)
#         losses = len(losing)
#         win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
#         total_pnl = strat_df['pnl'].sum()
#         avg_pnl = strat_df['pnl'].mean()
        
#         # Calculate profit factor
#         gross_profit = winning['pnl'].sum() if not winning.empty else 0
#         gross_loss = abs(losing['pnl'].sum()) if not losing.empty else 1
#         profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
#         # Calculate Sharpe ratio (simplified)
#         returns = strat_df['pnl'].values
#         sharpe = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0
        
#         # Calculate max drawdown
#         cumulative = strat_df['pnl'].cumsum()
#         running_max = cumulative.expanding().max()
#         drawdown = (cumulative - running_max) / running_max.abs() * 100
#         max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0
        
#         strategy_data.append({
#             'Strategy': strategy,
#             'Trades': total_trades,
#             'Wins': wins,
#             'Losses': losses,
#             'Win Rate %': round(win_rate, 1),
#             'Total P&L': round(total_pnl, 2),
#             'Avg P&L': round(avg_pnl, 2),
#             'Profit Factor': round(profit_factor, 2),
#             'Sharpe Ratio': round(sharpe, 2),
#             'Max Drawdown %': round(max_drawdown, 1),
#             'Best Trade': round(winning['pnl'].max(), 2) if not winning.empty else 0,
#             'Worst Trade': round(losing['pnl'].min(), 2) if not losing.empty else 0
#         })
    
#     return pd.DataFrame(strategy_data).sort_values('Total P&L', ascending=False)

# def get_recent_signals():
#     """Get recent strategy signals from log file"""
#     signals_data = []
#     try:
#         # Read from log file if it exists
#         log_file = "trading_bot.log"
#         if os.path.exists(log_file):
#             with open(log_file, 'r') as f:
#                 lines = f.readlines()[-50:]  # Last 50 lines
#                 for line in lines:
#                     if 'buy_call' in line or 'buy_put' in line or 'Signal' in line:
#                         signals_data.append(line.strip())
#     except:
#         pass
#     return signals_data

# # ============================================
# # SIDEBAR
# # ============================================

# with st.sidebar:
#     st.title("📊 Trading Bot")
#     st.markdown("---")
    
#     # Auto refresh
#     auto_refresh = st.checkbox("🔄 Auto Refresh", value=True)
#     if auto_refresh:
#         refresh_rate = st.selectbox("Refresh every:", ["5s", "10s", "30s", "1m"], index=1)
#         refresh_seconds = {"5s": 5, "10s": 10, "30s": 30, "1m": 60}[refresh_rate]
    
#     st.markdown("---")
    
#     st.subheader("🤖 Bot Commands")
#     st.code("""
# /status - Bot status
# /balance - Balance
# /positions - Open positions
# /watchlist - View symbols
# /add_symbol SYMBOL
# /remove_symbol SYMBOL
# /close_all - Close all
#     """)
    
#     st.markdown("---")
    
#     # Watchlist from config
#     st.subheader("📋 Watchlist")
#     st.info(f"{', '.join(Config.WATCHLIST)}")
    
#     # Market status
#     current_time = datetime.datetime.now().time()
#     market_open = datetime.time(9, 15)
#     market_close = datetime.time(15, 30)
#     is_market_open = market_open <= current_time <= datetime.time(15, 30)
#     st.markdown(f"**Market:** {'🟢 OPEN' if is_market_open else '🔴 CLOSED'}")

# # ============================================
# # HEADER METRICS
# # ============================================

# st.title("📈 Trading Bot Dashboard")
# st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# trades_df = load_trades()
# stats = {
#     'total_trades': len(trades_df),
#     'total_pnl': trades_df['pnl'].sum() if not trades_df.empty else 0,
#     'win_rate': (len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) * 100) if not trades_df.empty else 0
# }

# col1, col2, col3, col4, col5 = st.columns(5)
# with col1: st.metric("📊 Total Trades", stats['total_trades'])
# with col2: st.metric("💰 Total P&L", f"₹{stats['total_pnl']:,.2f}", delta=f"{stats['total_pnl']:+,.2f}")
# with col3: st.metric("🏆 Win Rate", f"{stats['win_rate']:.1f}%")
# with col4: st.metric("🕐 Market", "🟢 OPEN" if is_market_open else "🔴 CLOSED")
# with col5: 
#     active_strategies = len(trades_df['strategy'].unique()) if not trades_df.empty else 0
#     st.metric("🎯 Active Strategies", active_strategies)

# st.markdown("---")

# # ============================================
# # MARKET OVERVIEW SECTION
# # ============================================

# st.subheader("📊 Market Overview")
# st.markdown("---")

# # Index prices
# index_prices = get_index_prices()
# if index_prices:
#     cols = st.columns(len(index_prices))
#     for idx, (name, data) in enumerate(index_prices.items()):
#         with cols[idx]:
#             change_color = "🟢" if data.get('change', 0) >= 0 else "🔴"
#             st.metric(
#                 label=f"{change_color} {name}",
#                 value=f"₹{data.get('ltp', 0):,.2f}",
#                 delta=f"{data.get('change', 0):+.2f} ({data.get('change_percent', 0):+.2f}%)"
#             )
# else:
#     st.info("📭 Market data will appear during market hours (9:15 AM - 3:30 PM)")

# # Top Gainers & Losers
# top_stocks = get_top_stocks()

# col1, col2 = st.columns(2)

# with col1:
#     st.subheader("🚀 Top Gainers")
#     gainers = top_stocks.get('gainers', [])
#     for stock in gainers:
#         st.markdown(f"**{stock['name']}** ₹{stock['price']}   `+{stock['change']}%`")

# with col2:
#     st.subheader("📉 Top Losers")
#     losers = top_stocks.get('losers', [])
#     for stock in losers:
#         st.markdown(f"**{stock['name']}** ₹{stock['price']}   `{stock['change']}%`")

# st.markdown("---")

# # ============================================
# # STRATEGY ANALYSIS SECTION
# # ============================================

# st.subheader("🎯 Strategy Performance Analysis")
# st.markdown("---")

# strategy_df = get_strategy_performance()

# if not strategy_df.empty:
#     # Strategy summary cards
#     col1, col2, col3, col4 = st.columns(4)
    
#     best_strategy = strategy_df.iloc[0]['Strategy'] if not strategy_df.empty else "N/A"
#     best_pnl = strategy_df.iloc[0]['Total P&L'] if not strategy_df.empty else 0
    
#     worst_strategy = strategy_df.iloc[-1]['Strategy'] if not strategy_df.empty else "N/A"
#     worst_pnl = strategy_df.iloc[-1]['Total P&L'] if not strategy_df.empty else 0
    
#     with col1:
#         st.metric("🏆 Best Strategy", best_strategy, f"₹{best_pnl:+,.2f}")
#     with col2:
#         st.metric("📉 Worst Strategy", worst_strategy, f"₹{worst_pnl:+,.2f}")
#     with col3:
#         avg_win_rate = strategy_df['Win Rate %'].mean()
#         st.metric("📊 Avg Win Rate", f"{avg_win_rate:.1f}%")
#     with col4:
#         total_strategies = len(strategy_df)
#         st.metric("🎯 Active Strategies", total_strategies)
    
#     st.markdown("---")
    
#     # Detailed strategy table
#     st.subheader("📋 Strategy Details")
#     st.dataframe(strategy_df, use_container_width=True)
    
#     # Strategy P&L Chart
#     st.subheader("📊 Strategy P&L Comparison")
#     fig = px.bar(
#         strategy_df, x='Strategy', y='Total P&L',
#         title="Total P&L by Strategy",
#         color='Total P&L',
#         color_continuous_scale=['red', 'yellow', 'green'],
#         text='Total P&L'
#     )
#     fig.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
#     st.plotly_chart(fig, use_container_width=True)
    
#     # Win Rate vs Profit Factor Chart
#     st.subheader("📈 Strategy Efficiency Matrix")
#     fig = px.scatter(
#         strategy_df, x='Win Rate %', y='Profit Factor',
#         size='Trades', text='Strategy',
#         title="Win Rate vs Profit Factor",
#         color='Total P&L',
#         color_continuous_scale='RdYlGn'
#     )
#     fig.update_traces(textposition='top center')
#     st.plotly_chart(fig, use_container_width=True)
    
# else:
#     st.info("📭 No strategy data yet. Trades will appear here once the bot starts trading.")

# st.markdown("---")

# # ============================================
# # RECENT TRADES SECTION
# # ============================================

# st.subheader("📋 Recent Trades")

# if not trades_df.empty:
#     display_cols = ['trade_id', 'symbol', 'entry_price', 'quantity', 'pnl', 'strategy', 'position_type', 'status']
#     available_cols = [col for col in display_cols if col in trades_df.columns]
#     display_df = trades_df[available_cols].copy()
    
#     column_names = {'trade_id': 'ID', 'symbol': 'Symbol', 'entry_price': 'Entry', 'quantity': 'Qty', 
#                     'pnl': 'P&L', 'strategy': 'Strategy', 'position_type': 'Type', 'status': 'Status'}
#     display_df = display_df.rename(columns=column_names)
    
#     def color_pnl(val):
#         if isinstance(val, (int, float)):
#             return 'color: #00ff00' if val > 0 else 'color: #ff4444' if val < 0 else ''
#         return ''
    
#     st.dataframe(display_df.style.applymap(color_pnl, subset=['P&L']), use_container_width=True)
    
#     # Equity Curve
#     if len(trades_df) > 1:
#         st.subheader("📈 Equity Curve")
#         trades_sorted = trades_df.sort_values('trade_id')
#         trades_sorted['cumulative_pnl'] = trades_sorted['pnl'].cumsum()
        
#         fig = go.Figure()
#         fig.add_trace(go.Scatter(
#             x=trades_sorted['trade_id'], y=trades_sorted['cumulative_pnl'],
#             mode='lines+markers', name='Portfolio P&L',
#             line=dict(color='#00ff00', width=2),
#             marker=dict(size=6, color=trades_sorted['pnl'].apply(lambda x: 'green' if x > 0 else 'red'))
#         ))
#         fig.update_layout(title="Cumulative P&L", xaxis_title="Trade #", yaxis_title="₹", height=400)
#         st.plotly_chart(fig, use_container_width=True)
# else:
#     st.info("📭 No trades recorded yet. The bot is waiting for trading signals during market hours (9:15 AM - 3:30 PM).")

# st.markdown("---")

# # ============================================
# # SIGNAL LOGS (Recent strategy activity)
# # ============================================

# st.subheader("🔔 Recent Strategy Activity")

# signals = get_recent_signals()
# if signals:
#     for signal in signals[-10:]:  # Show last 10 signals
#         st.text(signal[:200])
# else:
#     st.info("📭 No recent signals. Check logs when bot is running.")

# st.markdown("---")

# # ============================================
# # AUTO REFRESH
# # ============================================

# if auto_refresh:
#     time.sleep(refresh_seconds)
#     st.rerun()





############################################################################################################################################

# dashboard_api.py - Fixed version (no import from main)
import json
import sqlite3
import os
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Dashboard HTML - Simple working version
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 20px; }
        .header h1 { font-size: 2rem; background: linear-gradient(135deg, #00ff88, #00aaff); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }
        .stat-label { font-size: 0.8rem; color: #888; text-transform: uppercase; }
        .stat-value { font-size: 1.8rem; font-weight: bold; margin: 10px 0; }
        .positive { color: #00ff88; }
        .negative { color: #ff4444; }
        .section { background: rgba(0,0,0,0.4); border-radius: 20px; padding: 25px; margin-bottom: 30px; }
        .section-title { font-size: 1.3rem; margin-bottom: 20px; border-bottom: 2px solid #00ff88; display: inline-block; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { background: rgba(0,255,136,0.1); color: #00ff88; }
        tr:hover { background: rgba(255,255,255,0.03); }
        .loading { text-align: center; padding: 40px; color: #888; }
        .refresh-indicator { position: fixed; bottom: 20px; right: 20px; background: rgba(0,0,0,0.7); padding: 8px 15px; border-radius: 20px; font-size: 0.75rem; }
        @media (max-width: 768px) { .stat-value { font-size: 1.3rem; } th, td { padding: 8px; font-size: 0.8rem; } }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📈 Trading Bot Dashboard</h1>
        <p id="marketStatus">Loading...</p>
        <div id="lastUpdated" style="font-size: 0.8rem; color: #666; margin-top: 10px;"></div>
    </div>

    <div class="stats-grid" id="statsGrid">
        <div class="stat-card"><div class="stat-label">📊 Total Trades</div><div class="stat-value" id="totalTrades">--</div></div>
        <div class="stat-card"><div class="stat-label">💰 Total P&L</div><div class="stat-value" id="totalPnl">--</div></div>
        <div class="stat-card"><div class="stat-label">🏆 Win Rate</div><div class="stat-value" id="winRate">--</div></div>
        <div class="stat-card"><div class="stat-label">📈 Open Positions</div><div class="stat-value" id="openPositions">--</div></div>
    </div>

    <div class="section">
        <h2 class="section-title">📋 Recent Trades</h2>
        <div style="overflow-x: auto;">
            <table id="tradesTable">
                <thead><tr><th>ID</th><th>Symbol</th><th>Entry</th><th>Exit</th><th>Qty</th><th>P&L</th><th>Strategy</th><th>Status</th></tr></thead>
                <tbody id="tradesBody"><tr><td colspan="8" class="loading">Loading trades...</td></tr></tbody>
            </table>
        </div>
    </div>

    <div class="refresh-indicator">Auto-refresh: <span id="countdown">10</span>s</div>
</div>

<script>
    let countdown = 10;
    
    async function loadData() {
        try {
            const resp = await fetch('/api/trades');
            const trades = await resp.json();
            
            let totalPnl = 0, winning = 0, closed = 0, openTrades = 0;
            trades.forEach(t => {
                if (t.status === 'closed' && t.pnl !== undefined) {
                    totalPnl += t.pnl;
                    closed++;
                    if (t.pnl > 0) winning++;
                } else if (t.status === 'open') {
                    openTrades++;
                }
            });
            
            document.getElementById('totalTrades').innerText = trades.length;
            const pnlElem = document.getElementById('totalPnl');
            pnlElem.innerText = `₹${totalPnl.toFixed(2)}`;
            pnlElem.className = `stat-value ${totalPnl >= 0 ? 'positive' : 'negative'}`;
            document.getElementById('winRate').innerText = closed > 0 ? ((winning/closed)*100).toFixed(1) + '%' : '0%';
            document.getElementById('openPositions').innerText = openTrades;
            
            const tbody = document.getElementById('tradesBody');
            if (trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="loading">No trades yet. Run main.py to start trading.</td></tr>';
            } else {
                tbody.innerHTML = trades.slice(0, 30).map(t => `
                    <tr>
                        <td>${t.trade_id || '-'}</td>
                        <td><strong>${t.symbol || '-'}</strong></td>
                        <td>₹${(t.entry_price || 0).toFixed(2)}</td>
                        <td>₹${(t.exit_price || 0).toFixed(2)}</td>
                        <td>${t.quantity || 0}</td>
                        <td class="${(t.pnl || 0) >= 0 ? 'positive' : 'negative'}">₹${(t.pnl || 0).toFixed(2)}</td>
                        <td>${t.strategy || '-'}</td>
                        <td>${t.status || 'closed'}</td>
                    </tr>
                `).join('');
            }
            
            const now = new Date();
            const hours = now.getHours();
            const mins = now.getMinutes();
            const isMarketOpen = (hours > 9 || (hours === 9 && mins >= 15)) && hours < 15;
            document.getElementById('marketStatus').innerHTML = isMarketOpen ? '🟢 MARKET OPEN' : '🔴 MARKET CLOSED';
            document.getElementById('lastUpdated').innerHTML = 'Updated: ' + now.toLocaleTimeString();
            
        } catch(e) {
            console.error(e);
            document.getElementById('tradesBody').innerHTML = '<tr><td colspan="8" class="loading">Error loading data. Make sure dashboard_api.py is running.</td></tr>';
        }
    }
    
    loadData();
    setInterval(() => {
        countdown--;
        document.getElementById('countdown').innerHTML = countdown;
        if (countdown <= 0) {
            countdown = 10;
            loadData();
        }
    }, 1000);
</script>
</body>
</html>'''

class DashboardHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/' or parsed.path == '/dashboard.html':
            self.send_html()
        elif parsed.path == '/api/trades':
            self.send_trades()
        elif parsed.path == '/api/all-data':
            self.send_trades()  # Same as /api/trades for simplicity
        else:
            self.send_error(404, "Not Found")
    
    def send_html(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(DASHBOARD_HTML.encode())
    
    def send_trades(self):
        """Send trades data from database"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'trading_bot.db')
            
            if not os.path.exists(db_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps([]).encode())
                return
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
            if not cursor.fetchone():
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps([]).encode())
                return
            
            # Get trades
            cursor.execute("""
                SELECT trade_id, symbol, entry_price, exit_price, quantity, pnl, 
                       strategy, status, entry_time
                FROM trades 
                ORDER BY trade_id DESC 
                LIMIT 100
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            trades = []
            for row in rows:
                trades.append({
                    'trade_id': row[0],
                    'symbol': row[1],
                    'entry_price': row[2] or 0,
                    'exit_price': row[3] or 0,
                    'quantity': row[4] or 0,
                    'pnl': row[5] or 0,
                    'strategy': row[6] or '-',
                    'status': row[7] or 'closed',
                    'entry_time': row[8] or ''
                })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(trades).encode())
            
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps([]).encode())
    
    def log_message(self, format, *args):
        """Reduce console noise - only show errors"""
        if '500' not in str(args):
            print(f"{args[0]} - {args[1]}")


if __name__ == '__main__':
    import socket
    port = 8080
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    
    print("="*50)
    print("📊 Trading Bot Dashboard")
    print("="*50)
    print(f"🌐 Open in browser: http://localhost:{port}")
    
    # Get local IP for phone access
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        print(f"📱 From phone: http://{ip_address}:{port}")
    except:
        pass
    
    print("="*50)
    print("Press Ctrl+C to stop")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
        server.shutdown()