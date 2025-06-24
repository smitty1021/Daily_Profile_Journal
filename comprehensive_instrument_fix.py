# comprehensive_instrument_fix.py
# This will check and fix the instrument display issue across all pages

from app import create_app, db
from app.models import Trade, Instrument


def comprehensive_instrument_fix():
    """Check and fix all instrument display issues"""
    app = create_app()

    with app.app_context():
        print("🔍 Comprehensive Instrument Fix")
        print("=" * 50)

        # Step 1: Check current state of all trades
        print("\n📊 Current Trade Instrument Status:")
        all_trades = Trade.query.all()

        trades_with_obj = 0
        trades_with_legacy_only = 0
        trades_with_numeric_legacy = 0

        for trade in all_trades:
            if trade.instrument_obj:
                trades_with_obj += 1
            elif trade.instrument_legacy:
                trades_with_legacy_only += 1
                if trade.instrument_legacy.isdigit():
                    trades_with_numeric_legacy += 1

        print(f"   ✅ Trades with proper instrument_obj: {trades_with_obj}")
        print(f"   ⚠️  Trades with only legacy data: {trades_with_legacy_only}")
        print(f"   ❌ Trades with numeric legacy: {trades_with_numeric_legacy}")

        # Step 2: Check available instruments
        print("\n🏦 Available Instruments:")
        instruments = Instrument.query.filter_by(is_active=True).all()
        for instr in instruments:
            print(f"   ID {instr.id}: {instr.symbol} ({instr.name})")

        # Step 3: Fix numeric legacy values
        if trades_with_numeric_legacy > 0:
            print(f"\n🔧 Fixing {trades_with_numeric_legacy} trades with numeric legacy values...")

            # Mapping based on your Instrument table
            id_to_symbol_map = {
                '1': 'NQ',  # Instrument ID 1 = NQ
                '2': 'ES',  # Instrument ID 2 = ES
                '3': 'YM',  # Instrument ID 3 = YM
            }

            fixed_count = 0
            for trade in all_trades:
                if trade.instrument_legacy and trade.instrument_legacy.isdigit():
                    legacy_id = trade.instrument_legacy

                    if legacy_id in id_to_symbol_map:
                        symbol = id_to_symbol_map[legacy_id]

                        # Find the instrument by symbol
                        instrument = Instrument.query.filter_by(symbol=symbol, is_active=True).first()

                        if instrument:
                            # Link to proper instrument
                            trade.instrument_id = instrument.id
                            trade.instrument_legacy = symbol  # Also update legacy to symbol

                            print(
                                f"   Fixed Trade {trade.id}: '{legacy_id}' -> {symbol} (instrument_id: {instrument.id})")
                            fixed_count += 1
                        else:
                            print(f"   ❌ No instrument found for symbol: {symbol}")
                    else:
                        print(f"   ❌ Unknown numeric legacy ID: {legacy_id} (Trade {trade.id})")

            print(f"   ✅ Fixed {fixed_count} trades")

        # Step 4: Fix trades with legacy symbols but no instrument_id
        print("\n🔗 Linking trades with symbol-based legacy data...")

        unlinked_count = 0
        linked_count = 0

        for trade in all_trades:
            if trade.instrument_id is None and trade.instrument_legacy:
                symbol = trade.instrument_legacy.upper()

                # Find matching instrument
                instrument = Instrument.query.filter_by(symbol=symbol, is_active=True).first()

                if instrument:
                    trade.instrument_id = instrument.id
                    print(f"   Linked Trade {trade.id}: '{symbol}' -> instrument_id {instrument.id}")
                    linked_count += 1
                else:
                    print(f"   ❌ No instrument found for symbol: '{symbol}' (Trade {trade.id})")
                    unlinked_count += 1

        print(f"   ✅ Linked {linked_count} trades")
        if unlinked_count > 0:
            print(f"   ⚠️  {unlinked_count} trades still unlinked")

        # Step 5: Commit all changes
        try:
            db.session.commit()
            print("\n💾 All changes committed to database")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing changes: {e}")
            return False

        # Step 6: Verify specific trades
        print("\n🧪 Verifying specific trades...")
        test_trade_ids = [187, 186, 185]  # Test the trades from your screenshots

        for trade_id in test_trade_ids:
            trade = Trade.query.get(trade_id)
            if trade:
                print(f"\nTrade {trade_id}:")
                print(f"   instrument_id: {trade.instrument_id}")
                print(f"   instrument_legacy: {trade.instrument_legacy}")
                print(f"   instrument_obj: {trade.instrument_obj}")
                print(f"   instrument property: {trade.instrument}")
                if trade.instrument_obj:
                    print(f"   symbol: {trade.instrument_obj.symbol}")

        # Step 7: Final status check
        print("\n📈 Final Status:")
        final_trades = Trade.query.all()
        final_with_obj = sum(1 for t in final_trades if t.instrument_obj)
        final_with_legacy_only = sum(1 for t in final_trades if not t.instrument_obj and t.instrument_legacy)
        final_broken = sum(1 for t in final_trades if not t.instrument_obj and not t.instrument_legacy)

        print(f"   ✅ Trades with proper instrument_obj: {final_with_obj}")
        print(f"   ⚠️  Trades with only legacy data: {final_with_legacy_only}")
        print(f"   ❌ Trades with no instrument data: {final_broken}")

        success = final_broken == 0 and final_with_obj > trades_with_obj
        print(f"\n🎯 Fix {'SUCCESSFUL' if success else 'NEEDS MORE WORK'}!")

        return success


if __name__ == "__main__":
    success = comprehensive_instrument_fix()
    if success:
        print("\n🚀 Restart your Flask app and check the pages!")
        print("   All trades should now show proper instrument symbols instead of numbers.")
    else:
        print("\n⚠️  Some issues remain. Check the output above for details.")