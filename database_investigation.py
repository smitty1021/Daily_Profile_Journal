# Step 2.16: Investigate what's actually in the database and create what's missing
# Save this as database_investigation.py and run it

import sqlite3
import os


def database_investigation():
    """Investigate the database and create missing tables"""

    # Find the database file
    possible_paths = [
        'app.db',
        'instance/app.db',
        'instance/database.db',
        'database.db'
    ]

    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print("❌ Could not find database file.")
        print("🔍 Checked paths:", possible_paths)
        print("📁 Current directory contents:")
        for item in os.listdir('.'):
            print(f"   {item}")
        return False

    print(f"📁 Found database at: {db_path}")

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Show all tables
        print("\n📋 All tables in database:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("   (No tables found)")
        else:
            for table in tables:
                print(f"   {table[0]}")

        # Check each table's schema
        for table in tables:
            table_name = table[0]
            print(f"\n🔍 Schema for table '{table_name}':")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   {col[1]} {col[2]} (nullable: {not col[3]})")

            # Show row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📊 {count} rows")

        # Now let's create the missing tables
        print("\n🏗️ Creating missing tables...")

        # Create instrument table if missing
        table_names = [t[0] for t in tables]
        if 'instrument' not in table_names:
            print("➕ Creating instrument table...")
            cursor.execute("""
                CREATE TABLE instrument (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(10) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    point_value FLOAT NOT NULL DEFAULT 1.0,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                );
            """)
            cursor.execute("CREATE INDEX ix_instrument_symbol ON instrument (symbol);")

            # Insert default instruments
            instruments = [
                ('NQ', 'Nasdaq 100', 20.0, 1),
                ('ES', 'S&P 500', 50.0, 1),
                ('YM', 'Dow Jones', 5.0, 1),
                ('MNQ', 'Micro Nasdaq', 2.0, 1),
                ('MES', 'Micro S&P', 5.0, 1),
                ('MYM', 'Micro Dow', 0.5, 1),
            ]
            cursor.executemany(
                "INSERT INTO instrument (symbol, name, point_value, is_active) VALUES (?, ?, ?, ?)",
                instruments
            )
            print(f"✅ Created instrument table with {len(instruments)} instruments")

        # Create trade table if missing
        if 'trade' not in table_names:
            print("➕ Creating trade table...")
            cursor.execute("""
                CREATE TABLE trade (
                    id INTEGER PRIMARY KEY,
                    instrument VARCHAR(10) NOT NULL,
                    trade_date DATE NOT NULL,
                    direction VARCHAR(5) NOT NULL,
                    point_value FLOAT DEFAULT 1.0,
                    initial_stop_loss FLOAT,
                    terminus_target FLOAT,
                    is_dca BOOLEAN DEFAULT 0,
                    mae FLOAT,
                    mfe FLOAT,
                    trade_notes TEXT,
                    how_closed VARCHAR(20),
                    news_event VARCHAR(100),
                    rules_rating INTEGER,
                    management_rating INTEGER,
                    target_rating INTEGER,
                    entry_rating INTEGER,
                    preparation_rating INTEGER,
                    psych_scored_highest TEXT,
                    psych_scored_lowest TEXT,
                    overall_analysis_notes TEXT,
                    screenshot_link VARCHAR(255),
                    trade_management_notes TEXT,
                    errors_notes TEXT,
                    improvements_notes TEXT,
                    tags VARCHAR(255),
                    trading_model_id INTEGER,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (trading_model_id) REFERENCES trading_model(id),
                    FOREIGN KEY (user_id) REFERENCES user(id)
                );
            """)
            print("✅ Created trade table")

        # Create entry_point table if missing
        if 'entry_point' not in table_names:
            print("➕ Creating entry_point table...")
            cursor.execute("""
                CREATE TABLE entry_point (
                    id INTEGER PRIMARY KEY,
                    entry_time TIME NOT NULL,
                    contracts INTEGER NOT NULL,
                    entry_price FLOAT NOT NULL,
                    trade_id INTEGER NOT NULL,
                    FOREIGN KEY (trade_id) REFERENCES trade(id)
                );
            """)
            print("✅ Created entry_point table")

        # Create exit_point table if missing
        if 'exit_point' not in table_names:
            print("➕ Creating exit_point table...")
            cursor.execute("""
                CREATE TABLE exit_point (
                    id INTEGER PRIMARY KEY,
                    exit_time TIME,
                    contracts INTEGER,
                    exit_price FLOAT,
                    trade_id INTEGER NOT NULL,
                    FOREIGN KEY (trade_id) REFERENCES trade(id)
                );
            """)
            print("✅ Created exit_point table")

        # Commit all changes
        conn.commit()

        # Show final state
        print("\n📋 Final database state:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        final_tables = cursor.fetchall()
        for table in final_tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   {table_name}: {count} rows")

        conn.close()

        print("\n🎉 Database setup complete!")
        print("🚀 Now restart your Flask app and try accessing /trades/")
        return True

    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = database_investigation()
    if not success:
        print("\n💥 Investigation failed.")