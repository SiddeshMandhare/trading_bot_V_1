# # run_strategy_backtest_fixed2.py - Compatible with all pandas versions
# import pandas as pd
# import numpy as np
# import glob
# import os
# from datetime import datetime
# import talib

# # ============================================
# # STRATEGY CLASSES
# # ============================================

# class BacktestEMA_RSI:
#     def get_strategy_name(self): return "EMA_RSI"
    
#     def calculate_indicators(self, df):
#         if len(df) < 20:
#             return
#         df['ema_9'] = talib.EMA(df['close'], timeperiod=9)
#         df['ema_15'] = talib.EMA(df['close'], timeperiod=15)
#         df['rsi'] = talib.RSI(df['close'], timeperiod=14)
#         df['volume_ma'] = talib.SMA(df['volume'], timeperiod=20)
    
#     def generate_signals(self, df):
#         if len(df) < 2:
#             return {'buy_call': False, 'buy_put': False}
        
#         cc = df.iloc[-1]
#         prev = df.iloc[-2]
        
#         bullish_crossover = prev['ema_9'] < prev['ema_15'] and cc['ema_9'] > cc['ema_15']
#         bearish_crossover = prev['ema_9'] > prev['ema_15'] and cc['ema_9'] < cc['ema_15']
        
#         buy_call = cc['rsi'] > 50 and bullish_crossover
#         buy_put = cc['rsi'] < 50 and bearish_crossover
        
#         return {'buy_call': buy_call, 'buy_put': buy_put}

# class BacktestMACD_Bollinger:
#     def get_strategy_name(self): return "MACD_Bollinger"
    
#     def calculate_indicators(self, df):
#         if len(df) < 26:
#             return
#         df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
#         df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'])
#         df['volume_ma'] = talib.SMA(df['volume'], timeperiod=20)
    
#     def generate_signals(self, df):
#         if len(df) < 2:
#             return {'buy_call': False, 'buy_put': False}
        
#         cc = df.iloc[-1]
        
#         buy_call = (cc['macd'] > cc['macd_signal'] and 
#                    cc['close'] > cc['upper_band'] and
#                    cc['volume'] > cc['volume_ma'] * 1.5)
#         buy_put = (cc['macd'] < cc['macd_signal'] and 
#                   cc['close'] < cc['lower_band'] and
#                   cc['volume'] > cc['volume_ma'] * 1.5)
        
#         return {'buy_call': buy_call, 'buy_put': buy_put}

# class BacktestRSI_Crossover:
#     def get_strategy_name(self): return "RSI_50_Crossover"
    
#     def calculate_indicators(self, df):
#         if len(df) < 15:
#             return
#         df['rsi'] = talib.RSI(df['close'], timeperiod=14)
#         df['volume_ma'] = talib.SMA(df['volume'], timeperiod=20)
    
#     def generate_signals(self, df):
#         if len(df) < 2:
#             return {'buy_call': False, 'buy_put': False}
        
#         cc = df.iloc[-1]
#         prev = df.iloc[-2]
        
#         buy_call = cc['rsi'] > 50 and prev['rsi'] <= 50
#         buy_put = cc['rsi'] < 50 and prev['rsi'] >= 50
        
#         return {'buy_call': buy_call, 'buy_put': buy_put}

# class BacktestMA_Crossover:
#     def get_strategy_name(self): return "MA_Crossover_50_200"
    
#     def calculate_indicators(self, df):
#         if len(df) < 200:
#             return
#         df['ma_50'] = talib.SMA(df['close'], timeperiod=50)
#         df['ma_200'] = talib.SMA(df['close'], timeperiod=200)
#         df['volume_ma'] = talib.SMA(df['volume'], timeperiod=20)
    
#     def generate_signals(self, df):
#         if len(df) < 2:
#             return {'buy_call': False, 'buy_put': False}
        
#         cc = df.iloc[-1]
#         prev = df.iloc[-2]
        
#         golden_cross = prev['ma_50'] < prev['ma_200'] and cc['ma_50'] > cc['ma_200']
#         death_cross = prev['ma_50'] > prev['ma_200'] and cc['ma_50'] < cc['ma_200']
        
#         buy_call = golden_cross and cc['volume'] > cc['volume_ma'] * 1.5
#         buy_put = death_cross and cc['volume'] > cc['volume_ma'] * 1.5
        
#         return {'buy_call': buy_call, 'buy_put': buy_put}

# # ============================================
# # DATA LOADER FOR NESTED FOLDERS
# # ============================================

# def load_nested_csv_data(base_folder):
#     """
#     Load all CSV files from nested folder structure
#     """
#     print(f"\n📂 Scanning folder: {base_folder}")
    
#     if not os.path.exists(base_folder):
#         print(f"❌ Folder not found: {base_folder}")
#         return None
    
#     all_files = []
    
#     # Walk through all subdirectories
#     for root, dirs, files in os.walk(base_folder):
#         for file in files:
#             if file.endswith('.csv'):
#                 full_path = os.path.join(root, file)
#                 all_files.append(full_path)
    
#     print(f"✅ Found {len(all_files)} CSV files")
    
#     if not all_files:
#         return None
    
#     dfs = []
    
#     for file_path in all_files:
#         try:
#             df = pd.read_csv(file_path)
            
#             # Try to find datetime column
#             datetime_col = None
#             for col in df.columns:
#                 if 'time' in col.lower() or 'date' in col.lower() or 'datetime' in col.lower():
#                     datetime_col = col
#                     break
            
#             if datetime_col:
#                 df['datetime'] = pd.to_datetime(df[datetime_col], errors='coerce')
#             else:
#                 # Try to extract date from folder name
#                 folder_name = os.path.basename(root)
#                 try:
#                     date = pd.to_datetime(folder_name, errors='coerce')
#                     if pd.notna(date):
#                         df['datetime'] = date
#                     else:
#                         # Use file modification time as fallback
#                         mod_time = os.path.getmtime(file_path)
#                         df['datetime'] = pd.to_datetime(mod_time, unit='s')
#                 except:
#                     mod_time = os.path.getmtime(file_path)
#                     df['datetime'] = pd.to_datetime(mod_time, unit='s')
            
#             # Drop rows with invalid datetime
#             df = df.dropna(subset=['datetime'])
            
#             if len(df) == 0:
#                 continue
            
#             df.set_index('datetime', inplace=True)
#             df.sort_index(inplace=True)
            
#             # Rename columns to standard names
#             column_map = {
#                 'Open': 'open', 'OPEN': 'open', 'open': 'open',
#                 'High': 'high', 'HIGH': 'high', 'high': 'high',
#                 'Low': 'low', 'LOW': 'low', 'low': 'low',
#                 'Close': 'close', 'CLOSE': 'close', 'close': 'close',
#                 'Volume': 'volume', 'VOLUME': 'volume', 'volume': 'volume',
#                 'LTP': 'close', 'ltp': 'close'
#             }
#             df.rename(columns=column_map, inplace=True)
            
#             dfs.append(df)
            
#         except Exception as e:
#             print(f"⚠️ Error loading {os.path.basename(file_path)}: {e}")
    
#     if not dfs:
#         print("❌ No data loaded")
#         return None
    
#     # Combine all data
#     data = pd.concat(dfs)
#     data = data[~data.index.duplicated(keep='first')]
#     data.sort_index(inplace=True)
    
#     print(f"✅ Loaded {len(data)} total rows")
#     print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    
#     return data

# # ============================================
# # BACKTEST ENGINE
# # ============================================

# class BacktestEngine:
#     def __init__(self, initial_capital=100000):
#         self.initial_capital = initial_capital
#         self.strategies = {
#             'EMA_RSI': BacktestEMA_RSI(),
#             'MACD_Bollinger': BacktestMACD_Bollinger(),
#             'RSI_50_Crossover': BacktestRSI_Crossover(),
#             'MA_Crossover_50_200': BacktestMA_Crossover()
#         }
    
#     def prepare_data(self, data, timeframe_minutes=15):
#         """Resample data to desired timeframe using minutes"""
        
#         # Use 'min' for minute frequency (pandas 2.0+)
#         # For older pandas, use 'T' or 'min'
#         rule = f'{timeframe_minutes}min'
        
#         print(f"📊 Resampling to {timeframe_minutes} minute intervals using rule: {rule}")
        
#         # Ensure we have OHLCV columns
#         if 'close' not in data.columns:
#             print("❌ No 'close' column found in data")
#             # Try to find close-like column
#             for col in data.columns:
#                 if 'close' in col.lower() or 'ltp' in col.lower():
#                     data['close'] = data[col]
#                     break
#             if 'close' not in data.columns:
#                 return None
        
#         # Create OHLCV if missing
#         if 'open' not in data.columns:
#             data['open'] = data['close']
#         if 'high' not in data.columns:
#             data['high'] = data['close']
#         if 'low' not in data.columns:
#             data['low'] = data['close']
#         if 'volume' not in data.columns:
#             data['volume'] = 0
        
#         # Resample
#         try:
#             resampled = data.resample(rule).agg({
#                 'open': 'first',
#                 'high': 'max',
#                 'low': 'min',
#                 'close': 'last',
#                 'volume': 'sum'
#             }).dropna()
#         except Exception as e:
#             print(f"⚠️ Resampling with '{rule}' failed: {e}")
#             # Try alternative frequency
#             try:
#                 rule = f'{timeframe_minutes}T'
#                 print(f"   Trying alternative: {rule}")
#                 resampled = data.resample(rule).agg({
#                     'open': 'first',
#                     'high': 'max',
#                     'low': 'min',
#                     'close': 'last',
#                     'volume': 'sum'
#                 }).dropna()
#             except Exception as e2:
#                 print(f"❌ Resampling failed: {e2}")
#                 return data  # Return original data if resampling fails
        
#         print(f"   Resampled to {len(resampled)} candles")
#         return resampled
    
