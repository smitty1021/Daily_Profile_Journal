# fix_missing_instruments.py
# Handle the 161 trades with no instrument data

from app import create_app, db
from app.models import Trade, Instrument
import sqlite3


def fix_missing_instruments():
    """Fix trades that have no instrument data at all"""
    app = create_app()

    with app.app_context():
        print("🔧 Fixing Trades with Missing Instrument Data")
        print("=" * 50)

        # Step 1: Check if there's an old 'instrument' column in the database
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        print(f"📁 Database: {db_path}")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check table schema
            cursor.execute("PRAGMA table_info(trade);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            print(f"📋 Available columns: {column_names}")

            has_old_instrument = 'instrument' in column_names

            if has_old_instrument:
                print("\n💡 Found old 'instrument' column - checking data...")

                # Check what data is in the old instrument column
                cursor.execute("SELECT DISTINCT instrument FROM trade WHERE instrument IS NOT NULL;")
                old_instruments = cursor.fetchall()

                print("🔍 Distinct values in old 'instrument' column:")
                for instr in old_instruments:
                    print(f"   '{instr[0]}'")

                # Count trades with data in old column but missing new columns
                cursor.execute("""
                    SELECT COUNT(*) FROM trade 
                    WHERE instrument IS NOT NULL 
                    AND (instrument_id IS NULL AND instrument_legacy IS NULL)
                """)
                orphaned_count = cursor.fetchone()[0]

                print(f"\n📊 Found {orphaned_count} trades with old instrument data but missing new instrument fields")

                if orphaned_count > 0:
                    print("\n🔄 Migrating old instrument data...")

                    # Get the mapping of values to proper symbols
                    value_mapping = {
                        'NQ': 'NQ',
                        'ES': 'ES',
                        'YM': 'YM',
                        'MNQ': 'MNQ',
                        'MES': 'MES',
                        'MYM': 'MYM',
                        '1': 'NQ',  # Legacy numeric mappings
                        '2': 'ES',
                        '3': 'YM',
                        'None': None,
                        'null': None,
                        '': None
                    }

                    # Update each distinct value
                    for old_value, in old_instruments:
                        if old_value in value_mapping:
                            new_symbol = value_mapping[old_value]

                            if new_symbol:
                                print(f"   Migrating '{old_value}' -> '{new_symbol}'...")

                                # Update instrument_legacy for these trades
                                cursor.execute("""
                                    UPDATE trade 
                                    SET instrument_legacy = ? 
                                    WHERE instrument = ? 
                                    AND (instrument_id IS NULL AND instrument_legacy IS NULL)
                                """, (new_symbol, old_value))

                                updated = cursor.rowcount
                                print(f"     📝 Updated {updated} trades")
                            else:
                                print(f"   Skipping NULL/empty value: '{old_value}'")
                        else:
                            print(f"   ⚠️  Unknown value: '{old_value}' - needs manual mapping")

                    conn.commit()
                    print("✅ Migration complete")

            else:
                print("❌ No old 'instrument' column found")
                print("💡 Trades may need manual instrument assignment")

            conn.close()

        except Exception as e:
            print(f"❌ Database error: {e}")
            return False

        # Step 2: Now use SQLAlchemy to link the migrated data
        print("\n🔗 Linking migrated instrument data...")

        # Get trades that now have instrument_legacy but no instrument_id
        unlinked_trades = Trade.query.filter(
            Trade.instrument_id.is_(None),
            Trade.instrument_legacy.isnot(None)
        ).all()

        print(f"📊 Found {len(unlinked_trades)} trades to link")

        linked_count = 0
        for trade in unlinked_trades:
            symbol = trade.instrument_legacy.upper()

            # Find matching instrument
            instrument = Instrument.query.filter_by(symbol=symbol, is_active=True).first()

            if instrument:
                trade.instrument_id = instrument.id
                linked_count += 1
            else:
                print(f"   ⚠️  No instrument found for symbol: '{symbol}' (Trade {trade.id})")

        if linked_count > 0:
            db.session.commit()
            print(f"✅ Linked {linked_count} additional trades")

        # Step 3: Check remaining orphaned trades
        print("\n📊 Checking remaining orphaned trades...")

        orphaned_trades = Trade.query.filter(
            Trade.instrument_id.is_(None),
            Trade.instrument_legacy.is_(None)
        ).all()

        print(f"❌ Still {len(orphaned_trades)} trades with no instrument data")

        if len(orphaned_trades) > 0:
            print("\n💡 Sample orphaned trades (first 10):")
            for trade in orphaned_trades[:10]:
                print(f"   Trade {trade.id}: Date {trade.trade_date}, Direction {trade.direction}")

            print(f"\n🤔 Options for remaining {len(orphaned_trades)} trades:")
            print("   1. Assign them all to a default instrument (e.g., NQ)")
            print("   2. Delete them if they're test/invalid data")
            print("   3. Leave them for manual assignment")

            # Offer to assign default instrument
            print("\n❓ Assign default instrument 'NQ' to all orphaned trades? (y/n)")
            # For automated script, let's not assign by default
            print("   Skipping auto-assignment. Run manual assignment if needed.")

        # Step 4: Final verification
        print("\n🧪 Final Verification:")

        total_trades = Trade.query.count()
        with_instrument_obj = Trade.query.filter(Trade.instrument_id.isnot(None)).count()
        with_legacy_only = Trade.query.filter(
            Trade.instrument_id.is_(None),
            Trade.instrument_legacy.isnot(None)
        ).count()
        orphaned = Trade.query.filter(
            Trade.instrument_id.is_(None),
            Trade.instrument_legacy.is_(None)
        ).count()

        print(f"   📊 Total trades: {total_trades}")
        print(f"   ✅ With proper instrument_obj: {with_instrument_obj}")
        print(f"   ⚠️  With legacy only: {with_legacy_only}")
        print(f"   ❌ Orphaned (no instrument): {orphaned}")

        success = orphaned < 50  # Success if we got most of them

        print(f"\n🎯 Fix {'SUCCESSFUL' if success else 'PARTIAL'}!")

        if success:
            print("🚀 Most trades now have proper instrument data!")
            print("   Restart your Flask app and check the trade pages.")
        else:
            print("⚠️  Some trades still need instrument assignment.")
            print("   Consider running manual assignment for orphaned trades.")

        return success


def assign_default_instrument_to_orphans():
    """Assign NQ as default instrument to all orphaned trades"""
    app = create_app()

    with app.app_context():
        print("🔧 Assigning Default Instrument to Orphaned Trades")

        # Get NQ instrument
        nq_instrument = Instrument.query.filter_by(symbol='NQ', is_active=True).first()

        if not nq_instrument:
            print("❌ NQ instrument not found!")
            return False

        # Get orphaned trades
        orphaned_trades = Trade.query.filter(
            Trade.instrument_id.is_(None),
            Trade.instrument_legacy.is_(None)
        ).all()

        print(f"📊 Assigning NQ to {len(orphaned_trades)} orphaned trades...")

        for trade in orphaned_trades:
            trade.instrument_id = nq_instrument.id
            trade.instrument_legacy = 'NQ'

        db.session.commit()

        print(f"✅ Assigned NQ to {len(orphaned_trades)} trades")
        return True


if __name__ == "__main__":
    print("Choose an option:")
    print("1. Migrate old instrument data (recommended)")
    print("2. Assign NQ to all orphaned trades")
    print("3. Both")

    choice = input("Enter choice (1-3): ").strip()

    if choice in ['1', '3']:
        fix_missing_instruments()

    if choice in ['2', '3']:
        assign_default_instrument_to_orphans()

    print("\n🎉 Done! Restart your Flask app to see the changes.")