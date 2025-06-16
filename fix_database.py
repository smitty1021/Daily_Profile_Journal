import sqlite3
import os
import sys


def find_database_file():
    """Try to find the SQLite database file"""
    possible_paths = [
        'instance/app.db',
        'app.db',
        'database.db',
        'instance/database.db',
        'instance/trading_journal.db'
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def add_point_value_column():
    """Add the missing point_value column to trade table"""

    # Try to find the database
    db_path = find_database_file()

    if not db_path:
        print("❌ Could not find database file automatically.")
        db_path = input("Please enter the path to your SQLite database file: ").strip()

        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False

    print(f"📂 Found database: {db_path}")

    try:
        # Backup the database first
        backup_path = db_path + '.backup'
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"💾 Created backup: {backup_path}")

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current schema
        cursor.execute("PRAGMA table_info(trade)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Current trade table columns: {columns}")

        if 'point_value' in columns:
            print("✅ point_value column already exists!")
            return True

        # Add the missing column
        print("🔨 Adding point_value column...")
        cursor.execute("ALTER TABLE trade ADD COLUMN point_value REAL")

        # Update existing trades with appropriate point values
        print("📊 Updating existing trades with point values...")

        # First, let's see what instruments we have
        cursor.execute("SELECT DISTINCT instrument_legacy FROM trade WHERE instrument_legacy IS NOT NULL")
        existing_instruments = cursor.fetchall()
        print(f"🎯 Found instruments: {[inst[0] for inst in existing_instruments]}")

        # Update with Random's point values
        update_sql = """
            UPDATE trade 
            SET point_value = CASE 
                WHEN UPPER(instrument_legacy) = 'NQ' THEN 20.0
                WHEN UPPER(instrument_legacy) = 'ES' THEN 50.0
                WHEN UPPER(instrument_legacy) = 'YM' THEN 5.0
                WHEN UPPER(instrument_legacy) = 'MNQ' THEN 2.0
                WHEN UPPER(instrument_legacy) = 'MES' THEN 5.0
                WHEN UPPER(instrument_legacy) = 'MYM' THEN 0.5
                WHEN UPPER(instrument_legacy) = 'ENQ' THEN 5.0
                WHEN UPPER(instrument_legacy) = 'EES' THEN 12.5
                WHEN UPPER(instrument_legacy) = 'EYM' THEN 12.5
                WHEN UPPER(instrument_legacy) = 'ERX' THEN 6.25
                ELSE 1.0
            END
            WHERE point_value IS NULL
        """

        cursor.execute(update_sql)
        updated_rows = cursor.rowcount

        # Commit changes
        conn.commit()

        print(f"✅ Successfully added point_value column!")
        print(f"✅ Updated {updated_rows} existing trades with point values")

        # Verify the change
        cursor.execute("PRAGMA table_info(trade)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Updated trade table columns: {new_columns}")

        # Show some sample data
        cursor.execute("""
            SELECT instrument_legacy, point_value, COUNT(*) as count 
            FROM trade 
            WHERE instrument_legacy IS NOT NULL 
            GROUP BY instrument_legacy, point_value
        """)
        sample_data = cursor.fetchall()
        if sample_data:
            print("\n📊 Point values assigned:")
            for inst, pv, count in sample_data:
                print(f"   {inst}: ${pv}/point ({count} trades)")

        return True

    except Exception as e:
        print(f"❌ Error updating database: {e}")
        print("💡 Try running the Flask migration instead:")
        print("   flask db migrate -m 'Add point_value column'")
        print("   flask db upgrade")
        return False

    finally:
        if 'conn' in locals():
            conn.close()


def main():
    print("🚀 Quick Fix: Adding point_value column to trade table")
    print("=" * 50)

    if add_point_value_column():
        print("\n🎉 SUCCESS! Your database has been updated.")
        print("🔄 You can now restart your Flask application.")
        print("\n💡 Next steps:")
        print("   1. Restart your Flask app")
        print("   2. Test the /trades/ page")
        print("   3. Consider setting up Flask-Migrate for future schema changes")
    else:
        print("\n❌ Failed to update database.")
        print("🔧 Alternative solutions:")
        print("   1. Use Flask-Migrate: flask db migrate && flask db upgrade")
        print("   2. Temporarily comment out the point_value column in your model")
        print("   3. Recreate the database (development only)")


if __name__ == "__main__":
    main()