#     def run_backtest(self, data, strategy_name, symbol="NIFTY"):
#         """Run backtest for a single strategy"""
        
#         if strategy_name not in self.strategies:
#             print(f"❌ Strategy {strategy_name} not found")
#             return None
        
#         strategy = self.strategies[strategy_name]
#         print(f"\n{'='*60}")
#         print(f"📊 Running Backtest: {strategy.get_strategy_name()}")
#         print(f"{'='*60}")
#         print(f"   Data points: {len(data)}")
#         print(f"   Period: {data.index[0]} to {data.index[-1]}")
        
#         capital = self.initial_capital
#         positions = []
#         trades = []
#         equity_curve = []
#         peak_capital = self.initial_capital
#         max_drawdown = 0
        
#         # Calculate indicators for entire dataset
#         strategy.calculate_indicators(data)
        
#         for i in range(min(50, len(data)//2), len(data)):
#             current_data = data.iloc[:i+1].copy()
#             current_price = data['close'].iloc[i]
#             current_time = data.index[i]
            
#             # Generate signals
#             signals = strategy.generate_signals(current_data)
            
#             # Check existing positions
#             for pos in positions[:]:
#                 if pos['type'] == 'LONG':
#                     if current_price <= pos['stop_loss']:
#                         pnl = (current_price - pos['entry_price']) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append({
#                             'entry_time': pos['entry_time'],
#                             'exit_time': current_time,
#                             'action': 'LONG',
#                             'entry_price': pos['entry_price'],
#                             'exit_price': current_price,
#                             'quantity': pos['quantity'],
#                             'pnl': pnl,
#                             'exit_reason': 'STOP_LOSS'
#                         })
#                         positions.remove(pos)
#                     elif current_price >= pos['target']:
#                         pnl = (current_price - pos['entry_price']) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append({
#                             'entry_time': pos['entry_time'],
#                             'exit_time': current_time,
#                             'action': 'LONG',
#                             'entry_price': pos['entry_price'],
#                             'exit_price': current_price,
#                             'quantity': pos['quantity'],
#                             'pnl': pnl,
#                             'exit_reason': 'TARGET'
#                         })
#                         positions.remove(pos)
#                 else:  # SHORT
#                     if current_price >= pos['stop_loss']:
#                         pnl = (pos['entry_price'] - current_price) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append({
#                             'entry_time': pos['entry_time'],
#                             'exit_time': current_time,
#                             'action': 'SHORT',
#                             'entry_price': pos['entry_price'],
#                             'exit_price': current_price,
#                             'quantity': pos['quantity'],
#                             'pnl': pnl,
#                             'exit_reason': 'STOP_LOSS'
#                         })
#                         positions.remove(pos)
#                     elif current_price <= pos['target']:
#                         pnl = (pos['entry_price'] - current_price) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append({
#                             'entry_time': pos['entry_time'],
#                             'exit_time': current_time,
#                             'action': 'SHORT',
#                             'entry_price': pos['entry_price'],
#                             'exit_price': current_price,
#                             'quantity': pos['quantity'],
#                             'pnl': pnl,
#                             'exit_reason': 'TARGET'
#                         })
#                         positions.remove(pos)
            
#             # Enter new positions
#             if len(positions) == 0:
#                 atr_points = current_price * 0.02
                
#                 if signals.get('buy_call'):
#                     stop_loss = current_price - atr_points
#                     target = current_price + (atr_points * 3)
#                     risk = current_price - stop_loss
                    
#                     if risk > 0:
#                         risk_amount = capital * 0.01
#                         quantity = max(1, int(risk_amount / risk))
#                         margin = current_price * quantity * 0.2
                        
#                         if margin <= capital:
#                             capital -= margin
#                             positions.append({
#                                 'type': 'LONG',
#                                 'entry_price': current_price,
#                                 'entry_time': current_time,
#                                 'quantity': quantity,
#                                 'stop_loss': stop_loss,
#                                 'target': target,
#                                 'margin': margin
#                             })
#                             print(f"   📈 LONG entry: {quantity} @ ₹{current_price:.2f}")
                            
#                 elif signals.get('buy_put'):
#                     stop_loss = current_price + atr_points
#                     target = current_price - (atr_points * 3)
#                     risk = stop_loss - current_price
                    
#                     if risk > 0:
#                         risk_amount = capital * 0.01
#                         quantity = max(1, int(risk_amount / risk))
#                         margin = current_price * quantity * 0.2
                        
#                         if margin <= capital:
#                             capital -= margin
#                             positions.append({
#                                 'type': 'SHORT',
#                                 'entry_price': current_price,
#                                 'entry_time': current_time,
#                                 'quantity': quantity,
#                                 'stop_loss': stop_loss,
#                                 'target': target,
#                                 'margin': margin
#                             })
#                             print(f"   📉 SHORT entry: {quantity} @ ₹{current_price:.2f}")
            
#             # Track equity curve
#             current_equity = capital
#             for pos in positions:
#                 if pos['type'] == 'LONG':
#                     current_equity += (current_price - pos['entry_price']) * pos['quantity']
#                 else:
#                     current_equity += (pos['entry_price'] - current_price) * pos['quantity']
            
#             equity_curve.append({'time': current_time, 'equity': current_equity})
            
#             # Track drawdown
#             if current_equity > peak_capital:
#                 peak_capital = current_equity
#             dd = (peak_capital - current_equity) / peak_capital * 100 if peak_capital > 0 else 0
#             if dd > max_drawdown:
#                 max_drawdown = dd
        
#         # Calculate metrics
#         metrics = self.calculate_metrics(trades, equity_curve, max_drawdown)
        
#         print(f"\n{'='*60}")
#         print(f"📊 BACKTEST RESULTS: {strategy.get_strategy_name()}")
#         print(f"{'='*60}")
#         print(f"   Total Trades: {metrics['total_trades']}")
#         print(f"   Win Rate: {metrics['win_rate']:.1f}%")
#         print(f"   Total P&L: ₹{metrics['total_pnl']:,.2f}")
#         print(f"   Total Return: {metrics['total_return']:.2f}%")
#         print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
#         print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
#         print(f"{'='*60}\n")
        
#         return {
#             'strategy': strategy.get_strategy_name(),
#             'metrics': metrics,
#             'trades': trades[-50:],
#             'equity_curve': equity_curve
#         }
    
#     def calculate_metrics(self, trades, equity_curve, max_drawdown):
#         if not trades:
#             return {
#                 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0,
#                 'total_return': 0, 'max_drawdown': 0, 'sharpe_ratio': 0
#             }
        
#         pnls = [t['pnl'] for t in trades]
#         winning = [p for p in pnls if p > 0]
#         losing = [p for p in pnls if p < 0]
        
#         total_pnl = sum(pnls)
#         win_rate = (len(winning) / len(trades) * 100) if trades else 0
        
#         gross_profit = sum(winning) if winning else 0
#         gross_loss = abs(sum(losing)) if losing else 1
#         profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
#         total_return = ((equity_curve[-1]['equity'] - self.initial_capital) / 
#                        self.initial_capital * 100) if equity_curve else 0
        
#         # Calculate Sharpe ratio
#         returns = []
#         for i in range(1, len(equity_curve)):
#             if equity_curve[i-1]['equity'] != 0:
#                 ret = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
#                 returns.append(ret)
        
#         sharpe = 0
#         if len(returns) > 1 and np.std(returns) > 0:
#             sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
        
#         return {
#             'total_trades': len(trades),
#             'winning_trades': len(winning),
#             'losing_trades': len(trades) - len(winning),
#             'win_rate': round(win_rate, 2),
#             'total_pnl': round(total_pnl, 2),
#             'total_return': round(total_return, 2),
#             'profit_factor': round(profit_factor, 2),
#             'max_drawdown': round(max_drawdown, 2),
#             'sharpe_ratio': round(sharpe, 2),
#             'best_trade': round(max(pnls), 2) if pnls else 0,
#             'worst_trade': round(min(pnls), 2) if pnls else 0,
#             'final_equity': round(equity_curve[-1]['equity'], 2) if equity_curve else self.initial_capital
#         }
    
#     def compare_all_strategies(self, data):
#         """Run backtest for all strategies and compare"""
#         print("\n" + "="*60)
#         print("📊 COMPARING ALL STRATEGIES")
#         print("="*60)
        
#         results = {}
#         for strategy_name in self.strategies.keys():
#             result = self.run_backtest(data, strategy_name)
#             if result:
#                 results[strategy_name] = result['metrics']
        
#         if not results:
#             print("❌ No results to compare")
#             return None
        
#         # Create comparison DataFrame
#         df = pd.DataFrame(results).T
#         df = df.sort_values('total_pnl', ascending=False)
        
#         print("\n📊 STRATEGY COMPARISON TABLE")
#         print("="*90)
#         print(f"{'Strategy':<20} {'Trades':>8} {'Win Rate':>10} {'Total P&L':>14} {'Return %':>10} {'Sharpe':>8} {'Max DD%':>8}")
#         print("-"*90)
        
#         for idx, row in df.iterrows():
#             print(f"{idx:<20} {row['total_trades']:>8} {row['win_rate']:>9.1f}% ₹{row['total_pnl']:>11,.2f} {row['total_return']:>9.2f}% {row['sharpe_ratio']:>7.2f} {row['max_drawdown']:>7.1f}%")
        
#         print("="*90)
        
#         # Find best strategy
#         best = df.iloc[0]
#         print(f"\n🏆 BEST STRATEGY: {df.index[0]}")
#         print(f"   Total P&L: ₹{best['total_pnl']:,.2f}")
#         print(f"   Win Rate: {best['win_rate']:.1f}%")
#         print(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
        
#         return df

# # ============================================
# # MAIN EXECUTION
# # ============================================

# if __name__ == "__main__":
#     # Your actual data path
#     BASE_FOLDER = r"E:\siddesh\Trading\Sublime\code\Test\option\trading_bot_V_1\NIFTY"
    
