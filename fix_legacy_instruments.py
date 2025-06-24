from app import create_app, db
from app.models import Trade, Instrument


def fix_legacy_instrument_data():
    """Fix trades that have numeric IDs stored as strings in instrument_legacy"""
    app = create_app()

    with app.app_context():
        print("🔍 Checking trades with legacy instrument data...")

        # Mapping of old numeric IDs to symbols (based on your screenshot)
        id_to_symbol_map = {
            '1': 'NQ',  # Instrument ID 1 = NQ
            '2': 'ES',  # Instrument ID 2 = ES
            '3': 'YM',  # Add more as needed
        }

        # Get all trades with instrument_legacy containing numeric IDs
        trades_to_fix = Trade.query.filter(
            Trade.instrument_id.is_(None),
            Trade.instrument_legacy.isnot(None)
        ).all()

        print(f"Found {len(trades_to_fix)} trades to fix")

        fixed_count = 0
        for trade in trades_to_fix:
            legacy_value = str(trade.instrument_legacy).strip()

            # Check if it's a numeric ID that needs mapping
            if legacy_value in id_to_symbol_map:
                symbol = id_to_symbol_map[legacy_value]

                # Find the instrument in the database
                instrument = Instrument.query.filter_by(symbol=symbol, is_active=True).first()

                if instrument:
                    # Update both the relationship and legacy field
                    trade.instrument_id = instrument.id
                    trade.instrument_legacy = symbol  # Store symbol instead of ID
                    print(f"Fixed trade {trade.id}: '{legacy_value}' -> '{symbol}' (ID: {instrument.id})")
                    fixed_count += 1
                else:
                    print(f"Warning: No instrument found for symbol '{symbol}' (trade {trade.id})")
            else:
                # It's already a symbol, just link it to the instrument
                instrument = Instrument.query.filter_by(symbol=legacy_value.upper(), is_active=True).first()
                if instrument:
                    trade.instrument_id = instrument.id
                    print(f"Linked trade {trade.id}: '{legacy_value}' -> ID {instrument.id}")
                    fixed_count += 1
                else:
                    print(f"No instrument found for symbol: '{legacy_value}' (trade {trade.id})")

        # Commit all changes
        db.session.commit()
        print(f"\n✅ Fixed {fixed_count} trades!")

        # Verify the fix
        print("\n🔍 Verifying trade 187...")
        trade_187 = Trade.query.get(187)
        if trade_187:
            print(f"Trade 187:")
            print(f"  instrument_id: {trade_187.instrument_id}")
            print(f"  instrument_legacy: {trade_187.instrument_legacy}")
            print(f"  instrument_obj: {trade_187.instrument_obj}")
            print(f"  instrument property: {trade_187.instrument}")
            if trade_187.instrument_obj:
                print(f"  symbol: {trade_187.instrument_obj.symbol}")


if __name__ == "__main__":
    fix_legacy_instrument_data()