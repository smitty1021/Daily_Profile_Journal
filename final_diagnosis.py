# Step 2.20: Final diagnosis - check SQLAlchemy metadata vs actual database
# Save this as final_diagnosis.py and run it

import sqlite3
import os
from app import create_app, db


def final_diagnosis():
    """Check what SQLAlchemy thinks vs what's actually in the database"""

    app = create_app()

    with app.app_context():
        print("🔧 Final diagnosis - SQLAlchemy vs Database Reality...")

        # Get database path
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_path = db_uri.replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")

        # Check what's actually in the database file
        print("\n📋 What's ACTUALLY in the database:")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(trade);")
            actual_columns = cursor.fetchall()
            print("   Actual columns in database file:")
            for col in actual_columns:
                print(f"     {col[1]} {col[2]}")

            # Check if point_value really exists
            actual_column_names = [col[1] for col in actual_columns]
            if 'point_value' in actual_column_names:
                print("   ✅ point_value column EXISTS in actual database")
            else:
                print("   ❌ point_value column MISSING in actual database")

            conn.close()

        except Exception as e:
            print(f"   ❌ Error reading database: {e}")

        # Check what SQLAlchemy thinks
        print("\n🔍 What SQLAlchemy thinks:")
        try:
            from app.models import Trade

            print("   SQLAlchemy Trade model columns:")
            for column in Trade.__table__.columns:
                print(f"     {column.name} {column.type}")

            # Check SQLAlchemy metadata
            print(f"   SQLAlchemy table name: {Trade.__tablename__}")
            print(f"   SQLAlchemy thinks table exists: {Trade.__table__.exists(db.engine)}")

        except Exception as e:
            print(f"   ❌ Error reading SQLAlchemy model: {e}")

        # Force SQLAlchemy to refresh metadata
        print("\n🔄 Forcing SQLAlchemy metadata refresh...")
        try:
            # Clear SQLAlchemy metadata cache
            db.metadata.clear()

            # Reflect the actual database schema
            db.metadata.reflect(bind=db.engine)

            print("   ✅ SQLAlchemy metadata cleared and reflected")

            # Check if trade table is now properly reflected
            if 'trade' in db.metadata.tables:
                reflected_trade = db.metadata.tables['trade']
                print("   📋 Reflected trade table columns:")
                for column in reflected_trade.columns:
                    print(f"     {column.name} {column.type}")
            else:
                print("   ❌ Trade table not found in reflected metadata")

        except Exception as e:
            print(f"   ❌ Error reflecting metadata: {e}")

        # Try a direct SQL query through SQLAlchemy
        print("\n🧪 Testing direct SQL query through SQLAlchemy...")
        try:
            result = db.engine.execute("SELECT COUNT(*) FROM trade")
            count = result.fetchone()[0]
            print(f"   ✅ Direct SQL query works: {count} trades found")
        except Exception as e:
            print(f"   ❌ Direct SQL query failed: {e}")

        # Try to create a test trade (this will reveal the exact issue)
        print("\n🧪 Testing Trade model instantiation...")
        try:
            from app.models import Trade
            test_trade = Trade()
            print("   ✅ Trade model can be instantiated")

            # Try to access point_value
            pv = test_trade.point_value
            print(f"   ✅ point_value property accessible: {pv}")

        except Exception as e:
            print(f"   ❌ Trade model issue: {e}")

        print("\n💡 DIAGNOSIS COMPLETE")

        # Provide specific fix based on findings
        print("\n🔧 RECOMMENDED FIX:")
        print("Based on the diagnosis, try these steps in order:")
        print("1. Delete any .pyc files: find . -name '*.pyc' -delete")
        print("2. Clear SQLAlchemy cache: db.metadata.clear()")
        print("3. If that doesn't work, there may be a custom @property in your Trade model")
        print("4. Check your models.py for any @property def point_value methods")


if __name__ == "__main__":
    final_diagnosis()