# Step 2.17: Fix the mismatch between your Trade model and the database table
# Save this as fix_model_mismatch.py and run it

import sqlite3
import os


def fix_model_mismatch():
    """Fix the mismatch between the Trade model and database table"""

    db_path = 'app.db'
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False

    print(f"📁 Found database at: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current trade table schema
        print("🔍 Current trade table schema:")
        cursor.execute("PRAGMA table_info(trade);")
        columns = cursor.fetchall()
        current_columns = [col[1] for col in columns]

        for col in columns:
            print(f"   {col[1]} {col[2]}")

        # Based on the SQL error, your model expects these columns that are missing:
        expected_columns = [
            'instrument_id',
            'instrument_legacy',
            'point_value'
        ]

        print(f"\n📋 Columns your model expects: {expected_columns}")
        print(f"📋 Columns we have: {current_columns}")

        # Add missing columns
        missing_columns = []
        for col in expected_columns:
            if col not in current_columns:
                missing_columns.append(col)

        if missing_columns:
            print(f"\n➕ Adding missing columns: {missing_columns}")

            # Add instrument_id if missing
            if 'instrument_id' in missing_columns:
                cursor.execute("ALTER TABLE trade ADD COLUMN instrument_id INTEGER;")
                print("   ✅ Added instrument_id column")

            # Add instrument_legacy if missing
            if 'instrument_legacy' in missing_columns:
                cursor.execute("ALTER TABLE trade ADD COLUMN instrument_legacy VARCHAR(10);")
                print("   ✅ Added instrument_legacy column")

            # Add point_value if missing (though it should exist)
            if 'point_value' in missing_columns:
                cursor.execute("ALTER TABLE trade ADD COLUMN point_value FLOAT DEFAULT 1.0;")
                print("   ✅ Added point_value column")
        else:
            print("✅ All expected columns exist")

        # Now, if we have an 'instrument' column but the model expects 'instrument_legacy',
        # let's copy the data and populate instrument_legacy
        if 'instrument' in current_columns and 'instrument_legacy' in missing_columns:
            print("\n🔄 Copying instrument data to instrument_legacy...")
            cursor.execute("UPDATE trade SET instrument_legacy = instrument WHERE instrument IS NOT NULL;")
            updated = cursor.rowcount
            print(f"   📝 Copied {updated} rows from instrument to instrument_legacy")

        # Commit changes
        conn.commit()

        # Show final schema
        print("\n📋 Final trade table schema:")
        cursor.execute("PRAGMA table_info(trade);")
        final_columns = cursor.fetchall()
        for col in final_columns:
            print(f"   {col[1]} {col[2]}")

        conn.close()

        print("\n🎉 Model/database mismatch fixed!")
        print("🚀 Now restart your Flask app and try accessing /trades/")
        return True

    except Exception as e:
        print(f"❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_model_mismatch()
    if not success:
        print("\n💥 Fix failed. Check the error messages above.")