from app import create_app, db
import sqlite3
import os

app = create_app()

with app.app_context():
    # Get database file path
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"📊 Database URI: {db_uri}")

    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')

        # Check if file exists
        if not os.path.exists(db_path):
            print(f"❌ Database file does not exist: {db_path}")
            print("🔧 Try running: flask db upgrade")
        else:
            print(f"✅ Found database file: {db_path}")

            try:
                # Connect directly to SQLite to check actual table structure
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='p12_scenario'")
                table_exists = cursor.fetchone()

                if not table_exists:
                    print("❌ Table 'p12_scenario' does not exist!")
                    print("🔧 Run: flask db upgrade")
                else:
                    print("✅ Table 'p12_scenario' exists")

                    # Get table info
                    cursor.execute("PRAGMA table_info(p12_scenario)")
                    columns = cursor.fetchall()

                    print(f"\n🔍 Found {len(columns)} columns in p12_scenario table:")
                    for column in columns:
                        print(f"  - {column[1]} ({column[2]})")

                conn.close()

            except Exception as e:
                print(f"❌ Error checking database: {e}")

    print("\n✅ Expected columns based on your model:")
    print("  - scenario_name (not 'name')")
    print("  - scenario_number")
    print("  - short_description")
    print("  - etc...")