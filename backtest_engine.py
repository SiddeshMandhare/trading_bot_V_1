# backtest_engine.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class BacktestTrade:
    entry_time: str
    exit_time: str
    symbol: str
    action: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_percent: float
    strategy: str
    exit_reason: str

class BacktestEngine:
    def __init__(self, tsl, initial_capital: float = 100000):
        self.tsl = tsl
        self.initial_capital = initial_capital
        self.results = {}
    
    def run_backtest(self, symbol: str, strategy, start_date: str, end_date: str, 
                     timeframe: str = '15', **strategy_params) -> Dict:
        """
        Run backtest for a strategy
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY', 'RELIANCE')
            strategy: Strategy class instance
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            timeframe: '1', '5', '15', '60', 'DAY'
            **strategy_params: Strategy-specific parameters
        """
        
        print(f"\n{'='*60}")
        print(f"📊 BACKTEST STARTED")
        print(f"{'='*60}")
        print(f"   Symbol: {symbol}")
        print(f"   Strategy: {strategy.get_strategy_name()}")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Timeframe: {timeframe}")
        print(f"{'='*60}\n")
        
        # Fetch historical data
        try:
            # Try long-term data first
            data = self.tsl.get_long_term_historical_data(
                tradingsymbol=symbol,
                exchange=self._get_exchange(symbol),
                timeframe=timeframe,
                from_date=start_date,
                to_date=end_date
            )
        except:
            # Fallback to regular historical data
            data = self.tsl.get_historical_data(
                tradingsymbol=symbol,
                exchange=self._get_exchange(symbol),
                timeframe=timeframe
            )
        
        if data is None or data.empty:
            print(f"❌ No data available for {symbol}")
            return {'error': 'No data available'}
        
        print(f"✅ Loaded {len(data)} candles")
        
        # Run simulation
        portfolio = self._run_simulation(data, strategy, symbol, strategy_params)
        
        # Calculate metrics
        metrics = self._calculate_metrics(portfolio)
        
        # Generate report
        report = self._generate_report(metrics, portfolio)
        
        self.results[symbol] = report
        
        return report
    
    def _get_exchange(self, symbol: str) -> str:
        """Determine exchange for symbol"""
        indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX']
        if symbol.upper() in indices:
            return 'INDEX'
        return 'NSE'
    
    def _run_simulation(self, data: pd.DataFrame, strategy, symbol: str, 
                        params: Dict) -> Dict:
        """Run the actual simulation"""
        
        portfolio = {
            'capital': self.initial_capital,
            'positions': [],
            'trades': [],
            'equity_curve': [],
            'drawdown_curve': []
        }
        
        peak_capital = self.initial_capital
        
        for i in range(len(data)):
            current_data = data.iloc[:i+1].copy()
            current_price = current_data['close'].iloc[-1]
            current_time = current_data['timestamp'].iloc[-1] if 'timestamp' in current_data.columns else i
            
            # Calculate indicators
            try:
                strategy.calculate_indicators(current_data)
                signals = strategy.generate_signals(current_data, symbol)
            except Exception as e:
                print(f"⚠️ Error at index {i}: {e}")
                signals = {'buy_call': False, 'buy_put': False}
            
            # Check existing positions
            for pos in portfolio['positions'][:]:
                # Stop loss check
                if pos['position_type'] == 'LONG':
                    if current_price <= pos['stop_loss']:
                        self._close_position(portfolio, pos, current_price, current_time, 'SL_HIT')
                    elif current_price >= pos['target']:
                        self._close_position(portfolio, pos, current_price, current_time, 'TARGET_HIT')
                else:
                    if current_price >= pos['stop_loss']:
                        self._close_position(portfolio, pos, current_price, current_time, 'SL_HIT')
                    elif current_price <= pos['target']:
                        self._close_position(portfolio, pos, current_price, current_time, 'TARGET_HIT')
            
            # Enter new positions
            if len(portfolio['positions']) == 0:
                if signals.get('buy_call'):
                    self._enter_position(portfolio, current_price, current_time, 'BUY', symbol, strategy.get_strategy_name(), params)
                elif signals.get('buy_put'):
                    self._enter_position(portfolio, current_price, current_time, 'SELL', symbol, strategy.get_strategy_name(), params)
            
            # Track equity curve
            current_equity = portfolio['capital'] + self._calculate_unrealized_pnl(portfolio, current_price)
            portfolio['equity_curve'].append({
                'time': current_time,
                'equity': current_equity
            })
            
            # Track drawdown
            if current_equity > peak_capital:
                peak_capital = current_equity
            drawdown = (peak_capital - current_equity) / peak_capital * 100 if peak_capital > 0 else 0
            portfolio['drawdown_curve'].append(drawdown)
        
        return portfolio
    
    def _enter_position(self, portfolio: Dict, price: float, time, action: str, 
                        symbol: str, strategy_name: str, params: Dict):
        """Enter a new position"""
        
        from config import Config
        atr_points = price * 0.02  # Default 2% ATR
        
        if action == 'BUY':
            stop_loss = price - (atr_points * 5)
            target = price + (atr_points * 5 * 3)
            position_type = 'LONG'
        else:
            stop_loss = price + (atr_points * 5)
            target = price - (atr_points * 5 * 3)
            position_type = 'SHORT'
        
        # Calculate position size
        risk_amount = portfolio['capital'] * 0.01  # 1% risk
        position_size = max(1, int(risk_amount / (abs(price - stop_loss))))
        
        position = {
            'symbol': symbol,
            'position_type': position_type,
            'entry_price': price,
            'entry_time': time,
            'quantity': position_size,
            'stop_loss': stop_loss,
            'target': target,
            'strategy': strategy_name
        }
        
        portfolio['positions'].append(position)
        
        # Deduct margin
        margin = price * position_size * 0.2
        portfolio['capital'] -= margin
        
        print(f"   📈 ENTRY: {action} {position_size} {symbol} @ ₹{price:.2f}")
    
    def _close_position(self, portfolio: Dict, position: Dict, price: float, 
                        time, reason: str):
        """Close an existing position"""
        
        if position['position_type'] == 'LONG':
            pnl = (price - position['entry_price']) * position['quantity']
        else:
            pnl = (position['entry_price'] - price) * position['quantity']
        
        # Return margin + profit/loss
        margin = position['entry_price'] * position['quantity'] * 0.2
        portfolio['capital'] += margin + pnl
        
        trade = BacktestTrade(
            entry_time=str(position['entry_time']),
            exit_time=str(time),
            symbol=position['symbol'],
            action=position['position_type'],
            entry_price=position['entry_price'],
            exit_price=price,
            quantity=position['quantity'],
            pnl=pnl,
            pnl_percent=(pnl / (position['entry_price'] * position['quantity']) * 100),
            strategy=position['strategy'],
            exit_reason=reason
        )
        
        portfolio['trades'].append(trade)
        portfolio['positions'].remove(position)
        
        print(f"   🔴 EXIT: {position['symbol']} @ ₹{price:.2f} | P&L: ₹{pnl:+,.2f} | Reason: {reason}")
    
    def _calculate_unrealized_pnl(self, portfolio: Dict, current_price: float) -> float:
        """Calculate unrealized P&L for open positions"""
        total_pnl = 0
        for pos in portfolio['positions']:
            if pos['position_type'] == 'LONG':
                pnl = (current_price - pos['entry_price']) * pos['quantity']
            else:
                pnl = (pos['entry_price'] - current_price) * pos['quantity']
            total_pnl += pnl
        return total_pnl
    
    def _calculate_metrics(self, portfolio: Dict) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        trades = portfolio['trades']
        equity_curve = [e['equity'] for e in portfolio['equity_curve']]
        drawdown_curve = portfolio['drawdown_curve']
        
        if not trades:
            return {'error': 'No trades executed'}
        
        pnls = [t.pnl for t in trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        
        # Basic metrics
        total_trades = len(trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(pnls)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Risk metrics
        max_drawdown = max(drawdown_curve) if drawdown_curve else 0
        
        # Sharpe ratio
        returns = np.diff(equity_curve) / equity_curve[:-1] if len(equity_curve) > 1 else [0]
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Sortino ratio (only downside deviation)
        negative_returns = [r for r in returns if r < 0]
        if negative_returns and np.std(negative_returns) > 0:
            sortino_ratio = (np.mean(returns) / np.std(negative_returns)) * np.sqrt(252)
        else:
            sortino_ratio = 0
        
        # Calmar ratio
        annual_return = (equity_curve[-1] / equity_curve[0] - 1) if equity_curve else 0
        calmar_ratio = annual_return / (max_drawdown / 100) if max_drawdown > 0 else 0
        
        # Expectancy
        expectancy = (avg_pnl * win_rate / 100) + (avg_pnl * (1 - win_rate / 100))
        
        # Best/Worst trades
        best_trade = max(pnls) if pnls else 0
        worst_trade = min(pnls) if pnls else 0
        
        # Average holding period
        holding_periods = []
        for t in trades:
            try:
                entry = datetime.fromisoformat(t.entry_time)
                exit = datetime.fromisoformat(t.exit_time)
                holding_periods.append((exit - entry).total_seconds() / 60)  # minutes
            except:
                pass
        avg_holding = np.mean(holding_periods) if holding_periods else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_count,
            'losing_trades': losing_count,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_return': round((equity_curve[-1] - self.initial_capital) / self.initial_capital * 100, 2),
            'avg_pnl': round(avg_pnl, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'calmar_ratio': round(calmar_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'expectancy': round(expectancy, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'avg_holding_minutes': round(avg_holding, 1),
            'final_equity': round(equity_curve[-1], 2)
        }
    
    def _generate_report(self, metrics: Dict, portfolio: Dict) -> Dict:
        """Generate detailed backtest report"""
        
        if 'error' in metrics:
            return metrics
        
        # Create trade summary
        trade_summary = []
        for trade in portfolio['trades']:
            trade_summary.append(asdict(trade))
        
        # Create equity curve for charting
        equity_curve = [{'time': e['time'], 'equity': e['equity']} for e in portfolio['equity_curve']]
        
        return {
            'metrics': metrics,
            'trades': trade_summary[-50:],  # Last 50 trades
            'equity_curve': equity_curve,
            'summary': {
                'initial_capital': self.initial_capital,
                'final_capital': metrics['final_equity'],
                'total_return': metrics['total_return'],
                'profitable_months': self._calculate_monthly_breakdown(portfolio['trades'])
            }
        }
    
    def _calculate_monthly_breakdown(self, trades: List[BacktestTrade]) -> Dict:
        """Calculate monthly P&L breakdown"""
        monthly_pnl = {}
        for trade in trades:
            try:
                month = trade.entry_time[:7]  # YYYY-MM
                monthly_pnl[month] = monthly_pnl.get(month, 0) + trade.pnl
            except:
                pass
        return dict(sorted(monthly_pnl.items())[-12:])  # Last 12 months


    def compare_strategies(self, symbol: str, strategies: List, start_date: str, end_date: str):
        """Compare multiple strategies back-to-back"""
        results = {}
        for strategy in strategies:
            results[strategy.get_strategy_name()] = self.run_backtest(
                symbol, strategy, start_date, end_date
            )
        
        # Generate comparison chart
        comparison = self._generate_comparison(results)
        return comparison

    def _generate_comparison(self, results):
        """Generate strategy comparison metrics"""
        comparison = {}
        for name, result in results.items():
            metrics = result.get('metrics', {})
            comparison[name] = {
                'win_rate': metrics.get('win_rate', 0),
                'total_return': metrics.get('total_return', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'max_drawdown': metrics.get('max_drawdown', 0),
                'profit_factor': metrics.get('profit_factor', 0)
            }
        return comparison


    def walk_forward_analysis(self, symbol: str, strategy, start_date: str, end_date: str, 
                          train_size: int = 180, test_size: int = 30):
        """Walk-forward optimization"""
        current_date = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        results = []
        
        while current_date + timedelta(days=train_size + test_size) <= end:
            train_start = current_date
            train_end = current_date + timedelta(days=train_size)
            test_start = train_end
            test_end = test_start + timedelta(days=test_size)
            
            # Optimize on training data
            optimal_params = self._optimize_params(symbol, strategy, train_start, train_end)
            
            # Test on out-of-sample data
            test_result = self.run_backtest(
                symbol, strategy, 
                test_start.strftime('%Y-%m-%d'), 
                test_end.strftime('%Y-%m-%d'),
                **optimal_params
            )
            
            results.append({
                'period': f"{test_start.date()} to {test_end.date()}",
                'params': optimal_params,
                'metrics': test_result.get('metrics', {})
            })
            
            current_date += timedelta(days=test_size)
        
        return results

    def export_results_to_csv(self, results: Dict, filename: str = None):
        """Export backtest results to CSV"""
        if filename is None:
            filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        trades_df = pd.DataFrame(results.get('trades', []))
        trades_df.to_csv(f"exports/{filename}", index=False)
        
        return filename