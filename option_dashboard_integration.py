# option_dashboard_integration.py
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any

class OptionDashboardService:
    """Service to provide option data to dashboard"""
    
    def __init__(self, tsl, option_processor):
        self.tsl = tsl
        self.option_processor = option_processor
        
    def get_option_positions(self) -> List[Dict]:
        """Get active option positions"""
        positions = []
        try:
            # Get from trade execution
            if hasattr(self.option_processor.execution, 'orderbook'):
                for sym, order in self.option_processor.execution.orderbook.items():
                    if 'option_type' in order:
                        positions.append({
                            'symbol': sym,
                            'underlying': order.get('underlying', ''),
                            'type': order.get('option_type', ''),
                            'strike': order.get('strike', 0),
                            'entry_price': order.get('entry_price', 0),
                            'current_price': self._get_current_price(sym),
                            'quantity': order.get('qty', 0),
                            'lots': order.get('lots', 0),
                            'pnl': self._calculate_pnl(order),
                            'delta': order.get('greeks', {}).get('delta', 0),
                            'theta': order.get('greeks', {}).get('theta', 0),
                            'entry_time': order.get('entry_time', '')
                        })
        except Exception as e:
            print(f"Error getting option positions: {e}")
        return positions
    
    def get_option_summary(self) -> Dict:
        """Get summary of option trading"""
        positions = self.get_option_positions()
        
        total_pnl = sum(p.get('pnl', 0) for p in positions)
        total_premium = sum(p.get('entry_price', 0) * p.get('quantity', 0) for p in positions)
        
        return {
            'active_positions': len(positions),
            'total_pnl': total_pnl,
            'total_premium_exposed': total_premium,
            'avg_delta': sum(p.get('delta', 0) for p in positions) / len(positions) if positions else 0,
            'total_theta': sum(p.get('theta', 0) for p in positions)
        }
    
    def get_option_chain_data(self, underlying: str = "NIFTY", strikes: int = 10) -> Dict:
        """Get formatted option chain data"""
        try:
            atm_strike, df = self.option_processor.adapter.get_option_chain(underlying)
            
            if df is None or df.empty:
                return {'success': False, 'error': 'No data available'}
            
            strikes_data = []
            for _, row in df.iterrows():
                strike = row.get('Strike Price', 0)
                strikes_data.append({
                    'strike': int(strike),
                    'ce_ltp': float(row.get('CE LTP', 0)),
                    'ce_oi': int(row.get('CE OI', 0)),
                    'ce_oi_change': int(row.get('CE Chg in OI', 0)),
                    'ce_iv': float(row.get('CE IV', 0)),
                    'pe_ltp': float(row.get('PE LTP', 0)),
                    'pe_oi': int(row.get('PE OI', 0)),
                    'pe_oi_change': int(row.get('PE Chg in OI', 0)),
                    'pe_iv': float(row.get('PE IV', 0))
                })
            
            # Filter near ATM
            strikes_data.sort(key=lambda x: x['strike'])
            atm_idx = next((i for i, s in enumerate(strikes_data) if s['strike'] >= atm_strike), len(strikes_data)//2)
            start = max(0, atm_idx - strikes)
            end = min(len(strikes_data), atm_idx + strikes + 1)
            
            return {
                'success': True,
                'underlying': underlying,
                'spot_price': self._get_spot_price(underlying),
                'atm_strike': atm_strike,
                'strikes': strikes_data[start:end]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current option price"""
        try:
            ltp = self.tsl.get_ltp_data(names=[symbol])
            return ltp.get(symbol, 0)
        except:
            return 0
    
    def _get_spot_price(self, underlying: str) -> float:
        """Get spot price of underlying"""
        try:
            ltp = self.tsl.get_ltp_data(names=[underlying])
            return ltp.get(underlying, 0)
        except:
            return 0
    
    def _calculate_pnl(self, order: Dict) -> float:
        """Calculate P&L for option position"""
        current = self._get_current_price(order.get('name', ''))
        entry = order.get('entry_price', 0)
        qty = order.get('qty', 0)
        
        if order.get('option_type') == 'CALL':
            return (current - entry) * qty
        else:
            return (entry - current) * qty