#     print("="*60)
#     print("🚀 STRATEGY BACKTEST ENGINE (Fixed for pandas compatibility)")
#     print("="*60)
    
#     # Load data from nested folders
#     raw_data = load_nested_csv_data(BASE_FOLDER)
    
#     if raw_data is not None and len(raw_data) > 100:
#         # Initialize engine
#         engine = BacktestEngine(initial_capital=100000)
        
#         # Prepare data (resample to 15-minute timeframe)
#         data = engine.prepare_data(raw_data, timeframe_minutes=15)
        
#         if data is not None and len(data) > 50:
#             print("\n" + "="*60)
#             print("📌 Select an option:")
#             print("1. Run single strategy")
#             print("2. Compare all strategies")
#             print("="*60)
            
#             choice = input("\nEnter choice (1 or 2): ").strip()
            
#             if choice == "1":
#                 print("\nAvailable strategies:")
#                 strategies_list = list(engine.strategies.keys())
#                 for i, name in enumerate(strategies_list, 1):
#                     print(f"   {i}. {name}")
                
#                 try:
#                     strat_choice = int(input("Select strategy number: ")) - 1
#                     if 0 <= strat_choice < len(strategies_list):
#                         strategy_name = strategies_list[strat_choice]
#                         result = engine.run_backtest(data, strategy_name)
                        
#                         if result:
#                             # Save results to CSV
#                             trades_df = pd.DataFrame(result['trades'])
#                             trades_df.to_csv(f"backtest_{strategy_name}.csv", index=False)
#                             print(f"\n✅ Results saved to backtest_{strategy_name}.csv")
#                     else:
#                         print("❌ Invalid choice")
#                 except ValueError:
#                     print("❌ Please enter a number")
            
#             elif choice == "2":
#                 comparison = engine.compare_all_strategies(data)
#                 if comparison is not None:
#                     comparison.to_csv("strategy_comparison.csv")
#                     print(f"\n✅ Comparison saved to strategy_comparison.csv")
#             else:
#                 print("❌ Invalid choice. Please enter 1 or 2.")
#         else:
#             print("❌ Insufficient data after resampling")
#     else:
#         print("❌ No data loaded. Please check the folder path.")
#         print(f"   Path: {BASE_FOLDER}")






###############################################################################################################################




# # master_backtest.py - Universal Backtest for ALL Strategies
# import pandas as pd
# import numpy as np
# import talib
# import glob
# import os
# import sys
# from datetime import datetime
# from typing import Dict, Any, List
# import warnings
# warnings.filterwarnings('ignore')

# # ============================================
# # ALL STRATEGIES - Auto-loaded from your strategies folder
# # ============================================

# # Import all strategies dynamically
# from strategies import (
#     EMA_RSI_Strategy,
#     MACD_Bollinger_Strategy,
#     RSI_50_Crossover,
#     VWAP_Strategy,
#     MovingAverageCrossover,
#     OpeningRangeBreakout,
#     SupertrendStrategy,
#     StochasticRSI_Strategy,
#     IchimokuStrategy,
#     PriceActionStrategy,
#     TripleEMA_ADX_Strategy,
#     SMC_FairValueGap,
#     SMC_LiquiditySweep,
#     SMC_OrderBlock_BOS,
# )

# # Strategy registry with display names
# STRATEGY_REGISTRY = {
#     # Existing strategies
#     'EMA_RSI': EMA_RSI_Strategy,
#     'MACD_Bollinger': MACD_Bollinger_Strategy,
#     'RSI_50_Crossover': RSI_50_Crossover,
#     'VWAP_Reversion': VWAP_Strategy,
#     'MA_Crossover_50_200': MovingAverageCrossover,
#     'ORB_30min': OpeningRangeBreakout,
#     # New strategies
#     'Supertrend_RSI': SupertrendStrategy,
#     'StochasticRSI_MACD': StochasticRSI_Strategy,
#     'Ichimoku_Cloud': IchimokuStrategy,
#     'PriceAction_Engulfing_PinBar': PriceActionStrategy,
#     'TripleEMA_ADX': TripleEMA_ADX_Strategy,
#     'SMC_FairValueGap': SMC_FairValueGap,
#     'SMC_LiquiditySweep': SMC_LiquiditySweep,
#     'SMC_OrderBlock_BOS': SMC_OrderBlock_BOS,
# }

# # Strategy display names for reports
# STRATEGY_NAMES = {
#     'EMA_RSI': '📊 EMA/RSI Strategy',
#     'MACD_Bollinger': '📈 MACD + Bollinger Bands',
#     'RSI_50_Crossover': '⚡ RSI 50 Crossover',
#     'VWAP_Reversion': '🔄 VWAP Mean Reversion',
#     'MA_Crossover_50_200': '📉 MA Crossover (50/200)',
#     'ORB_30min': '🎯 Opening Range Breakout',
#     'Supertrend_RSI': '🔷 Supertrend + RSI',
#     'StochasticRSI_MACD': '🌀 Stochastic RSI + MACD',
#     'Ichimoku_Cloud': '☁️ Ichimoku Cloud Breakout',
#     'PriceAction_Engulfing_PinBar': '🕯️ Price Action (Engulfing/Pin Bar)',
#     'TripleEMA_ADX': '📊 Triple EMA + ADX',
#     'SMC_FairValueGap': '🎯 SMC - Fair Value Gap (FVG)',
#     'SMC_LiquiditySweep': '🔍 SMC - Liquidity Sweep',
#     'SMC_OrderBlock_BOS': '🏛️ SMC - Order Block + BOS',
# }

# # ============================================
# # DATA LOADER - Works with your nested folder structure
# # ============================================

# def load_market_data(base_folder: str, symbol: str = "NIFTY", 
#                      start_date: str = None, end_date: str = None,
#                      timeframe_minutes: int = 15) -> pd.DataFrame:
#     """
#     Load all CSV data from nested folders and resample to desired timeframe
#     """
#     print(f"\n📂 Loading data from: {base_folder}")
    
#     if not os.path.exists(base_folder):
#         print(f"❌ Folder not found: {base_folder}")
#         return None
    
#     # Find all CSV files recursively
#     all_files = []
#     for root, dirs, files in os.walk(base_folder):
#         for file in files:
#             if file.endswith('.csv'):
#                 all_files.append(os.path.join(root, file))
    
#     print(f"✅ Found {len(all_files)} CSV files")
    
#     if not all_files:
#         return None
    
#     dfs = []
    
#     for file_path in all_files:
#         try:
#             df = pd.read_csv(file_path)
            
#             # Find datetime column
#             datetime_col = None
#             for col in df.columns:
#                 col_lower = col.lower()
#                 if 'time' in col_lower or 'date' in col_lower or 'datetime' in col_lower:
#                     datetime_col = col
#                     break
            
#             if datetime_col:
#                 df['datetime'] = pd.to_datetime(df[datetime_col], errors='coerce')
#             else:
#                 # Try to extract date from folder name
#                 folder_name = os.path.basename(os.path.dirname(file_path))
#                 try:
#                     date = pd.to_datetime(folder_name, errors='coerce')
#                     if pd.notna(date):
#                         df['datetime'] = date
#                     else:
#                         mod_time = os.path.getmtime(file_path)
#                         df['datetime'] = pd.to_datetime(mod_time, unit='s')
#                 except:
#                     mod_time = os.path.getmtime(file_path)
#                     df['datetime'] = pd.to_datetime(mod_time, unit='s')
            
#             df = df.dropna(subset=['datetime'])
#             if len(df) == 0:
#                 continue
            
#             df.set_index('datetime', inplace=True)
#             df.sort_index(inplace=True)
            
#             # Standardize column names
#             column_map = {
#                 'Open': 'open', 'OPEN': 'open', 'open': 'open',
#                 'High': 'high', 'HIGH': 'high', 'high': 'high',
#                 'Low': 'low', 'LOW': 'low', 'low': 'low',
#                 'Close': 'close', 'CLOSE': 'close', 'close': 'close',
#                 'Volume': 'volume', 'VOLUME': 'volume', 'volume': 'volume',
#                 'LTP': 'close', 'ltp': 'close'
#             }
#             df.rename(columns=column_map, inplace=True)
            
#             dfs.append(df)
            
#         except Exception as e:
#             print(f"⚠️ Error loading {os.path.basename(file_path)}: {e}")
    
#     if not dfs:
#         print("❌ No data loaded")
#         return None
    
#     # Combine all data
#     data = pd.concat(dfs)
#     data = data[~data.index.duplicated(keep='first')]
#     data.sort_index(inplace=True)
    
#     # Filter by date range
#     if start_date:
#         data = data[data.index >= pd.to_datetime(start_date)]
#     if end_date:
#         data = data[data.index <= pd.to_datetime(end_date)]
    
#     print(f"📊 Raw data: {len(data)} rows from {data.index[0]} to {data.index[-1]}")
    
#     # Resample to timeframe
#     if timeframe_minutes > 0:
#         rule = f'{timeframe_minutes}min'
#         try:
#             resampled = data.resample(rule).agg({
#                 'open': 'first',
#                 'high': 'max',
#                 'low': 'min',
#                 'close': 'last',
#                 'volume': 'sum'
#             }).dropna()
#             print(f"📊 Resampled to {timeframe_minutes}min: {len(resampled)} candles")
#             return resampled
#         except Exception as e:
#             print(f"⚠️ Resampling failed: {e}, using original data")
#             return data
    
#     return data

# # ============================================
# # BACKTEST ENGINE
# # ============================================

# class UniversalBacktestEngine:
#     def __init__(self, initial_capital: float = 100000, 
#                  risk_per_trade: float = 0.01,
#                  risk_reward_ratio: float = 3):
#         self.initial_capital = initial_capital
#         self.risk_per_trade = risk_per_trade
#         self.risk_reward_ratio = risk_reward_ratio
    
