#!/usr/bin/env python3
"""
Migration script to update trade closure methods to standardized values
Run this script to update all existing trades to use the new standardized closure methods
"""

from app import create_app, db
from app.models import Trade
from sqlalchemy import text


def update_trade_closure_methods():
    """Update all existing trades to use standardized closure methods"""

    app = create_app()

    with app.app_context():
        print("🔧 Starting trade closure methods migration...")

        # Mapping from old values to new standardized values
        closure_mapping = {
            # Old Value -> New Standardized Value
            'Target Hit': 'Closed by Take Profit',
            'TP': 'Closed by Take Profit',
            'Take Profit': 'Closed by Take Profit',
            'Stop Loss': 'Closed by Stop Loss',
            'SL': 'Closed by Stop Loss',
            'Manual Close': 'Closed Manually',
            'Manual': 'Closed Manually',
            'Trailing Stop': 'Closed by Trailing Stop Loss',
            'Trailing SL': 'Closed by Trailing Stop Loss',
            'Time Stop': 'Exited by Time Rule',
            'Time Exit': 'Exited by Time Rule',
            'Risk Management': 'Closed Manually',  # Map to manual since it's a manual decision
            'Partial Scale': 'Still Open / Partially Exited',
            'Breakeven Stop': 'Closed by Stop Loss',  # Technically a stop loss at breakeven
            'None': None,  # Keep as NULL
            'Still Open': 'Still Open / Partially Exited',
        }

        try:
            # Get all unique how_closed values currently in database
            result = db.session.execute(
                text("SELECT DISTINCT how_closed FROM trade WHERE how_closed IS NOT NULL")
            )
            existing_values = [row[0] for row in result.fetchall()]

            print(f"📊 Found {len(existing_values)} unique closure methods in database:")
            for value in existing_values:
                new_value = closure_mapping.get(value, value)
                status = "✅ MAPPED" if value in closure_mapping else "⚠️  UNMAPPED"
                print(f"  {status}: '{value}' -> '{new_value}'")

            print()

            # Count trades that will be updated
            total_trades = db.session.query(Trade).count()
            trades_to_update = 0

            for old_value in closure_mapping.keys():
                count = db.session.query(Trade).filter(Trade.how_closed == old_value).count()
                if count > 0:
                    trades_to_update += count
                    print(f"📝 Will update {count} trades with closure method '{old_value}'")

            print(f"\n📈 Total trades in database: {total_trades}")
            print(f"🔄 Trades to be updated: {trades_to_update}")

            if trades_to_update == 0:
                print("✅ No trades need to be updated!")
                return

            # Confirm before proceeding
            confirm = input(f"\n❓ Do you want to update {trades_to_update} trades? (y/N): ").strip().lower()

            if confirm != 'y':
                print("❌ Migration cancelled by user")
                return

            print("\n🚀 Starting migration...")

            # Perform the updates
            updated_count = 0

            for old_value, new_value in closure_mapping.items():
                trades = Trade.query.filter(Trade.how_closed == old_value).all()

                if trades:
                    print(f"🔄 Updating {len(trades)} trades from '{old_value}' to '{new_value}'...")

                    for trade in trades:
                        trade.how_closed = new_value
                        updated_count += 1

                    # Commit in batches for safety
                    db.session.commit()
                    print(f"✅ Updated {len(trades)} trades")

            print(f"\n🎉 Migration completed successfully!")
            print(f"📊 Total trades updated: {updated_count}")

            # Show final distribution
            print("\n📈 Final closure method distribution:")
            result = db.session.execute(
                text("SELECT how_closed, COUNT(*) FROM trade GROUP BY how_closed ORDER BY COUNT(*) DESC")
            )

            for row in result.fetchall():
                closure_method = row[0] if row[0] else 'NULL'
                count = row[1]
                print(f"  📋 {closure_method}: {count} trades")

        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            raise

        print("\n✅ Migration completed! Your filters should now work correctly.")


if __name__ == "__main__":
    update_trade_closure_methods()