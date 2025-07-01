import sqlite3

conn = sqlite3.connect('instance/database.db')

# Get ALL table info
cursor = conn.execute("PRAGMA table_info(trade);")
columns = cursor.fetchall()

print("ALL Trade table columns:")
for i, col in enumerate(columns):
    print(f"{i:2} | {col[1]:25} | {col[2]:15} | NotNull: {col[3]} | Default: {col[4]} | PK: {col[5]}")

print(f"\nTotal columns: {len(columns)}")

# Check for pnl specifically (case insensitive)
pnl_columns = [col for col in columns if col[1].lower() == 'pnl']
print(f"PnL columns found: {len(pnl_columns)}")
for col in pnl_columns:
    print(f"  Found: {col}")

# Try to manually add the column to see what happens
try:
    conn.execute("ALTER TABLE trade ADD COLUMN pnl FLOAT;")
    conn.commit()
    print("\n✅ Successfully added pnl column manually")
except Exception as e:
    print(f"\n❌ Error adding pnl column: {e}")

conn.close()