import sqlite3

conn = sqlite3.connect('instance/database.db')

# Get all tables
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("All tables in database:")
if tables:
    for table in tables:
        print(f"  - {table[0]}")
else:
    print("  No tables found!")

print(f"\nTotal tables: {len(tables)}")

# Check for any trade-related tables
trade_tables = [table[0] for table in tables if 'trade' in table[0].lower()]
print(f"\nTrade-related tables: {trade_tables}")

conn.close()