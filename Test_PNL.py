from auth_service import create_tradehull_with_totp
from config import Config

tsl = create_tradehull_with_totp(Config.CLIENT_CODE, Config.PIN, Config.TOTP_SECRET)
positions = tsl.get_positions()

if positions is not None and not positions.empty:
    for _, row in positions.iterrows():
        print(f"Symbol: {row.get('tradingSymbol')}")
        print(f"  Net Qty: {row.get('netQty')}")
        print(f"  Avg Price: {row.get('avgPrice')}")
        print(f"  LTP: {row.get('ltp')}")
        print(f"  P&L: {row.get('pnl')}")
        print("-" * 40)
else:
    print("No open positions found")
