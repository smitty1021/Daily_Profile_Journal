import sqlite3

conn = sqlite3.connect('instance/database.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check specifically for tag_new
tag_new_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tag_new';").fetchone()
if tag_new_exists:
    print("\n❌ tag_new table exists (this is the problem)")
    # Remove it
    conn.execute("DROP TABLE tag_new;")
    conn.commit()
    print("✅ Removed tag_new table")
else:
    print("\n✅ No tag_new table found")

conn.close()