# Step 2.18: Ultimate fix - recreate the table with exactly the columns SQLAlchemy expects
# Save this as ultimate_database_fix.py and run it

import sqlite3
import os
from app import create_app


def ultimate_database_fix():
    """Recreate the trade table with exactly the columns SQLAlchemy expects"""

    app = create_app()

    with app.app_context():
        print("🔧 Ultimate database fix - recreating trade table...")

        # Find database file
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False

        print(f"📁 Found database at: {db_path}")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if trade table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trade';")
            trade_exists = cursor.fetchone() is not None

            if trade_exists:
                print("🗑️ Dropping existing trade table...")
                # First, backup any existing data
                cursor.execute("SELECT COUNT(*) FROM trade")
                existing_rows = cursor.fetchone()[0]
                print(f"   📊 Found {existing_rows} existing trades")

                if existing_rows > 0:
                    print("   💾 Backing up existing trade data...")
                    cursor.execute("CREATE TABLE trade_backup AS SELECT * FROM trade")

                # Drop the problematic table
                cursor.execute("DROP TABLE trade")
                print("   ✅ Dropped trade table")

            # Create the trade table with EXACTLY the columns SQLAlchemy expects
            # Based on the SQL error, these are the columns your model needs:
            print("🏗️ Creating new trade table with correct schema...")

            create_sql = """
            CREATE TABLE trade (
                id INTEGER PRIMARY KEY,
                instrument_id INTEGER,
                instrument_legacy VARCHAR(10),
                trade_date DATE NOT NULL,
                direction VARCHAR(5) NOT NULL,
                point_value FLOAT,
                initial_stop_loss FLOAT,
                terminus_target FLOAT,
                is_dca BOOLEAN DEFAULT 0,
                mae FLOAT,
                mfe FLOAT,
                trade_notes TEXT,
                how_closed VARCHAR(20),
                news_event VARCHAR(100),
                rules_rating INTEGER,
                management_rating INTEGER,
                target_rating INTEGER,
                entry_rating INTEGER,
                preparation_rating INTEGER,
                psych_scored_highest TEXT,
                psych_scored_lowest TEXT,
                overall_analysis_notes TEXT,
                screenshot_link VARCHAR(255),
                trade_management_notes TEXT,
                errors_notes TEXT,
                improvements_notes TEXT,
                tags VARCHAR(255),
                trading_model_id INTEGER,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (trading_model_id) REFERENCES trading_model(id),
                FOREIGN KEY (user_id) REFERENCES user(id)
            );
            """

            cursor.execute(create_sql)
            print("✅ Created new trade table with correct schema")

            # If we had backup data, restore it
            if trade_exists and existing_rows > 0:
                print("🔄 Restoring backup data...")
                try:
                    # Get columns from backup table
                    cursor.execute("PRAGMA table_info(trade_backup)")
                    backup_columns = [col[1] for col in cursor.fetchall()]

                    # Get columns from new table
                    cursor.execute("PRAGMA table_info(trade)")
                    new_columns = [col[1] for col in cursor.fetchall()]

                    # Find common columns
                    common_columns = [col for col in backup_columns if col in new_columns]
                    print(f"   📋 Common columns: {common_columns}")

                    if common_columns:
                        # Insert data for common columns
                        columns_str = ', '.join(common_columns)
                        cursor.execute(f"INSERT INTO trade ({columns_str}) SELECT {columns_str} FROM trade_backup")
                        restored = cursor.rowcount
                        print(f"   ✅ Restored {restored} trades")

                    # Drop backup table
                    cursor.execute("DROP TABLE trade_backup")

                except Exception as e:
                    print(f"   ⚠️ Could not restore backup data: {e}")
                    print("   📝 You may need to re-enter your trades")

            # Verify the table structure
            print("\n🔍 Final trade table schema:")
            cursor.execute("PRAGMA table_info(trade);")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   {col[1]} {col[2]} (nullable: {not col[3]})")

            # Check row count
            cursor.execute("SELECT COUNT(*) FROM trade")
            final_count = cursor.fetchone()[0]
            print(f"\n📊 Final trade count: {final_count}")

            # Commit all changes
            conn.commit()
            conn.close()

            print("\n🎉 Ultimate database fix complete!")
            print("🚀 Now restart your Flask app and try accessing /trades/")
            return True

        except Exception as e:
            print(f"❌ Error during ultimate fix: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = ultimate_database_fix()
    if not success:
        print("\n💥 Ultimate fix failed. Check the error messages above.")