#     def run_backtest(self, data: pd.DataFrame, strategy, 
#                      strategy_name: str) -> Dict:
#         """
#         Run backtest for a single strategy
#         """
#         print(f"\n{'='*60}")
#         print(f"📊 Testing: {STRATEGY_NAMES.get(strategy_name, strategy_name)}")
#         print(f"{'='*60}")
        
#         capital = self.initial_capital
#         positions = []
#         trades = []
#         equity_curve = []
#         peak_capital = self.initial_capital
#         max_drawdown = 0
        
#         # Calculate indicators
#         try:
#             strategy.calculate_indicators(data)
#         except Exception as e:
#             print(f"⚠️ Indicator calculation error: {e}")
#             return None
        
#         for i in range(max(100, len(data) // 10), len(data)):
#             current_data = data.iloc[:i+1].copy()
#             current_price = data['close'].iloc[i]
#             current_time = data.index[i]
            
#             # Generate signals
#             try:
#                 signals = strategy.generate_signals(current_data, "NIFTY")
#             except Exception as e:
#                 signals = {'buy_call': False, 'buy_put': False}
            
#             # Check existing positions
#             for pos in positions[:]:
#                 if pos['type'] == 'LONG':
#                     if current_price <= pos['stop_loss']:
#                         pnl = (current_price - pos['entry_price']) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append(self._create_trade_record(pos, current_price, current_time, pnl, 'STOP_LOSS'))
#                         positions.remove(pos)
#                     elif current_price >= pos['target']:
#                         pnl = (current_price - pos['entry_price']) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append(self._create_trade_record(pos, current_price, current_time, pnl, 'TARGET'))
#                         positions.remove(pos)
#                 else:  # SHORT
#                     if current_price >= pos['stop_loss']:
#                         pnl = (pos['entry_price'] - current_price) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append(self._create_trade_record(pos, current_price, current_time, pnl, 'STOP_LOSS'))
#                         positions.remove(pos)
#                     elif current_price <= pos['target']:
#                         pnl = (pos['entry_price'] - current_price) * pos['quantity']
#                         capital += pos['margin'] + pnl
#                         trades.append(self._create_trade_record(pos, current_price, current_time, pnl, 'TARGET'))
#                         positions.remove(pos)
            
#             # Enter new positions
#             if len(positions) == 0:
#                 atr_points = self._calculate_atr(data, i) * 2
#                 if atr_points <= 0:
#                     atr_points = current_price * 0.01
                
#                 if signals.get('buy_call'):
#                     stop_loss = current_price - atr_points
#                     target = current_price + (atr_points * self.risk_reward_ratio)
#                     risk = current_price - stop_loss
                    
#                     if risk > 0:
#                         risk_amount = capital * self.risk_per_trade
#                         quantity = max(1, int(risk_amount / risk))
#                         margin = current_price * quantity * 0.2
                        
#                         if margin <= capital:
#                             capital -= margin
#                             positions.append({
#                                 'type': 'LONG',
#                                 'entry_price': current_price,
#                                 'entry_time': current_time,
#                                 'quantity': quantity,
#                                 'stop_loss': stop_loss,
#                                 'target': target,
#                                 'margin': margin,
#                                 'strategy': strategy_name
#                             })
#                             print(f"   📈 LONG: {quantity} @ ₹{current_price:.2f} (SL: ₹{stop_loss:.2f}, Target: ₹{target:.2f})")
                            
#                 elif signals.get('buy_put'):
#                     stop_loss = current_price + atr_points
#                     target = current_price - (atr_points * self.risk_reward_ratio)
#                     risk = stop_loss - current_price
                    
#                     if risk > 0:
#                         risk_amount = capital * self.risk_per_trade
#                         quantity = max(1, int(risk_amount / risk))
#                         margin = current_price * quantity * 0.2
                        
#                         if margin <= capital:
#                             capital -= margin
#                             positions.append({
#                                 'type': 'SHORT',
#                                 'entry_price': current_price,
#                                 'entry_time': current_time,
#                                 'quantity': quantity,
#                                 'stop_loss': stop_loss,
#                                 'target': target,
#                                 'margin': margin,
#                                 'strategy': strategy_name
#                             })
#                             print(f"   📉 SHORT: {quantity} @ ₹{current_price:.2f} (SL: ₹{stop_loss:.2f}, Target: ₹{target:.2f})")
            
#             # Track equity curve
#             current_equity = capital
#             for pos in positions:
#                 if pos['type'] == 'LONG':
#                     current_equity += (current_price - pos['entry_price']) * pos['quantity']
#                 else:
#                     current_equity += (pos['entry_price'] - current_price) * pos['quantity']
            
#             equity_curve.append({'time': current_time, 'equity': current_equity})
            
#             # Track drawdown
#             if current_equity > peak_capital:
#                 peak_capital = current_equity
#             dd = (peak_capital - current_equity) / peak_capital * 100 if peak_capital > 0 else 0
#             if dd > max_drawdown:
#                 max_drawdown = dd
        
#         metrics = self._calculate_metrics(trades, equity_curve, max_drawdown)
        
#         print(f"\n   Results: {metrics['total_trades']} trades | Win Rate: {metrics['win_rate']:.1f}% | P&L: ₹{metrics['total_pnl']:,.2f}")
        
#         return {
#             'strategy': strategy_name,
#             'display_name': STRATEGY_NAMES.get(strategy_name, strategy_name),
#             'metrics': metrics,
#             'trades': trades[-50:],
#             'equity_curve': equity_curve
#         }
    
#     def _calculate_atr(self, data: pd.DataFrame, index: int, period: int = 14) -> float:
#         """Calculate ATR at given index"""
#         if index < period:
#             return 0
#         try:
#             high = data['high'].iloc[index-period:index+1]
#             low = data['low'].iloc[index-period:index+1]
#             close = data['close'].iloc[index-period:index+1]
            
#             tr1 = high - low
#             tr2 = abs(high - close.shift())
#             tr3 = abs(low - close.shift())
#             tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
#             atr = tr.rolling(window=period).mean().iloc[-1]
#             return atr if not pd.isna(atr) else 0
#         except:
#             return 0
    
#     def _create_trade_record(self, pos, exit_price, exit_time, pnl, reason):
#         return {
#             'entry_time': pos['entry_time'],
#             'exit_time': exit_time,
#             'type': pos['type'],
#             'entry_price': pos['entry_price'],
#             'exit_price': exit_price,
#             'quantity': pos['quantity'],
#             'pnl': pnl,
#             'exit_reason': reason,
#             'strategy': pos['strategy']
#         }
    
#     def _calculate_metrics(self, trades, equity_curve, max_drawdown):
#         if not trades:
#             return {
#                 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0,
#                 'total_return': 0, 'max_drawdown': 0, 'profit_factor': 0,
#                 'sharpe_ratio': 0, 'avg_win': 0, 'avg_loss': 0,
#                 'best_trade': 0, 'worst_trade': 0
#             }
        
#         pnls = [t['pnl'] for t in trades]
#         winning = [p for p in pnls if p > 0]
#         losing = [p for p in pnls if p < 0]
        
#         total_pnl = sum(pnls)
#         win_rate = (len(winning) / len(trades) * 100) if trades else 0
        
#         gross_profit = sum(winning) if winning else 0
#         gross_loss = abs(sum(losing)) if losing else 1
#         profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
#         total_return = ((equity_curve[-1]['equity'] - self.initial_capital) / 
#                        self.initial_capital * 100) if equity_curve else 0
        
#         # Sharpe ratio
#         returns = []
#         for i in range(1, len(equity_curve)):
#             if equity_curve[i-1]['equity'] != 0:
#                 ret = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
#                 returns.append(ret)
        
#         sharpe = 0
#         if len(returns) > 1 and np.std(returns) > 0:
#             sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
        
#         return {
#             'total_trades': len(trades),
#             'winning_trades': len(winning),
#             'losing_trades': len(trades) - len(winning),
#             'win_rate': round(win_rate, 2),
#             'total_pnl': round(total_pnl, 2),
#             'total_return': round(total_return, 2),
#             'profit_factor': round(profit_factor, 2),
#             'max_drawdown': round(max_drawdown, 2),
#             'sharpe_ratio': round(sharpe, 2),
#             'avg_win': round(sum(winning) / len(winning), 2) if winning else 0,
#             'avg_loss': round(abs(sum(losing) / len(losing)), 2) if losing else 0,
#             'best_trade': round(max(pnls), 2) if pnls else 0,
#             'worst_trade': round(min(pnls), 2) if pnls else 0,
#             'final_equity': round(equity_curve[-1]['equity'], 2) if equity_curve else self.initial_capital
#         }

# # ============================================
# # RUN COMPLETE ANALYSIS
# # ============================================

# def run_complete_backtest():
#     # Configuration
#     DATA_FOLDER = r"E:\siddesh\Trading\Sublime\code\Test\option\trading_bot_V_1\NIFTY"
#     TIMEFRAME_MINUTES = 15
#     INITIAL_CAPITAL = 100000
#     RISK_PER_TRADE = 0.01  # 1% risk per trade
#     RISK_REWARD = 3  # 1:3 risk reward
    
#     print("="*80)
#     print("🚀 MASTER BACKTEST ENGINE - TESTING ALL STRATEGIES")
#     print("="*80)
#     print(f"   Data Folder: {DATA_FOLDER}")
#     print(f"   Timeframe: {TIMEFRAME_MINUTES} minutes")
#     print(f"   Initial Capital: ₹{INITIAL_CAPITAL:,.2f}")
#     print(f"   Risk per Trade: {RISK_PER_TRADE*100}%")
#     print(f"   Risk/Reward: 1:{RISK_REWARD}")
#     print("="*80)
    
#     # Load data
#     data = load_market_data(DATA_FOLDER, timeframe_minutes=TIMEFRAME_MINUTES)
    
