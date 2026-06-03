# cleanup_db.py
import sqlite3

print("=" * 50)
print("CLEANING DATABASE")
print("=" * 50)

# Connect to database
conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

# Check current trades
cursor.execute("SELECT COUNT(*) FROM trades")
total = cursor.fetchone()[0]
print(f"\n📊 Current trades in database: {total}")

# Delete all MANUAL trades (they are duplicates)
cursor.execute("DELETE FROM trades WHERE strategy='MANUAL'")
deleted = cursor.rowcount
print(f"✅ Deleted {deleted} MANUAL trades")

# Reset P&L for open positions to 0
cursor.execute("UPDATE trades SET pnl = 0 WHERE status='open'")
updated = cursor.rowcount
print(f"✅ Reset P&L for {updated} open positions")

# Delete all MANUAL trades
cursor.execute("DELETE FROM trades WHERE strategy='MANUAL'")
print(f"Deleted {cursor.rowcount} MANUAL trades")

# Show remaining trades
cursor.execute("SELECT strategy, COUNT(*) FROM trades GROUP BY strategy")
remaining = cursor.fetchall()
print(f"\n📊 Remaining trades by strategy:")
for strat, count in remaining:
    print(f"   - {strat}: {count} trades")



# Get all MANUAL trades
cursor.execute("SELECT rowid, symbol, entry_price, quantity, pnl FROM trades WHERE strategy='MANUAL'")
rows = cursor.fetchall()

for row in rows:
    trade_id, symbol, entry_price, qty, pnl = row
    
    # If P&L is positive, this was likely a SELL (profit from BUY)
    # If P&L is negative, this was likely a BUY
    if pnl > 0:
        transaction_type = 'SELL'
    elif pnl < 0:
        transaction_type = 'BUY'
    else:
        # Try to determine from price pattern
        transaction_type = 'BUY'  # default
    
    cursor.execute("UPDATE trades SET transaction_type = ? WHERE rowid = ?", (transaction_type, trade_id))




# Check if column exists
cursor.execute("PRAGMA table_info(trades)")
columns = [col[1] for col in cursor.fetchall()]

if 'transaction_type' not in columns:
    cursor.execute("ALTER TABLE trades ADD COLUMN transaction_type TEXT")
    print("✅ Added transaction_type column")
else:
    print("transaction_type column already exists")


conn.commit()
conn.close()

print("\n" + "=" * 50)
print("✅ DATABASE CLEANED!")
print("=" * 50)
print("\nNext steps:")
print("1. Restart your dashboard")
print("2. Click 'Sync Now' button")
print("3. Refresh the browser")
