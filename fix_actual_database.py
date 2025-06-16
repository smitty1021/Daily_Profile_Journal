# Step 2.14: Check and fix the actual database schema
# Save this as fix_actual_database.py and run it

from app import create_app, db
import sqlite3


def fix_actual_database():
    """Check the actual database schema and fix it"""
    app = create_app()

    with app.app_context():
        print("🔧 Checking actual database schema...")

        # Get the database file path
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")

        try:
            # Connect directly to SQLite to inspect the schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check what tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"📋 Existing tables: {tables}")

            # Check the actual trade table schema
            if 'trade' in tables:
                print("\n🔍 Actual trade table schema:")
                cursor.execute("PRAGMA table_info(trade);")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   {col[1]} {col[2]} (nullable: {not col[3]})")

                # Check if point_value column exists
                column_names = [col[1] for col in columns]
                if 'point_value' not in column_names:
                    print("\n➕ Adding missing point_value column to trade table...")
                    cursor.execute("ALTER TABLE trade ADD COLUMN point_value FLOAT DEFAULT 1.0;")
                    print("✅ Added point_value column")
                else:
                    print("✅ point_value column already exists")

                # Check if we need to add instrument column (if only instrument_id exists)
                if 'instrument' not in column_names and 'instrument_legacy' in column_names:
                    print("➕ Adding instrument column...")
                    cursor.execute("ALTER TABLE trade ADD COLUMN instrument VARCHAR(10);")

                    # Copy data from instrument_legacy to instrument if it exists
                    cursor.execute(
                        "UPDATE trade SET instrument = instrument_legacy WHERE instrument_legacy IS NOT NULL;")
                    print("✅ Added instrument column and copied from instrument_legacy")
                elif 'instrument' not in column_names and 'instrument_id' in column_names:
                    print("➕ Adding instrument column...")
                    cursor.execute("ALTER TABLE trade ADD COLUMN instrument VARCHAR(10);")
                    print("✅ Added instrument column (you'll need to populate it manually)")
                else:
                    print("✅ instrument column exists")

            # Check the instrument table
            if 'instrument' in tables:
                print("\n🔍 Instrument table schema:")
                cursor.execute("PRAGMA table_info(instrument);")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   {col[1]} {col[2]} (nullable: {not col[3]})")

                cursor.execute("SELECT symbol, name, point_value FROM instrument;")
                instruments = cursor.fetchall()
                print(f"\n📊 Found {len(instruments)} instruments:")
                for symbol, name, point_value in instruments:
                    print(f"   {symbol}: {name} (${point_value})")
            else:
                print("\n🚨 No instrument table found - creating it...")
                create_table_sql = """
                CREATE TABLE instrument (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(10) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    point_value FLOAT NOT NULL DEFAULT 1.0,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                );
                """
                cursor.execute(create_table_sql)
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
                print(f"✅ Created instrument table and added {len(instruments)} instruments")

            # Now fix any trades that need point values
            if 'trade' in tables:
                print("\n🔄 Updating trade point values...")

                # Check current state
                cursor.execute("SELECT COUNT(*) FROM trade WHERE point_value IS NULL OR point_value = 0")
                trades_needing_update = cursor.fetchone()[0]
                print(f"📊 Found {trades_needing_update} trades needing point value updates")

                if trades_needing_update > 0:
                    # Update based on instrument column
                    updates = [
                        ('NQ', 20.0), ('ES', 50.0), ('YM', 5.0),
                        ('MNQ', 2.0), ('MES', 5.0), ('MYM', 0.5)
                    ]

                    total_updated = 0
                    for instrument, point_value in updates:
                        cursor.execute(
                            "UPDATE trade SET point_value = ? WHERE instrument = ? AND (point_value IS NULL OR point_value = 0)",
                            (point_value, instrument)
                        )
                        updated = cursor.rowcount
                        if updated > 0:
                            print(f"  📝 Updated {updated} {instrument} trades -> ${point_value}")
                            total_updated += updated

                    # Update any remaining trades to 1.0
                    cursor.execute("UPDATE trade SET point_value = 1.0 WHERE point_value IS NULL OR point_value = 0")
                    remaining = cursor.rowcount
                    if remaining > 0:
                        print(f"  📝 Updated {remaining} other trades -> $1.0")
                        total_updated += remaining

                    print(f"✅ Total trades updated: {total_updated}")
                else:
                    print("✅ All trades already have point values")

            # Commit all changes
            conn.commit()
            conn.close()

            print("\n🎉 Database schema fix complete!")
            return True

        except Exception as e:
            print(f"❌ Error during schema fix: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = fix_actual_database()
    if success:
        print("\n🚀 Database schema fixed! Now:")
        print("1. Restart your Flask app")
        print("2. Try accessing: http://localhost:5000/trades/")
        print("3. The point_value column should now exist and work correctly")
    else:
        print("\n💥 Schema fix failed. Check the error messages above.")