#     if data is None or len(data) < 100:
#         print("❌ Insufficient data for backtest")
#         return
    
#     print(f"\n✅ Data ready: {len(data)} candles")
    
#     # Initialize engine
#     engine = UniversalBacktestEngine(
#         initial_capital=INITIAL_CAPITAL,
#         risk_per_trade=RISK_PER_TRADE,
#         risk_reward_ratio=RISK_REWARD
#     )
    
#     # Run backtest for all strategies
#     results = {}
    
#     for strategy_key, strategy_class in STRATEGY_REGISTRY.items():
#         try:
#             strategy = strategy_class()
#             result = engine.run_backtest(data, strategy, strategy_key)
#             if result and result['metrics']['total_trades'] > 0:
#                 results[strategy_key] = result
#         except Exception as e:
#             print(f"⚠️ {strategy_key} failed: {e}")
    
#     # Print comparison table
#     print("\n" + "="*100)
#     print("📊 STRATEGY COMPARISON REPORT")
#     print("="*100)
    
#     # Create comparison DataFrame
#     comparison_data = []
#     for key, result in results.items():
#         m = result['metrics']
#         comparison_data.append({
#             'Strategy': result['display_name'],
#             'Trades': m['total_trades'],
#             'Win Rate %': m['win_rate'],
#             'Total P&L (₹)': m['total_pnl'],
#             'Return %': m['total_return'],
#             'Profit Factor': m['profit_factor'],
#             'Sharpe': m['sharpe_ratio'],
#             'Max DD %': m['max_drawdown'],
#             'Avg Win (₹)': m['avg_win'],
#             'Avg Loss (₹)': m['avg_loss']
#         })
    
#     df = pd.DataFrame(comparison_data)
#     df = df.sort_values('Total P&L (₹)', ascending=False)
    
#     # Print table
#     print("\n" + df.to_string(index=False))
    
#     # Save to CSV
#     df.to_csv('strategy_backtest_results.csv', index=False)
#     print(f"\n✅ Results saved to: strategy_backtest_results.csv")
    
#     # Print best strategy
#     if not df.empty:
#         best = df.iloc[0]
#         print("\n" + "="*80)
#         print(f"🏆 BEST PERFORMING STRATEGY: {best['Strategy']}")
#         print("="*80)
#         print(f"   Total Trades: {best['Trades']}")
#         print(f"   Win Rate: {best['Win Rate %']}%")
#         print(f"   Total P&L: ₹{best['Total P&L (₹)']:,.2f}")
#         print(f"   Return: {best['Return %']}%")
#         print(f"   Profit Factor: {best['Profit Factor']}")
#         print(f"   Sharpe Ratio: {best['Sharpe']}")
#         print(f"   Max Drawdown: {best['Max DD %']}%")
#         print("="*80)
    
#     # Also save detailed results for each strategy
#     for key, result in results.items():
#         trades_df = pd.DataFrame(result['trades'])
#         if not trades_df.empty:
#             trades_df.to_csv(f'backtest_{key}.csv', index=False)
#             print(f"   📁 Saved: backtest_{key}.csv")
    
#     return results, df

# # ============================================
# # MAIN
# # ============================================

# if __name__ == "__main__":
#     results, comparison = run_complete_backtest()










########################################################################################################################################################











# # option_backtest_complete.py - Complete Option Backtest for Your Data Structure
# import os
# import pandas as pd
# import numpy as np
# import glob
# from datetime import datetime
# import warnings
# warnings.filterwarnings('ignore')

# # ============================================
# # DATA LOADER FOR OPTION CHAIN DATA
# # ============================================

# class OptionDataLoader:
#     def __init__(self, base_folder):
#         self.base_folder = base_folder
    
#     def load_all_option_data(self, start_date=None, end_date=None):
#         """Load all option chain data from nested folders"""
#         print(f"\n📂 Loading option data from: {self.base_folder}")
        
#         if not os.path.exists(self.base_folder):
#             print(f"❌ Folder not found")
#             return None
        
#         # Find all date folders
#         date_folders = []
#         for item in os.listdir(self.base_folder):
#             item_path = os.path.join(self.base_folder, item)
#             if os.path.isdir(item_path):
#                 try:
#                     # Try to parse as date
#                     date = datetime.strptime(item, '%Y-%m-%d')
#                     date_folders.append((item, date))
#                 except:
#                     pass
        
#         date_folders.sort(key=lambda x: x[1])
#         print(f"✅ Found {len(date_folders)} date folders")
        
#         # For each date, load all strike data
#         all_data = []
        
#         for folder_name, folder_date in date_folders:
#             if start_date and folder_date < datetime.strptime(start_date, '%Y-%m-%d'):
#                 continue
#             if end_date and folder_date > datetime.strptime(end_date, '%Y-%m-%d'):
#                 continue
            
#             date_data = self._load_date_data(folder_name, folder_date)
#             if date_data is not None and len(date_data) > 0:  # Fixed: check length instead of truth value
#                 all_data.append(date_data)
#                 print(f"   Loaded {folder_name}: {len(date_data)} records")
        
#         if not all_data:
#             print("❌ No data loaded")
#             return None
        
#         # Combine all data
#         combined = pd.concat(all_data, ignore_index=True)
        
#         # Sort by timestamp
#         if 'timestamp' in combined.columns:
#             combined.sort_values('timestamp', inplace=True)
        
#         print(f"\n📊 Total loaded: {len(combined)} records")
#         if len(combined) > 0:
#             print(f"   Date range: {combined['timestamp'].min()} to {combined['timestamp'].max()}")
        
#         return combined
    
#     def _load_date_data(self, date_folder, date):
#         """Load all strikes for a single date"""
#         date_path = os.path.join(self.base_folder, date_folder)
        
#         # Find all strike folders (ATM, ATM+1, ATM-1, etc.)
#         strike_folders = []
#         for item in os.listdir(date_path):
#             item_path = os.path.join(date_path, item)
#             if os.path.isdir(item_path):
#                 strike_folders.append((item, item_path))
        
#         if not strike_folders:
#             return None
        
#         strike_data = []
        
#         for strike_name, strike_path in strike_folders:
#             # Parse strike offset
#             if strike_name == 'ATM':
#                 strike_offset = 0
#             elif strike_name.startswith('ATM+'):
#                 try:
#                     strike_offset = int(strike_name.replace('ATM+', ''))
#                 except:
#                     strike_offset = 0
#             elif strike_name.startswith('ATM-'):
#                 try:
#                     strike_offset = -int(strike_name.replace('ATM-', ''))
#                 except:
#                     strike_offset = 0
#             else:
#                 continue
            
#             # Load CALL data
#             call_file = os.path.join(strike_path, f'NIFTY_{date_folder}_CALL.csv')
#             put_file = os.path.join(strike_path, f'NIFTY_{date_folder}_PUT.csv')
            
#             if os.path.exists(call_file):
#                 try:
#                     call_df = pd.read_csv(call_file)
#                     call_df['option_type'] = 'CALL'
#                     call_df['strike_offset'] = strike_offset
#                     call_df['trade_date'] = date
#                     strike_data.append(call_df)
#                 except Exception as e:
#                     print(f"   Warning: Could not read {call_file}: {e}")
            
#             if os.path.exists(put_file):
#                 try:
#                     put_df = pd.read_csv(put_file)
#                     put_df['option_type'] = 'PUT'
#                     put_df['strike_offset'] = strike_offset
#                     put_df['trade_date'] = date
#                     strike_data.append(put_df)
#                 except Exception as e:
#                     print(f"   Warning: Could not read {put_file}: {e}")
        
#         if not strike_data:
#             return None
        
#         df = pd.concat(strike_data, ignore_index=True)
        
#         # Parse datetime - handle different column names
#         if 'datetime' in df.columns:
#             df['timestamp'] = pd.to_datetime(df['datetime'])
#         elif 'time' in df.columns:
#             df['timestamp'] = pd.to_datetime(df['time'])
#         elif 'Date' in df.columns:
#             df['timestamp'] = pd.to_datetime(df['Date'])
#         else:
#             # Create timestamp from date and time if available
#             if 'date' in df.columns and 'time' in df.columns:
#                 df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
#             else:
#                 # Use the folder date
#                 df['timestamp'] = pd.Timestamp(date)
        
#         return df

# # ============================================
# # OPTION BACKTEST ENGINE
# # ============================================

# class OptionBacktestEngine:
#     def __init__(self, initial_capital=100000, risk_per_trade=0.01, 
#                  sl_percent=0.30, target_percent=1.5, max_lots=2):
#         self.initial_capital = initial_capital
#         self.risk_per_trade = risk_per_trade
#         self.sl_percent = sl_percent
#         self.target_percent = target_percent
#         self.max_lots = max_lots
#         self.lot_sizes = {'NIFTY': 50, 'BANKNIFTY': 25, 'FINNIFTY': 40}
    
#     def run_backtest(self, data, strategy_name="Option_Strategy"):
#         """Run backtest on option chain data"""
        
#         print(f"\n{'='*60}")
#         print(f"📊 OPTION BACKTEST: {strategy_name}")
#         print(f"{'='*60}")
        
#         capital = self.initial_capital
#         positions = []
#         trades = []
#         equity_curve = []
#         peak_capital = self.initial_capital
#         max_drawdown = 0
        
#         # Sort by timestamp
#         if 'timestamp' in data.columns:
#             data = data.sort_values('timestamp')
#             unique_times = data['timestamp'].unique()
#         else:
#             unique_times = data.index.unique() if hasattr(data, 'index') else range(len(data))
        
#         for current_time in unique_times:
#             # Get data for this timestamp
#             if 'timestamp' in data.columns:
#                 group = data[data['timestamp'] == current_time]
#             else:
#                 group = data.loc[current_time] if hasattr(data, 'loc') else data
            
#             if len(group) == 0:
#                 continue
            
