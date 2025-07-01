import sqlite3

conn = sqlite3.connect('instance/app.db')  # Using correct database name

# Get table schema
cursor = conn.execute("PRAGMA table_info(trade);")
columns = cursor.fetchall()

print("Trade table columns:")
print("ID | Name                 | Type       | NotNull | Default | PrimaryKey")
print("-" * 70)
for col in columns:
    default_val = str(col[4]) if col[4] is not None else "None"
    print(f"{col[0]:2} | {col[1]:20} | {col[2]:10} | {col[3]:7} | {default_val:7} | {col[5]}")

# Check specifically for pnl column
pnl_exists = any(col[1] == 'pnl' for col in columns)
print(f"\n✅ PnL column exists: {pnl_exists}")

if pnl_exists:
    pnl_col = next(col for col in columns if col[1] == 'pnl')
    print(f"PnL column details: {pnl_col}")

conn.close()