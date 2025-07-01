from app import create_app, db
from app.models import Trade


def populate_pnl_column():
    """Populate the new pnl column for all existing trades"""
    app = create_app()
    with app.app_context():
        trades = Trade.query.all()
        print(f"Updating P&L for {len(trades)} trades...")

        updated_count = 0
        for i, trade in enumerate(trades):
            old_pnl = trade.pnl
            new_pnl = trade.calculate_and_store_pnl()
            updated_count += 1

            if i % 50 == 0:  # Show progress every 50 trades
                db.session.commit()
                print(f"Updated {i} trades...")

            if i < 5:  # Show first 5 for verification
                print(f"Trade {trade.id}: {old_pnl} -> {new_pnl}")

        db.session.commit()
        print(f"✅ All {updated_count} trades updated!")


if __name__ == "__main__":
    populate_pnl_column()