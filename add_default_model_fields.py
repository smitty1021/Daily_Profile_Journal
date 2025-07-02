#!/usr/bin/env python3
"""
Add default model fields to trading_model table
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db


def upgrade_database():
    """Add new columns to trading_model table"""
    app = create_app()

    with app.app_context():
        try:
            # Add the new columns to the trading_model table
            with db.engine.connect() as conn:
                # Add is_default column
                conn.execute(db.text("""
                    ALTER TABLE trading_model 
                    ADD COLUMN is_default BOOLEAN NOT NULL DEFAULT 0
                """))

                # Add created_by_admin_user_id column
                conn.execute(db.text("""
                    ALTER TABLE trading_model 
                    ADD COLUMN created_by_admin_user_id INTEGER
                """))

                # Add foreign key constraint (optional for SQLite)
                # Note: SQLite has limited ALTER TABLE support for foreign keys

                conn.commit()

            print("✅ Successfully added new columns to trading_model table")
            print("   - is_default (BOOLEAN)")
            print("   - created_by_admin_user_id (INTEGER)")

        except Exception as e:
            print(f"❌ Error upgrading database: {e}")
            raise


if __name__ == "__main__":
    upgrade_database()