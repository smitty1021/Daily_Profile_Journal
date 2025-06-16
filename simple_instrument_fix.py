# Step 2.8: Simple fix - reset the instrument table completely
# Save this as simple_instrument_fix.py and run it

from app import create_app, db
from app.models import Instrument, Trade
import sqlite3
import os


def simple_instrument_fix():
    """Simple fix: drop and recreate the instrument table properly"""
    app = create_app()

    with app.app_context():
        print("🔧 Simple fix: Resetting instrument table...")

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

            # Drop the index if it exists
            cursor.execute("DROP INDEX IF EXISTS ix_instrument_symbol;")

            conn.commit()
            conn.close()
            print("✅ Old instrument table dropped")

            # Now use SQLAlchemy to create the table with the correct schema
            print("🏗️ Creating new instrument table with SQLAlchemy...")
            db.create_all()
            print("✅ New instrument table created")

            # Seed the default instruments
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

            for instrument_data in default_instruments:
                instrument = Instrument(**instrument_data)
                db.session.add(instrument)

            db.session.commit()
            print(f"✅ Added {len(default_instruments)} instruments")

            # Fix existing trades
            print("🔄 Updating existing trades with correct point values...")
            trades_updated = 0

            for trade in Trade.query.all():
                if trade.point_value is None or trade.point_value == 0:
                    correct_point_value = Instrument.get_point_value(trade.instrument)
                    trade.point_value = correct_point_value
                    trades_updated += 1
                    print(f"  📝 Updated trade {trade.id}: {trade.instrument} -> ${correct_point_value}")

            if trades_updated > 0:
                db.session.commit()
                print(f"✅ Updated {trades_updated} trades")
            else:
                print("✅ No trades needed updating")

            # Test the system
            print("🧪 Testing instrument system...")

            # Test choices
            choices = Instrument.get_instrument_choices()
            print(f"✅ Instrument choices: {len(choices)} options")
            for choice in choices[:3]:  # Show first 3
                print(f"   {choice}")

            # Test point values
            point_values = Instrument.get_instrument_point_values()
            print(f"✅ Point values: {point_values}")

            # Test individual lookup
            nq_value = Instrument.get_point_value('NQ')
            es_value = Instrument.get_point_value('ES')
            print(f"✅ Individual lookups: NQ=${nq_value}, ES=${es_value}")

            print("🎉 Simple fix complete! Your dynamic instrument system is ready.")
            return True

        except Exception as e:
            print(f"❌ Error during simple fix: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False


if __name__ == "__main__":
    success = simple_instrument_fix()
    if success:
        print("\n🚀 You can now restart your Flask app and test the trades page!")
        print("📋 Try accessing: http://localhost:5000/trades/")
    else:
        print("\n💥 Simple fix failed. Check the error messages above.")