#             # Get ATM data for current timestamp
#             atm_data = group[group['strike_offset'] == 0]
            
#             # Get spot price from ATM data
#             spot_price = 0
#             if not atm_data.empty:
#                 if 'spot' in atm_data.columns:
#                     spot_price = atm_data['spot'].iloc[0]
#                 elif 'strike' in atm_data.columns:
#                     spot_price = atm_data['strike'].iloc[0]
#                 elif 'close' in atm_data.columns:
#                     spot_price = atm_data['close'].iloc[0]
            
#             # Get premiums for different strikes
#             call_premiums = {}
#             put_premiums = {}
            
#             for _, row in group.iterrows():
#                 strike_offset = row.get('strike_offset', 0)
#                 option_type = row.get('option_type', '')
                
#                 # Get premium (close price or LTP)
#                 premium = 0
#                 if 'close' in row:
#                     premium = float(row['close']) if pd.notna(row['close']) else 0
#                 elif 'ltp' in row:
#                     premium = float(row['ltp']) if pd.notna(row['ltp']) else 0
                
#                 if option_type == 'CALL':
#                     call_premiums[strike_offset] = premium
#                 elif option_type == 'PUT':
#                     put_premiums[strike_offset] = premium
            
#             # Check existing positions
#             for pos in positions[:]:
#                 # Get current premium
#                 if pos['option_type'] == 'CALL':
#                     current_premium = call_premiums.get(pos['strike_offset'], 0)
#                 else:
#                     current_premium = put_premiums.get(pos['strike_offset'], 0)
                
#                 if current_premium == 0:
#                     continue
                
#                 # Check stop loss
#                 if current_premium <= pos['stop_loss']:
#                     pnl = (current_premium - pos['entry_premium']) * pos['quantity']
#                     capital += pos['margin'] + pnl
                    
#                     trades.append({
#                         'entry_time': pos['entry_time'],
#                         'exit_time': current_time,
#                         'option_type': pos['option_type'],
#                         'strike_offset': pos['strike_offset'],
#                         'entry_premium': pos['entry_premium'],
#                         'exit_premium': current_premium,
#                         'pnl': pnl,
#                         'exit_reason': 'STOP_LOSS'
#                     })
#                     positions.remove(pos)
#                     print(f"   🔴 EXIT: {pos['option_type']} (Offset:{pos['strike_offset']}) @ ₹{current_premium:.2f} | P&L: ₹{pnl:+.2f}")
                    
#                 # Check target
#                 elif current_premium >= pos['target']:
#                     pnl = (current_premium - pos['entry_premium']) * pos['quantity']
#                     capital += pos['margin'] + pnl
                    
#                     trades.append({
#                         'entry_time': pos['entry_time'],
#                         'exit_time': current_time,
#                         'option_type': pos['option_type'],
#                         'strike_offset': pos['strike_offset'],
#                         'entry_premium': pos['entry_premium'],
#                         'exit_premium': current_premium,
#                         'pnl': pnl,
#                         'exit_reason': 'TARGET'
#                     })
#                     positions.remove(pos)
#                     print(f"   🟢 EXIT: {pos['option_type']} (Offset:{pos['strike_offset']}) @ ₹{current_premium:.2f} | P&L: ₹{pnl:+.2f}")
            
#             # Generate signal
#             if len(positions) == 0:
#                 signal = self._generate_signal(group, spot_price, call_premiums, put_premiums)
                
#                 if signal:
#                     option_type = signal['type']
#                     strike_offset = signal['strike_offset']
                    
#                     # Get premium
#                     if option_type == 'CALL':
#                         premium = call_premiums.get(strike_offset, 0)
#                     else:
#                         premium = put_premiums.get(strike_offset, 0)
                    
#                     if premium <= 0:
#                         continue
                    
#                     # Calculate lot size and position size
#                     lot_size = 50  # Default for NIFTY
#                     risk_amount = capital * self.risk_per_trade
#                     stop_loss = premium * (1 - self.sl_percent)
#                     target = premium * (1 + self.target_percent)
                    
#                     risk_per_lot = (premium - stop_loss) * lot_size
#                     if risk_per_lot > 0:
#                         max_lots_allowed = int(risk_amount / risk_per_lot)
#                         lots = min(max_lots_allowed, self.max_lots)
                        
#                         if lots > 0:
#                             quantity = lots * lot_size
#                             margin = premium * quantity
                            
#                             if margin <= capital:
#                                 capital -= margin
#                                 positions.append({
#                                     'option_type': option_type,
#                                     'strike_offset': strike_offset,
#                                     'entry_premium': premium,
#                                     'entry_time': current_time,
#                                     'quantity': quantity,
#                                     'lots': lots,
#                                     'stop_loss': stop_loss,
#                                     'target': target,
#                                     'margin': margin
#                                 })
#                                 print(f"   📈 ENTRY: {option_type} (Offset:{strike_offset}) @ ₹{premium:.2f} | Lots:{lots} | SL:₹{stop_loss:.2f} | TG:₹{target:.2f}")
            
#             # Track equity curve
#             current_equity = capital
#             for pos in positions:
#                 if pos['option_type'] == 'CALL':
#                     current_premium = call_premiums.get(pos['strike_offset'], pos['entry_premium'])
#                 else:
#                     current_premium = put_premiums.get(pos['strike_offset'], pos['entry_premium'])
#                 current_equity += (current_premium - pos['entry_premium']) * pos['quantity']
            
#             equity_curve.append({'time': current_time, 'equity': current_equity})
            
#             # Update drawdown
#             if current_equity > peak_capital:
#                 peak_capital = current_equity
#             dd = (peak_capital - current_equity) / peak_capital * 100 if peak_capital > 0 else 0
#             if dd > max_drawdown:
#                 max_drawdown = dd
        
#         # Calculate metrics
#         metrics = self._calculate_metrics(trades, equity_curve, max_drawdown)
        
#         print(f"\n{'='*60}")
#         print(f"📊 BACKTEST RESULTS")
#         print(f"{'='*60}")
#         print(f"   Total Trades: {metrics['total_trades']}")
#         print(f"   Win Rate: {metrics['win_rate']:.1f}%")
#         print(f"   Total P&L: ₹{metrics['total_pnl']:,.2f}")
#         print(f"   Total Return: {metrics['total_return']:.2f}%")
#         print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
#         print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
#         print(f"{'='*60}\n")
        
#         return {
#             'metrics': metrics,
#             'trades': trades,
#             'equity_curve': equity_curve
#         }
    
#     def _generate_signal(self, group, spot_price, call_premiums, put_premiums):
#         """Generate trading signal - Simple OTM strategy"""
        
#         # Check if we have ATM data
#         atm_call = call_premiums.get(0, 0)
#         atm_put = put_premiums.get(0, 0)
        
#         if atm_call == 0 and atm_put == 0:
#             return None
        
#         # Simple strategy: Buy 1 OTM Call if ATM Call premium is reasonable
#         otm_call = call_premiums.get(1, 0)
#         if otm_call > 0 and otm_call < 100:  # Only if premium is reasonable
#             return {'type': 'CALL', 'strike_offset': 1}
        
#         # Alternative: Buy 1 OTM Put
#         otm_put = put_premiums.get(1, 0)
#         if otm_put > 0 and otm_put < 100:
#             return {'type': 'PUT', 'strike_offset': 1}
        
#         return None
    
#     def _calculate_metrics(self, trades, equity_curve, max_drawdown):
#         if not trades:
#             return {
#                 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0,
#                 'total_return': 0, 'max_drawdown': 0, 'profit_factor': 0,
#                 'best_trade': 0, 'worst_trade': 0, 'final_equity': self.initial_capital
#             }
        
#         pnls = [t['pnl'] for t in trades]
#         winning = [p for p in pnls if p > 0]
#         losing = [p for p in pnls if p < 0]
        
#         total_pnl = sum(pnls)
#         win_rate = (len(winning) / len(trades) * 100) if trades else 0
        
#         gross_profit = sum(winning) if winning else 0
#         gross_loss = abs(sum(losing)) if losing else 1
#         profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
#         total_return = 0
#         final_equity = self.initial_capital
#         if equity_curve:
#             final_equity = equity_curve[-1]['equity']
#             total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
#         return {
#             'total_trades': len(trades),
#             'winning_trades': len(winning),
#             'losing_trades': len(trades) - len(winning),
#             'win_rate': round(win_rate, 2),
#             'total_pnl': round(total_pnl, 2),
#             'total_return': round(total_return, 2),
#             'profit_factor': round(profit_factor, 2),
#             'max_drawdown': round(max_drawdown, 2),
#             'best_trade': round(max(pnls), 2) if pnls else 0,
#             'worst_trade': round(min(pnls), 2) if pnls else 0,
#             'final_equity': round(final_equity, 2)
#         }

# # ============================================
# # MULTIPLE STRATEGY BACKTEST
# # ============================================

# def test_multiple_strategies(data):
#     """Test different option strategies"""
    
#     strategies = [
#         {'name': '1 OTM Call', 'type': 'CALL', 'offset': 1},
#         {'name': '2 OTM Call', 'type': 'CALL', 'offset': 2},
#         {'name': '1 OTM Put', 'type': 'PUT', 'offset': 1},
#         {'name': '2 OTM Put', 'type': 'PUT', 'offset': 2},
#         {'name': 'ATM Straddle', 'type': 'STRADDLE', 'offset': 0},
#     ]
    
#     results = []
    
#     for strategy in strategies:
#         print(f"\n{'='*50}")
#         print(f"Testing: {strategy['name']}")
#         print(f"{'='*50}")
        
#         engine = OptionBacktestEngine(
#             initial_capital=100000,
#             risk_per_trade=0.01,
#             sl_percent=0.30,
#             target_percent=1.5,
#             max_lots=2
#         )
        
#         # Modify signal generation for different strategies
#         original_generate = engine._generate_signal
        
