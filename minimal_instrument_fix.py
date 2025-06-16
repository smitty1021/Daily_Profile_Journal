# Step 2.9: Create a minimal working version first
# Save this as minimal_instrument_fix.py and run it

from app import create_app, db
from app.models import Trade
import sqlite3


def minimal_instrument_fix():
    """Create a minimal instrument table that works with your current system"""
    app = create_app()

    with app.app_context():
        print("🔧 Creating minimal instrument table...")

        # Get the database file path
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")

        try:
            # Connect directly to SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Drop the existing instrument table if it exists
            print("🗑️ Dropping existing instrument table...")
            cursor.execute("DROP TABLE IF EXISTS instrument;")
            cursor.execute("DROP INDEX IF EXISTS ix_instrument_symbol;")

            # Create a minimal instrument table with just the essential columns
            print("🏗️ Creating minimal instrument table...")
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

            # Create index
            cursor.execute("CREATE INDEX ix_instrument_symbol ON instrument (symbol);")

            # Insert the default instruments directly with SQL
            print("📊 Inserting default instruments...")
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

            conn.commit()
            conn.close()
            print(f"✅ Created instrument table and added {len(instruments)} instruments")

            # Test that we can query it
            print("🧪 Testing instrument queries...")

            # Test direct SQL query
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT symbol, name, point_value FROM instrument WHERE is_active = 1")
            results = cursor.fetchall()
            conn.close()

            print(f"✅ Found {len(results)} active instruments:")
            for symbol, name, point_value in results:
                print(f"   {symbol}: {name} (${point_value})")

            # Fix existing trades
            print("🔄 Updating existing trades with correct point values...")

            # Create a simple point value lookup
            point_values = {
                'NQ': 20.0, 'ES': 50.0, 'YM': 5.0,
                'MNQ': 2.0, 'MES': 5.0, 'MYM': 0.5
            }

            trades_updated = 0
            for trade in Trade.query.all():
                if trade.point_value is None or trade.point_value == 0:
                    correct_point_value = point_values.get(trade.instrument, 1.0)
                    trade.point_value = correct_point_value
                    trades_updated += 1
                    print(f"  📝 Updated trade {trade.id}: {trade.instrument} -> ${correct_point_value}")

            if trades_updated > 0:
                db.session.commit()
                print(f"✅ Updated {trades_updated} trades")
            else:
                print("✅ No trades needed updating")

            print("🎉 Minimal fix complete! Now let's test your trades page.")
            return True

        except Exception as e:
            print(f"❌ Error during minimal fix: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = minimal_instrument_fix()
    if success:
        print("\n🚀 The database is fixed! Now:")
        print("1. Restart your Flask app")
        print("2. Try accessing: http://localhost:5000/trades/")
        print("3. If it works, we can then update the Instrument model properly")
    else:
        print("\n💥 Minimal fix failed. Check the error messages above.")