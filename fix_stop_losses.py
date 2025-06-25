from app import create_app, db
from app.models import Trade
from datetime import datetime


def review_and_fix_stop_losses():
    """Review all trades and fix missing/unrealistic stop losses"""
    app = create_app()

    with app.app_context():
        print("🔍 Reviewing all trades for stop loss issues...")

        # Get all trades
        all_trades = Trade.query.all()

        issues_found = []
        fixed_count = 0

        for trade in all_trades:
            print(f"\n📊 Trade {trade.id}: {trade.instrument} {trade.direction} on {trade.trade_date}")

            # Check if trade has entries
            if not trade.entries.first():
                issues_found.append(f"Trade {trade.id}: No entry points")
                continue

            first_entry = trade.entries.first()
            entry_price = first_entry.entry_price

            print(f"   Entry: {entry_price}")
            print(f"   Current Stop Loss: {trade.initial_stop_loss}")
            print(f"   Dollar Risk Property: {trade.dollar_risk}")

            # Check for missing stop loss
            if trade.initial_stop_loss is None:
                # Suggest realistic stop loss based on instrument
                if trade.instrument == 'NQ':
                    suggested_stop = entry_price - 50 if trade.direction == 'Long' else entry_price + 50
                elif trade.instrument == 'ES':
                    suggested_stop = entry_price - 20 if trade.direction == 'Long' else entry_price + 20
                elif trade.instrument == 'YM':
                    suggested_stop = entry_price - 100 if trade.direction == 'Long' else entry_price + 100
                else:
                    suggested_stop = entry_price * 0.99 if trade.direction == 'Long' else entry_price * 1.01

                print(f"   ❌ MISSING STOP LOSS - Suggested: {suggested_stop}")
                issues_found.append(f"Trade {trade.id}: Missing stop loss (suggested: {suggested_stop})")

                # Uncomment the next two lines to auto-fix:
                # trade.initial_stop_loss = suggested_stop
                # fixed_count += 1

            # Check for unrealistic stop losses
            elif trade.dollar_risk is None:
                print(f"   ⚠️  Dollar risk calculation failed")
                issues_found.append(f"Trade {trade.id}: Dollar risk calculation failed")

            elif trade.dollar_risk == 0:
                print(f"   ⚠️  Zero dollar risk")
                issues_found.append(f"Trade {trade.id}: Zero dollar risk")

            else:
                print(f"   ✅ Stop loss OK - Risk: ${trade.dollar_risk:.2f}")

        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"   Total trades reviewed: {len(all_trades)}")
        print(f"   Issues found: {len(issues_found)}")
        print(f"   Trades fixed: {fixed_count}")

        if issues_found:
            print(f"\n🚨 ISSUES FOUND:")
            for issue in issues_found:
                print(f"   - {issue}")

        # Uncomment to save changes:
        # if fixed_count > 0:
        #     db.session.commit()
        #     print(f"\n✅ Saved {fixed_count} fixes to database")


if __name__ == "__main__":
    review_and_fix_stop_losses()