#         if strategy['type'] == 'CALL':
#             engine._generate_signal = lambda g, s, cp, pp: {'type': 'CALL', 'strike_offset': strategy['offset']} if cp.get(strategy['offset'], 0) > 0 else None
#         elif strategy['type'] == 'PUT':
#             engine._generate_signal = lambda g, s, cp, pp: {'type': 'PUT', 'strike_offset': strategy['offset']} if pp.get(strategy['offset'], 0) > 0 else None
#         else:
#             engine._generate_signal = lambda g, s, cp, pp: {'type': 'CALL', 'strike_offset': 0} if cp.get(0, 0) > 0 else None
        
#         result = engine.run_backtest(data, strategy['name'])
        
#         if result:
#             metrics = result['metrics']
#             results.append({
#                 'Strategy': strategy['name'],
#                 'Trades': metrics['total_trades'],
#                 'Win Rate %': metrics['win_rate'],
#                 'Total P&L (₹)': metrics['total_pnl'],
#                 'Return %': metrics['total_return'],
#                 'Max DD %': metrics['max_drawdown'],
#                 'Profit Factor': metrics['profit_factor']
#             })
        
#         # Restore original
#         engine._generate_signal = original_generate
    
#     # Create comparison DataFrame
#     df = pd.DataFrame(results)
#     if not df.empty:
#         df = df.sort_values('Total P&L (₹)', ascending=False)
        
#         print("\n" + "="*80)
#         print("📊 STRATEGY COMPARISON")
#         print("="*80)
#         print(df.to_string(index=False))
        
#         # Save to CSV
#         df.to_csv('option_strategy_comparison.csv', index=False)
#         print(f"\n✅ Comparison saved to option_strategy_comparison.csv")
    
#     return df

# # ============================================
# # MAIN
# # ============================================

# if __name__ == "__main__":
#     DATA_FOLDER = r"E:\siddesh\Trading\Sublime\code\Test\option\trading_bot_V_1\NIFTY"
    
#     print("="*70)
#     print("🚀 OPTION BACKTEST ENGINE - COMPLETE VERSION")
#     print("="*70)
    
#     # Load data
#     loader = OptionDataLoader(DATA_FOLDER)
#     data = loader.load_all_option_data(start_date='2021-01-01', end_date='2021-12-31')
    
#     if data is None or len(data) == 0:
#         print("❌ No data loaded")
#         exit()
    
#     print(f"\n✅ Data loaded: {len(data)} records")
#     print(f"   Columns: {list(data.columns)}")
    
#     # Ask user what to do
#     print("\n" + "="*50)
#     print("Select an option:")
#     print("1. Run single strategy backtest")
#     print("2. Compare all strategies")
#     print("3. Quick data preview")
#     print("="*50)
    
#     choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
#     if choice == '1':
#         # Single strategy
#         engine = OptionBacktestEngine(
#             initial_capital=100000,
#             risk_per_trade=0.01,
#             sl_percent=0.30,
#             target_percent=1.5,
#             max_lots=2
#         )
#         results = engine.run_backtest(data, "OTM Call Strategy")
        
#         if results and results['trades']:
#             # Save trades
#             trades_df = pd.DataFrame(results['trades'])
#             trades_df.to_csv('option_backtest_trades.csv', index=False)
#             print(f"\n✅ Trades saved to option_backtest_trades.csv")
#             1
#             # Save equity curve
#             equity_df = pd.DataFrame(results['equity_curve'])
#             equity_df.to_csv('option_backtest_equity.csv', index=False)
#             print(f"✅ Equity curve saved to option_backtest_equity.csv")
    
#     elif choice == '2':
#         # Compare strategies
#         test_multiple_strategies(data)
    
#     elif choice == '3':
#         # Quick preview
#         print("\n📊 DATA PREVIEW:")
#         print(f"   Total records: {len(data)}")
#         print(f"   Columns: {list(data.columns)}")
#         print(f"\n   First 5 rows:")
#         print(data.head(10))
#         print(f"\n   Unique timestamps: {data['timestamp'].nunique() if 'timestamp' in data.columns else 'N/A'}")
#         print(f"   Option types: {data['option_type'].unique() if 'option_type' in data.columns else 'N/A'}")
#         print(f"   Strike offsets: {sorted(data['strike_offset'].unique()) if 'strike_offset' in data.columns else 'N/A'}")
    
#     else:
#         print("Invalid choice")



#######################################################################################################################################################################





# backtest_all_strategies_fixed.py - Fixed for your data structure
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================
# IMPORT YOUR STRATEGIES (only available ones)
# ============================================

STRATEGY_LIST = []

try:
    from strategies import EMA_RSI_Strategy
    STRATEGY_LIST.append({'class': EMA_RSI_Strategy, 'name': '📊 EMA/RSI', 'type': 'trend'})
except: pass

try:
    from strategies import MACD_Bollinger_Strategy
    STRATEGY_LIST.append({'class': MACD_Bollinger_Strategy, 'name': '📈 MACD+Bollinger', 'type': 'momentum'})
except: pass

try:
    from strategies import RSI_50_Crossover
    STRATEGY_LIST.append({'class': RSI_50_Crossover, 'name': '⚡ RSI 50 Crossover', 'type': 'momentum'})
except: pass

try:
    from strategies import VWAP_Strategy
    STRATEGY_LIST.append({'class': VWAP_Strategy, 'name': '🔄 VWAP Reversion', 'type': 'mean_reversion'})
except: pass

try:
    from strategies import MovingAverageCrossover
    STRATEGY_LIST.append({'class': MovingAverageCrossover, 'name': '📉 MA Crossover', 'type': 'trend'})
except: pass

try:
    from strategies import OpeningRangeBreakout
    STRATEGY_LIST.append({'class': OpeningRangeBreakout, 'name': '🎯 ORB 30min', 'type': 'breakout'})
except: pass

try:
    from strategies import SupertrendStrategy
    STRATEGY_LIST.append({'class': SupertrendStrategy, 'name': '🔷 Supertrend+RSI', 'type': 'trend'})
except: pass

try:
    from strategies import StochasticRSI_Strategy
    STRATEGY_LIST.append({'class': StochasticRSI_Strategy, 'name': '🌀 StochasticRSI', 'type': 'momentum'})
except: pass

try:
    from strategies import IchimokuStrategy
    STRATEGY_LIST.append({'class': IchimokuStrategy, 'name': '☁️ Ichimoku Cloud', 'type': 'trend'})
except: pass

try:
    from strategies import PriceActionStrategy
    STRATEGY_LIST.append({'class': PriceActionStrategy, 'name': '🕯️ Price Action', 'type': 'price_action'})
except: pass

try:
    from strategies import TripleEMA_ADX_Strategy
    STRATEGY_LIST.append({'class': TripleEMA_ADX_Strategy, 'name': '📊 Triple EMA+ADX', 'type': 'trend'})
except: pass

print(f"✅ Loaded {len(STRATEGY_LIST)} strategies")

# ============================================
# DATA LOADER - FIXED FOR YOUR STRUCTURE
# ============================================

def load_spot_data(base_folder, start_date=None, end_date=None):
    """Load spot price data from your option chain structure"""
    print(f"\n📂 Loading data from: {base_folder}")
    
    if not os.path.exists(base_folder):
        print(f"❌ Folder not found")
        return None
    
    # Find all date folders
    date_folders = []
    for item in os.listdir(base_folder):
        item_path = os.path.join(base_folder, item)
        if os.path.isdir(item_path):
            try:
                date = datetime.strptime(item, '%Y-%m-%d')
                date_folders.append((item, date))
            except:
                pass
    
    date_folders.sort(key=lambda x: x[1])
    print(f"✅ Found {len(date_folders)} date folders")
    
    all_records = []
    
    for folder_name, folder_date in date_folders:
        if start_date and folder_date < datetime.strptime(start_date, '%Y-%m-%d'):
            continue
        if end_date and folder_date > datetime.strptime(end_date, '%Y-%m-%d'):
            continue
        
        # Get data from ATM folder
        atm_path = os.path.join(base_folder, folder_name, 'ATM')
        if not os.path.exists(atm_path):
            continue
        
        # Try to load CALL data
        call_file = os.path.join(atm_path, f'NIFTY_{folder_name}_CALL.csv')
        if os.path.exists(call_file):
            try:
                df = pd.read_csv(call_file)
                
                # Check for datetime column
                if 'datetime' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['datetime'])
                elif 'time' in df.columns:
                    # If only time column, combine with date
                    df['timestamp'] = pd.to_datetime(folder_name + ' ' + df['time'])
                else:
                    # Use folder date + row index
                    df['timestamp'] = folder_date
                
                # Get spot price
                if 'spot' in df.columns:
                    df['close'] = df['spot']
                elif 'strike' in df.columns:
                    df['close'] = df['strike']
                elif 'close' in df.columns:
                    df['close'] = df['close']
                else:
                    continue
                
                # Select required columns
                result_df = df[['timestamp', 'close']].copy()
                result_df['date'] = folder_date
                all_records.append(result_df)
                
            except Exception as e:
                print(f"   Warning: Error reading {call_file}: {e}")
        
        # Also try PUT data as fallback
        if not all_records or len([r for r in all_records if r['date'].iloc[0] == folder_date]) == 0:
            put_file = os.path.join(atm_path, f'NIFTY_{folder_name}_PUT.csv')
            if os.path.exists(put_file):
                try:
                    df = pd.read_csv(put_file)
                    
                    if 'datetime' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['datetime'])
                    elif 'time' in df.columns:
                        df['timestamp'] = pd.to_datetime(folder_name + ' ' + df['time'])
                    else:
                        df['timestamp'] = folder_date
                    
                    if 'spot' in df.columns:
                        df['close'] = df['spot']
                    elif 'strike' in df.columns:
                        df['close'] = df['strike']
                    elif 'close' in df.columns:
                        df['close'] = df['close']
                    else:
                        continue
                    
                    result_df = df[['timestamp', 'close']].copy()
                    result_df['date'] = folder_date
                    all_records.append(result_df)
                    
                except Exception as e:
                    print(f"   Warning: Error reading {put_file}: {e}")
    
    if not all_records:
        print("❌ No data loaded")
        return None
    
    # Combine all data
    combined = pd.concat(all_records, ignore_index=True)
    combined = combined.drop_duplicates(subset=['timestamp'])
    combined.sort_values('timestamp', inplace=True)
    
    print(f"📊 Loaded {len(combined)} spot price records")
    print(f"   Date range: {combined['timestamp'].min()} to {combined['timestamp'].max()}")
    
    return combined

