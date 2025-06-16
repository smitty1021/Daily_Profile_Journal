# Step 2.7: Create a proper database migration
# Save this as create_instrument_migration.py and run it

from app import create_app, db
from app.models import Instrument, Trade
import sqlite3
import os


def create_instrument_migration():
    """Create the instrument table properly with all columns"""
    app = create_app()

    with app.app_context():
        print("🔧 Creating proper instrument table migration...")

        # Get the database file path
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if not db_path:
            print("❌ Could not find database path")
            return False

        print(f"📁 Database path: {db_path}")

        try:
            # Connect directly to SQLite to check/create the table
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if instrument table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instrument';")
            table_exists = cursor.fetchone() is not None

            if table_exists:
                print("📋 Instrument table exists, checking columns...")

                # Get existing columns
                cursor.execute("PRAGMA table_info(instrument);")
                existing_columns = [column[1] for column in cursor.fetchall()]
                print(f"🔍 Existing columns: {existing_columns}")

                # Check if we need to add missing columns
                required_columns = {
                    'display_order': 'INTEGER NOT NULL DEFAULT 0',
                    'tick_size': 'FLOAT DEFAULT 0.25',
                    'description': 'TEXT'
                }

                missing_columns = []
                for col_name, col_def in required_columns.items():
                    if col_name not in existing_columns:
                        missing_columns.append((col_name, col_def))

                if missing_columns:
                    print(f"➕ Adding missing columns: {[col[0] for col in missing_columns]}")
                    for col_name, col_def in missing_columns:
                        cursor.execute(f"ALTER TABLE instrument ADD COLUMN {col_name} {col_def};")
                        print(f"✅ Added column: {col_name}")
                else:
                    print("✅ All required columns exist")
            else:
                print("🏗️ Creating new instrument table...")

                # Create the complete table
                create_table_sql = """
                CREATE TABLE instrument (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(10) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    point_value FLOAT NOT NULL DEFAULT 1.0,
                    tick_size FLOAT DEFAULT 0.25,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    description TEXT
                );
                """
                cursor.execute(create_table_sql)

                # Create index
                cursor.execute("CREATE INDEX ix_instrument_symbol ON instrument (symbol);")
                print("✅ Created instrument table with all columns")

            # Commit the changes
            conn.commit()
            conn.close()

            # Now seed the default instruments using SQLAlchemy
            print("📊 Seeding default instruments...")

            default_instruments = [
                {'symbol': 'NQ', 'name': 'Nasdaq 100', 'point_value': 20.0, 'tick_size': 0.25, 'display_order': 1,
                 'is_active': True},
                {'symbol': 'ES', 'name': 'S&P 500', 'point_value': 50.0, 'tick_size': 0.25, 'display_order': 2,
                 'is_active': True},
                {'symbol': 'YM', 'name': 'Dow Jones', 'point_value': 5.0, 'tick_size': 1.0, 'display_order': 3,
                 'is_active': True},
                {'symbol': 'MNQ', 'name': 'Micro Nasdaq', 'point_value': 2.0, 'tick_size': 0.25, 'display_order': 4,
                 'is_active': True},
                {'symbol': 'MES', 'name': 'Micro S&P', 'point_value': 5.0, 'tick_size': 0.25, 'display_order': 5,
                 'is_active': True},
                {'symbol': 'MYM', 'name': 'Micro Dow', 'point_value': 0.5, 'tick_size': 1.0, 'display_order': 6,
                 'is_active': True},
            ]

            instruments_added = 0
            for instrument_data in default_instruments:
                # Check if instrument already exists
                existing = Instrument.query.filter_by(symbol=instrument_data['symbol']).first()
                if not existing:
                    instrument = Instrument(**instrument_data)
                    db.session.add(instrument)
                    instruments_added += 1
                else:
                    print(f"↩️ Instrument {instrument_data['symbol']} already exists")

            if instruments_added > 0:
                db.session.commit()
                print(f"✅ Added {instruments_added} new instruments")
            else:
                print("✅ All instruments already exist")

            # Fix existing trades
            print("🔄 Updating existing trades with correct point values...")
            trades_updated = 0
            for trade in Trade.query.all():
                if trade.point_value is None or trade.point_value == 0:
                    correct_point_value = Instrument.get_point_value(trade.instrument)
                    trade.point_value = correct_point_value
                    trades_updated += 1

            if trades_updated > 0:
                db.session.commit()
                print(f"✅ Updated {trades_updated} trades with correct point values")
            else:
                print("✅ All trades already have correct point values")

            # Test the system
            print("🧪 Testing instrument system...")
            choices = Instrument.get_instrument_choices()
            point_values = Instrument.get_instrument_point_values()
            nq_value = Instrument.get_point_value('NQ')

            print(f"✅ Instrument choices: {len(choices)} options")
            print(f"✅ Point values: {point_values}")
            print(f"✅ NQ point value: ${nq_value}")

            print("🎉 Migration complete! Your dynamic instrument system is ready.")
            return True

        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    success = create_instrument_migration()
    if success:
        print("\n🚀 You can now restart your Flask app and test the trades page!")
    else:
        print("\n💥 Migration failed. Check the error messages above.")