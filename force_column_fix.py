# Step 2.21: Force fix the point_value column issue
# Save this as force_column_fix.py and run it

import sqlite3
import os
from app import create_app, db


def force_column_fix():
    """Force fix the point_value column by rebuilding the table properly"""

    app = create_app()

    with app.app_context():
        print("🔧 Force fixing the point_value column issue...")

        # Get database path
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_path = db_uri.replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check current trade table schema
            print("\n🔍 Current schema:")
            cursor.execute("PRAGMA table_info(trade);")
            current_columns = cursor.fetchall()
            for col in current_columns:
                print(f"   {col[1]} {col[2]}")

            current_column_names = [col[1] for col in current_columns]

            # The issue might be that the column exists in some metadata but not properly
            # Let's try to drop and recreate the point_value column
            if 'point_value' in current_column_names:
                print("\n🗑️ Dropping problematic point_value column...")
                # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table

                # Step 1: Create a new table without point_value
                print("🏗️ Creating temporary table...")
                cursor.execute("""
                    CREATE TABLE trade_temp AS 
                    SELECT id, instrument_id, instrument_legacy, trade_date, direction,
                           initial_stop_loss, terminus_target, is_dca, mae, mfe,
                           trade_notes, how_closed, news_event, rules_rating,
                           management_rating, target_rating, entry_rating,
                           preparation_rating, psych_scored_highest, psych_scored_lowest,
                           overall_analysis_notes, screenshot_link, trade_management_notes,
                           errors_notes, improvements_notes, tags, trading_model_id, user_id
                    FROM trade
                """)

                # Step 2: Drop the original table
                print("🗑️ Dropping original trade table...")
                cursor.execute("DROP TABLE trade")

                # Step 3: Create the new table with proper schema
                print("🏗️ Creating new trade table with proper schema...")
                cursor.execute("""
                    CREATE TABLE trade (
                        id INTEGER PRIMARY KEY,
                        instrument_id INTEGER,
                        instrument_legacy VARCHAR(10),
                        trade_date DATE NOT NULL,
                        direction VARCHAR(5) NOT NULL,
                        point_value FLOAT DEFAULT 1.0,
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
                        user_id INTEGER NOT NULL
                    );
                """)

                # Step 4: Copy data back from temp table
                print("🔄 Copying data back...")
                cursor.execute("""
                    INSERT INTO trade (id, instrument_id, instrument_legacy, trade_date, direction,
                                     initial_stop_loss, terminus_target, is_dca, mae, mfe,
                                     trade_notes, how_closed, news_event, rules_rating,
                                     management_rating, target_rating, entry_rating,
                                     preparation_rating, psych_scored_highest, psych_scored_lowest,
                                     overall_analysis_notes, screenshot_link, trade_management_notes,
                                     errors_notes, improvements_notes, tags, trading_model_id, user_id)
                    SELECT id, instrument_id, instrument_legacy, trade_date, direction,
                           initial_stop_loss, terminus_target, is_dca, mae, mfe,
                           trade_notes, how_closed, news_event, rules_rating,
                           management_rating, target_rating, entry_rating,
                           preparation_rating, psych_scored_highest, psych_scored_lowest,
                           overall_analysis_notes, screenshot_link, trade_management_notes,
                           errors_notes, improvements_notes, tags, trading_model_id, user_id
                    FROM trade_temp
                """)

                # Step 5: Drop temp table
                print("🧹 Cleaning up temporary table...")
                cursor.execute("DROP TABLE trade_temp")

            else:
                print("\n➕ Adding point_value column...")
                cursor.execute("ALTER TABLE trade ADD COLUMN point_value FLOAT DEFAULT 1.0;")

            # Commit changes
            conn.commit()

            # Verify the new schema
            print("\n✅ New schema:")
            cursor.execute("PRAGMA table_info(trade);")
            new_columns = cursor.fetchall()
            for col in new_columns:
                print(f"   {col[1]} {col[2]}")

            new_column_names = [col[1] for col in new_columns]
            if 'point_value' in new_column_names:
                print("✅ point_value column now exists!")
            else:
                print("❌ point_value column still missing!")

            # Check row count
            cursor.execute("SELECT COUNT(*) FROM trade")
            row_count = cursor.fetchone()[0]
            print(f"\n📊 Trade table has {row_count} rows")

            conn.close()

            print("\n🎉 Force column fix complete!")
            print("🚀 Now restart your Flask app and try accessing /trades/")
            return True

        except Exception as e:
            print(f"❌ Error during force fix: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = force_column_fix()
    if not success:
        print("\n💥 Force fix failed. Check the error messages above.")