# ============================================
# BACKTEST ENGINE
# ============================================

class BacktestEngine:
    def __init__(self, capital=100000, risk_pct=0.01, rr=3):
        self.capital = capital
        self.risk_pct = risk_pct
        self.rr = rr
        self.initial_capital = capital
    
    def prepare_data(self, data):
        """Prepare data for backtesting - FIXED"""
        if data is None or len(data) < 50:
            return None
        
        df = data.copy()
        
        # Ensure timestamp is index
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        
        # Sort index
        df.sort_index(inplace=True)
        
        # Create OHLC if missing (use close for all)
        if 'open' not in df.columns:
            df['open'] = df['close']
        if 'high' not in df.columns:
            df['high'] = df['close']
        if 'low' not in df.columns:
            df['low'] = df['close']
        if 'volume' not in df.columns:
            df['volume'] = 0
        
        # Resample to 15 minute timeframe
        try:
            resampled = df.resample('15T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            print(f"📊 Resampled to 15min: {len(resampled)} candles")
            return resampled
        except Exception as e:
            print(f"⚠️ Resampling failed: {e}, using original data")
            return df
    
    def run_backtest(self, data, strategy_class, strategy_name):
        """Run backtest for a single strategy"""
        
        print(f"\n{'='*50}")
        print(f"📊 Testing: {strategy_name}")
        print(f"{'='*50}")
        
        try:
            strategy = strategy_class()
        except Exception as e:
            print(f"   ❌ Init failed: {e}")
            return None
        
        capital = self.initial_capital
        positions = []
        trades = []
        equity_curve = []
        peak_capital = self.initial_capital
        max_dd = 0
        
        # Calculate indicators
        try:
            strategy.calculate_indicators(data)
        except Exception as e:
            print(f"   ❌ Indicator error: {e}")
            return None
        
        print(f"   Data points: {len(data)}")
        
        for i in range(50, len(data)):
            current_data = data.iloc[:i+1].copy()
            price = data['close'].iloc[i]
            time = data.index[i]
            
            # Generate signals
            try:
                signals = strategy.generate_signals(current_data, "NIFTY")
            except Exception as e:
                signals = {'buy_call': False, 'buy_put': False}
            
            # Check existing positions
            for pos in positions[:]:
                if pos['type'] == 'LONG':
                    if price <= pos['sl']:
                        pnl = (price - pos['entry']) * pos['qty']
                        capital += pos['margin'] + pnl
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': time,
                            'type': 'LONG',
                            'pnl': pnl,
                            'exit_reason': 'SL'
                        })
                        positions.remove(pos)
                    elif price >= pos['target']:
                        pnl = (price - pos['entry']) * pos['qty']
                        capital += pos['margin'] + pnl
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': time,
                            'type': 'LONG',
                            'pnl': pnl,
                            'exit_reason': 'TARGET'
                        })
                        positions.remove(pos)
                else:  # SHORT
                    if price >= pos['sl']:
                        pnl = (pos['entry'] - price) * pos['qty']
                        capital += pos['margin'] + pnl
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': time,
                            'type': 'SHORT',
                            'pnl': pnl,
                            'exit_reason': 'SL'
                        })
                        positions.remove(pos)
                    elif price <= pos['target']:
                        pnl = (pos['entry'] - price) * pos['qty']
                        capital += pos['margin'] + pnl
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': time,
                            'type': 'SHORT',
                            'pnl': pnl,
                            'exit_reason': 'TARGET'
                        })
                        positions.remove(pos)
            
            # Enter new positions
            if len(positions) == 0:
                atr = price * 0.01
                
                if signals.get('buy_call'):
                    sl = price - atr
                    target = price + (atr * self.rr)
                    risk = price - sl
                    
                    if risk > 0:
                        risk_amount = capital * self.risk_pct
                        qty = max(1, int(risk_amount / risk))
                        margin = price * qty * 0.2
                        
                        if margin <= capital:
                            capital -= margin
                            positions.append({
                                'type': 'LONG',
                                'entry': price,
                                'entry_time': time,
                                'qty': qty,
                                'sl': sl,
                                'target': target,
                                'margin': margin
                            })
                            print(f"   📈 LONG: {qty} @ ₹{price:.2f}")
                            
                elif signals.get('buy_put'):
                    sl = price + atr
                    target = price - (atr * self.rr)
                    risk = sl - price
                    
                    if risk > 0:
                        risk_amount = capital * self.risk_pct
                        qty = max(1, int(risk_amount / risk))
                        margin = price * qty * 0.2
                        
                        if margin <= capital:
                            capital -= margin
                            positions.append({
                                'type': 'SHORT',
                                'entry': price,
                                'entry_time': time,
                                'qty': qty,
                                'sl': sl,
                                'target': target,
                                'margin': margin
                            })
                            print(f"   📉 SHORT: {qty} @ ₹{price:.2f}")
            
            # Track equity
            equity = capital
            for pos in positions:
                if pos['type'] == 'LONG':
                    equity += (price - pos['entry']) * pos['qty']
                else:
                    equity += (pos['entry'] - price) * pos['qty']
            equity_curve.append(equity)
            
            if equity > peak_capital:
                peak_capital = equity
            dd = (peak_capital - equity) / peak_capital * 100 if peak_capital > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        # Calculate metrics
        metrics = self._calc_metrics(trades, equity_curve, max_dd)
        
        if metrics['total_trades'] > 0:
            print(f"   ✅ Trades: {metrics['total_trades']} | Win: {metrics['win_rate']:.1f}% | P&L: ₹{metrics['total_pnl']:,.2f}")
        else:
            print(f"   ⚠️ No trades generated")
        
        return {'metrics': metrics, 'trades': trades}
    
    def _calc_metrics(self, trades, equity_curve, max_dd):
        if not trades:
            return {
                'total_trades': 0, 'win_rate': 0, 'total_pnl': 0,
                'total_return': 0, 'max_drawdown': 0, 'profit_factor': 0,
                'best_trade': 0, 'worst_trade': 0
            }
        
        pnls = [t['pnl'] for t in trades]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p < 0]
        
        total_pnl = sum(pnls)
        win_rate = (len(winning) / len(trades) * 100)
        
        gross_profit = sum(winning) if winning else 0
        gross_loss = abs(sum(losing)) if losing else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        total_return = 0
        if equity_curve:
            total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital * 100
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(trades) - len(winning),
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_return': round(total_return, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_dd, 2),
            'best_trade': round(max(pnls), 2) if pnls else 0,
            'worst_trade': round(min(pnls), 2) if pnls else 0,
        }

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    DATA_FOLDER = r"E:\siddesh\Trading\Sublime\code\Test\option\trading_bot_V_1\NIFTY"
    
    print("="*70)
    print("🚀 BACKTESTING ALL STRATEGIES")
    print("="*70)
    
    # Load data
    spot_data = load_spot_data(DATA_FOLDER, start_date='2021-01-01', end_date='2021-12-31')
    
    if spot_data is None or len(spot_data) < 50:
        print("❌ Insufficient data")
        exit()
    
    # Initialize engine
    engine = BacktestEngine(capital=100000, risk_pct=0.01, rr=3)
    
    # Prepare data
    data = engine.prepare_data(spot_data)
    
    if data is None or len(data) < 50:
        print("❌ Failed to prepare data")
        exit()
    
    print(f"\n✅ Data ready: {len(data)} candles")
    print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    
    # Run backtests
    results = {}
    
    for strategy_info in STRATEGY_LIST:
        try:
            result = engine.run_backtest(data, strategy_info['class'], strategy_info['name'])
            if result and result['metrics']['total_trades'] > 0:
                results[strategy_info['name']] = result['metrics']
        except Exception as e:
            print(f"   ❌ {strategy_info['name']} error: {e}")
    
    # Print comparison
    if results:
        print("\n" + "="*100)
        print("📊 STRATEGY COMPARISON")
        print("="*100)
        print(f"{'Strategy':<25} {'Trades':>8} {'Win Rate':>10} {'Total P&L':>14} {'Return %':>10} {'Max DD%':>10} {'PF':>8}")
        print("-"*100)
        
        sorted_results = sorted(results.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
        
        for name, m in sorted_results:
            print(f"{name:<25} {m['total_trades']:>8} {m['win_rate']:>9.1f}% ₹{m['total_pnl']:>11,.2f} {m['total_return']:>9.2f}% {m['max_drawdown']:>9.1f}% {m['profit_factor']:>7.2f}")
        
        print("="*100)
        
        # Winner
        best = sorted_results[0]
        print(f"\n🏆 BEST STRATEGY: {best[0]}")
        print(f"   Total P&L: ₹{best[1]['total_pnl']:,.2f}")
        print(f"   Win Rate: {best[1]['win_rate']:.1f}%")
        print(f"   Total Trades: {best[1]['total_trades']}")
        
        # Save results
        results_df = pd.DataFrame([{'Strategy': k, **v} for k, v in results.items()])
        results_df = results_df.sort_values('total_pnl', ascending=False)
        results_df.to_csv('backtest_results.csv', index=False)
        print(f"\n✅ Results saved to backtest_results.csv")
    else:
        print("\n❌ No strategies produced any trades")