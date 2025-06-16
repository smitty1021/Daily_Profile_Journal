# Step 2.15: Direct fix for the missing point_value column
# Save this as direct_column_fix.py and run it

import sqlite3
import os


def direct_column_fix():
    """Add the missing point_value column directly to the database"""

    # Common database paths - adjust if yours is different
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
        print("❌ Could not find database file. Please check the path.")
        print("🔍 Looked for:", possible_paths)
        return False

    print(f"📁 Found database at: {db_path}")

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if trade table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trade';")
        if not cursor.fetchone():
            print("❌ Trade table not found!")
            return False

        print("✅ Trade table found")

        # Check current schema
        print("\n🔍 Current trade table schema:")
        cursor.execute("PRAGMA table_info(trade);")
        columns = cursor.fetchall()
        column_names = []
        for col in columns:
            column_names.append(col[1])
            print(f"   {col[1]} {col[2]}")

        # Check if point_value column exists
        if 'point_value' in column_names:
            print("✅ point_value column already exists!")
        else:
            print("\n➕ Adding point_value column...")
            cursor.execute("ALTER TABLE trade ADD COLUMN point_value FLOAT;")
            print("✅ Added point_value column")

        # Check if instrument column exists (for populating point values)
        has_instrument = 'instrument' in column_names
        has_instrument_legacy = 'instrument_legacy' in column_names
        has_instrument_id = 'instrument_id' in column_names

        print(f"\n📊 Instrument columns found:")
        print(f"   instrument: {has_instrument}")
        print(f"   instrument_legacy: {has_instrument_legacy}")
        print(f"   instrument_id: {has_instrument_id}")

        # Add instrument column if it doesn't exist but instrument_legacy does
        if not has_instrument and has_instrument_legacy:
            print("➕ Adding instrument column...")
            cursor.execute("ALTER TABLE trade ADD COLUMN instrument VARCHAR(10);")
            cursor.execute("UPDATE trade SET instrument = instrument_legacy WHERE instrument_legacy IS NOT NULL;")
            print("✅ Added instrument column and copied from instrument_legacy")
            has_instrument = True

        # Now populate point values if we have instrument data
        if has_instrument:
            print("\n🔄 Setting point values based on instruments...")

            # Check how many trades need point values
            cursor.execute("SELECT COUNT(*) FROM trade WHERE point_value IS NULL")
            trades_needing_update = cursor.fetchone()[0]
            print(f"📊 Found {trades_needing_update} trades needing point values")

            if trades_needing_update > 0:
                # Update each instrument type
                updates = [
                    ('NQ', 20.0),
                    ('ES', 50.0),
                    ('YM', 5.0),
                    ('MNQ', 2.0),
                    ('MES', 5.0),
                    ('MYM', 0.5)
                ]

                total_updated = 0
                for instrument, point_value in updates:
                    cursor.execute(
                        "UPDATE trade SET point_value = ? WHERE instrument = ? AND point_value IS NULL",
                        (point_value, instrument)
                    )
                    updated = cursor.rowcount
                    if updated > 0:
                        print(f"  📝 Updated {updated} {instrument} trades -> ${point_value}")
                        total_updated += updated

                # Set remaining trades to 1.0
                cursor.execute("UPDATE trade SET point_value = 1.0 WHERE point_value IS NULL")
                remaining = cursor.rowcount
                if remaining > 0:
                    print(f"  📝 Updated {remaining} other trades -> $1.0")
                    total_updated += remaining

                print(f"✅ Total trades updated: {total_updated}")
            else:
                print("✅ All trades already have point values")
        else:
            print("⚠️ No instrument column found - setting all point values to 1.0")
            cursor.execute("UPDATE trade SET point_value = 1.0 WHERE point_value IS NULL")
            updated = cursor.rowcount
            print(f"📝 Updated {updated} trades with default point value")

        # Commit changes
        conn.commit()

        # Verify the fix
        print("\n🧪 Verifying the fix...")
        cursor.execute("PRAGMA table_info(trade);")
        columns = cursor.fetchall()
        point_value_exists = any(col[1] == 'point_value' for col in columns)

        if point_value_exists:
            cursor.execute("SELECT COUNT(*) FROM trade WHERE point_value IS NOT NULL")
            trades_with_point_values = cursor.fetchone()[0]
            print(f"✅ point_value column exists with {trades_with_point_values} populated trades")
        else:
            print("❌ point_value column still missing!")
            return False

        conn.close()

        print("\n🎉 Database fix complete!")
        print("🚀 Now restart your Flask app and try accessing /trades/")
        return True

    except Exception as e:
        print(f"❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = direct_column_fix()
    if not success:
        print("\n💥 Fix failed. Please check the error messages above.")
        print("📝 You may need to manually locate your database file.")