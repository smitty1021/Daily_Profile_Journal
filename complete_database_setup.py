# Step 2.12: Complete database setup - create all tables and fix everything
# Save this as complete_database_setup.py and run it

from app import create_app, db
import sqlite3


def complete_database_setup():
    """Create all necessary tables and set up the database properly"""
    app = create_app()

    with app.app_context():
        print("🔧 Setting up complete database...")

        # Get the database file path
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")

        try:
            # First, check what tables exist
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [table[0] for table in cursor.fetchall()]
            print(f"📋 Existing tables: {existing_tables}")

            conn.close()

            # Create all tables using SQLAlchemy
            print("🏗️ Creating all database tables...")
            db.create_all()
            print("✅ Database tables created/updated")

            # Check tables again
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            all_tables = [table[0] for table in cursor.fetchall()]
            print(f"📋 All tables after creation: {all_tables}")

            # Now handle instruments
            if 'instrument' not in all_tables:
                print("🚨 Instrument table missing - creating manually...")
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
                print("✅ Instrument table created manually")

            # Insert default instruments
            print("📊 Setting up default instruments...")
            instruments = [
                ('NQ', 'Nasdaq 100', 20.0, 1),
                ('ES', 'S&P 500', 50.0, 1),
                ('YM', 'Dow Jones', 5.0, 1),
                ('MNQ', 'Micro Nasdaq', 2.0, 1),
                ('MES', 'Micro S&P', 5.0, 1),
                ('MYM', 'Micro Dow', 0.5, 1),
            ]

            # Check if instruments already exist
            cursor.execute("SELECT COUNT(*) FROM instrument")
            existing_instrument_count = cursor.fetchone()[0]

            if existing_instrument_count == 0:
                cursor.executemany(
                    "INSERT INTO instrument (symbol, name, point_value, is_active) VALUES (?, ?, ?, ?)",
                    instruments
                )
                print(f"✅ Added {len(instruments)} default instruments")
            else:
                print(f"✅ Found {existing_instrument_count} existing instruments")

            # Handle trades table
            if 'trade' in all_tables:
                print("🔍 Checking existing trades...")
                cursor.execute("SELECT COUNT(*) FROM trade")
                trade_count = cursor.fetchone()[0]
                print(f"📊 Found {trade_count} existing trades")

                if trade_count > 0:
                    # Check if trades need point value updates
                    cursor.execute("SELECT COUNT(*) FROM trade WHERE point_value IS NULL OR point_value = 0")
                    trades_needing_update = cursor.fetchone()[0]

                    if trades_needing_update > 0:
                        print(f"🔄 Updating {trades_needing_update} trades with point values...")

                        # Update trades with correct point values
                        cursor.execute(
                            "UPDATE trade SET point_value = 20.0 WHERE instrument = 'NQ' AND (point_value IS NULL OR point_value = 0)")
                        cursor.execute(
                            "UPDATE trade SET point_value = 50.0 WHERE instrument = 'ES' AND (point_value IS NULL OR point_value = 0)")
                        cursor.execute(
                            "UPDATE trade SET point_value = 5.0 WHERE instrument = 'YM' AND (point_value IS NULL OR point_value = 0)")
                        cursor.execute(
                            "UPDATE trade SET point_value = 2.0 WHERE instrument = 'MNQ' AND (point_value IS NULL OR point_value = 0)")
                        cursor.execute(
                            "UPDATE trade SET point_value = 5.0 WHERE instrument = 'MES' AND (point_value IS NULL OR point_value = 0)")
                        cursor.execute(
                            "UPDATE trade SET point_value = 0.5 WHERE instrument = 'MYM' AND (point_value IS NULL OR point_value = 0)")
                        cursor.execute(
                            "UPDATE trade SET point_value = 1.0 WHERE instrument NOT IN ('NQ', 'ES', 'YM', 'MNQ', 'MES', 'MYM') AND (point_value IS NULL OR point_value = 0)")

                        print("✅ Trade point values updated")
                    else:
                        print("✅ All trades already have point values")
            else:
                print("✅ Trade table ready for new trades")

            # Commit all changes
            conn.commit()
            conn.close()

            # Test the instrument system
            print("🧪 Testing instrument system...")

            # Test direct SQL query
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT symbol, name, point_value FROM instrument WHERE is_active = 1")
            results = cursor.fetchall()
            conn.close()

            print(f"✅ Found {len(results)} active instruments:")
            for symbol, name, point_value in results:
                print(f"   {symbol}: {name} (${point_value})")

            print("🎉 Complete database setup finished!")
            return True

        except Exception as e:
            print(f"❌ Error during complete setup: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = complete_database_setup()
    if success:
        print("\n🚀 Database setup complete! Now:")
        print("1. Restart your Flask app")
        print("2. Try accessing: http://localhost:5000/trades/")
        print("3. Try adding a new trade")
        print("4. All instrument point values should work correctly")
    else:
        print("\n💥 Complete setup failed. Check the error messages above.")