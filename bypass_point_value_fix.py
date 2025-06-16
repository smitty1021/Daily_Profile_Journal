# Step 2.11: Bypass the point_value property issue with direct database update
# Save this as bypass_point_value_fix.py and run it

from app import create_app, db
import sqlite3


def bypass_point_value_fix():
    """Bypass the point_value property issue by updating the database directly"""
    app = create_app()

    with app.app_context():
        print("🔧 Bypassing point_value property issue...")

        # Get the database file path
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")

        try:
            # Connect directly to SQLite to update trades
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check current state of trades
            print("🔍 Checking current trade point values...")
            cursor.execute("SELECT COUNT(*) FROM trade WHERE point_value IS NULL OR point_value = 0")
            trades_needing_update = cursor.fetchone()[0]
            print(f"📊 Found {trades_needing_update} trades needing point value updates")

            if trades_needing_update > 0:
                print("🔄 Updating trades with correct point values...")

                # Update NQ trades
                cursor.execute(
                    "UPDATE trade SET point_value = 20.0 WHERE instrument = 'NQ' AND (point_value IS NULL OR point_value = 0)")
                nq_updated = cursor.rowcount
                print(f"  📝 Updated {nq_updated} NQ trades -> $20.0")

                # Update ES trades
                cursor.execute(
                    "UPDATE trade SET point_value = 50.0 WHERE instrument = 'ES' AND (point_value IS NULL OR point_value = 0)")
                es_updated = cursor.rowcount
                print(f"  📝 Updated {es_updated} ES trades -> $50.0")

                # Update YM trades
                cursor.execute(
                    "UPDATE trade SET point_value = 5.0 WHERE instrument = 'YM' AND (point_value IS NULL OR point_value = 0)")
                ym_updated = cursor.rowcount
                print(f"  📝 Updated {ym_updated} YM trades -> $5.0")

                # Update MNQ trades
                cursor.execute(
                    "UPDATE trade SET point_value = 2.0 WHERE instrument = 'MNQ' AND (point_value IS NULL OR point_value = 0)")
                mnq_updated = cursor.rowcount
                print(f"  📝 Updated {mnq_updated} MNQ trades -> $2.0")

                # Update MES trades
                cursor.execute(
                    "UPDATE trade SET point_value = 5.0 WHERE instrument = 'MES' AND (point_value IS NULL OR point_value = 0)")
                mes_updated = cursor.rowcount
                print(f"  📝 Updated {mes_updated} MES trades -> $5.0")

                # Update MYM trades
                cursor.execute(
                    "UPDATE trade SET point_value = 0.5 WHERE instrument = 'MYM' AND (point_value IS NULL OR point_value = 0)")
                mym_updated = cursor.rowcount
                print(f"  📝 Updated {mym_updated} MYM trades -> $0.5")

                # Update any other instruments to 1.0
                cursor.execute(
                    "UPDATE trade SET point_value = 1.0 WHERE instrument NOT IN ('NQ', 'ES', 'YM', 'MNQ', 'MES', 'MYM') AND (point_value IS NULL OR point_value = 0)")
                other_updated = cursor.rowcount
                print(f"  📝 Updated {other_updated} other trades -> $1.0")

                total_updated = nq_updated + es_updated + ym_updated + mnq_updated + mes_updated + mym_updated + other_updated
                print(f"✅ Total trades updated: {total_updated}")
            else:
                print("✅ All trades already have point values")

            # Commit the changes
            conn.commit()

            # Verify the update
            print("🧪 Verifying updates...")
            cursor.execute(
                "SELECT instrument, point_value, COUNT(*) FROM trade GROUP BY instrument, point_value ORDER BY instrument")
            results = cursor.fetchall()

            print("📊 Current trade point values by instrument:")
            for instrument, point_value, count in results:
                print(f"   {instrument}: ${point_value} ({count} trades)")

            conn.close()

            print("🎉 Point value fix complete! Now let's test the trades page.")
            return True

        except Exception as e:
            print(f"❌ Error during bypass fix: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = bypass_point_value_fix()
    if success:
        print("\n🚀 Point values fixed! Now:")
        print("1. Restart your Flask app")
        print("2. Try accessing: http://localhost:5000/trades/")
        print("3. The gross_pnl property should now work correctly")
    else:
        print("\n💥 Bypass fix failed. Check the error messages above.")