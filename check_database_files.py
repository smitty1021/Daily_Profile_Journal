# Step 2.19: Check for multiple database files and verify which one Flask is using
# Save this as check_database_files.py and run it

import os
import sqlite3
from app import create_app


def check_database_files():
    """Check for multiple database files and verify Flask configuration"""

    print("🔍 Checking for database files...")

    # Search for database files in common locations
    search_paths = [
        '.',
        'instance/',
        'app/',
        '../'
    ]

    db_files = []
    for path in search_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.db') or file.endswith('.sqlite') or file.endswith('.sqlite3'):
                    full_path = os.path.join(path, file)
                    db_files.append(full_path)

    print(f"📋 Found {len(db_files)} database files:")
    for db_file in db_files:
        print(f"   {db_file}")

    # Check Flask configuration
    print("\n🔧 Checking Flask database configuration...")
    app = create_app()

    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
        print(f"📍 SQLALCHEMY_DATABASE_URI: {db_uri}")

        # Extract the actual file path
        if db_uri.startswith('sqlite:///'):
            configured_db_path = db_uri.replace('sqlite:///', '')
            print(f"📁 Configured database path: {configured_db_path}")

            # Check if this file exists
            if os.path.exists(configured_db_path):
                print("✅ Configured database file exists")

                # Check the schema of the configured database
                print("\n🔍 Checking schema of configured database:")
                conn = sqlite3.connect(configured_db_path)
                cursor = conn.cursor()

                # Check if trade table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trade';")
                trade_exists = cursor.fetchone() is not None

                if trade_exists:
                    print("✅ Trade table exists in configured database")

                    # Check columns
                    cursor.execute("PRAGMA table_info(trade);")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]

                    print("📋 Columns in configured database:")
                    for col in columns:
                        print(f"   {col[1]} {col[2]}")

                    # Check specifically for point_value
                    if 'point_value' in column_names:
                        print("✅ point_value column exists in configured database")
                    else:
                        print("❌ point_value column MISSING in configured database")

                        # Add it
                        print("➕ Adding point_value column to configured database...")
                        cursor.execute("ALTER TABLE trade ADD COLUMN point_value FLOAT;")
                        conn.commit()
                        print("✅ Added point_value column")

                    # Check row count
                    cursor.execute("SELECT COUNT(*) FROM trade")
                    row_count = cursor.fetchone()[0]
                    print(f"📊 Trade table has {row_count} rows")

                else:
                    print("❌ Trade table does NOT exist in configured database")
                    print("🏗️ Creating trade table in configured database...")

                    # Create the table with all expected columns
                    create_sql = """
                    CREATE TABLE trade (
                        id INTEGER PRIMARY KEY,
                        instrument_id INTEGER,
                        instrument_legacy VARCHAR(10),
                        trade_date DATE NOT NULL,
                        direction VARCHAR(5) NOT NULL,
                        point_value FLOAT,
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
                        user_id INTEGER NOT NULL
                    );
                    """

                    cursor.execute(create_sql)
                    conn.commit()
                    print("✅ Created trade table in configured database")

                conn.close()

            else:
                print("❌ Configured database file does NOT exist")
                print(f"   Expected: {configured_db_path}")
                print("   This might be why Flask can't find the table!")

                # Create the missing database file
                print("🏗️ Creating missing database file...")
                conn = sqlite3.connect(configured_db_path)
                cursor = conn.cursor()

                # Create trade table
                create_sql = """
                CREATE TABLE trade (
                    id INTEGER PRIMARY KEY,
                    instrument_id INTEGER,
                    instrument_legacy VARCHAR(10),
                    trade_date DATE NOT NULL,
                    direction VARCHAR(5) NOT NULL,
                    point_value FLOAT,
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
                    user_id INTEGER NOT NULL
                );
                """

                cursor.execute(create_sql)

                # Also create instrument table if needed
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instrument';")
                if not cursor.fetchone():
                    print("🏗️ Creating instrument table...")
                    cursor.execute("""
                        CREATE TABLE instrument (
                            id INTEGER PRIMARY KEY,
                            symbol VARCHAR(10) UNIQUE NOT NULL,
                            name VARCHAR(100) NOT NULL,
                            point_value FLOAT NOT NULL DEFAULT 1.0,
                            is_active BOOLEAN NOT NULL DEFAULT 1
                        );
                    """)

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
                    print("✅ Created instrument table with default instruments")

                conn.commit()
                conn.close()
                print(f"✅ Created database file at: {configured_db_path}")

        else:
            print(f"❌ Unexpected database URI format: {db_uri}")

    print("\n🎉 Database file check complete!")
    print("🚀 Now restart your Flask app and try accessing /trades/")


if __name__ == "__main__":
    check_database_files()