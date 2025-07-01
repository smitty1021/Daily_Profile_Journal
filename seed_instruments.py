from run import app
from app.models import Instrument
from app import db

# Push app context to work with database
app.app_context().push()

# Check if instruments already exist
if Instrument.query.count() > 0:
    print("Instruments already exist. Skipping seed.")
else:
    # Create default instruments with CORRECT symbols
    instruments_data = [
        {
            'symbol': 'NQ', 'name': 'E-mini NASDAQ-100', 'exchange': 'CME',
            'asset_class': 'Equity Index', 'product_group': 'E-mini Futures',
            'point_value': 20.0, 'tick_size': 0.25, 'currency': 'USD', 'is_active': True
        },
        {
            'symbol': 'ES', 'name': 'E-mini S&P 500', 'exchange': 'CME',
            'asset_class': 'Equity Index', 'product_group': 'E-mini Futures',
            'point_value': 50.0, 'tick_size': 0.25, 'currency': 'USD', 'is_active': True
        },
        {
            'symbol': 'YM', 'name': 'E-mini Dow Jones', 'exchange': 'CME',
            'asset_class': 'Equity Index', 'product_group': 'E-mini Futures',
            'point_value': 5.0, 'tick_size': 1.0, 'currency': 'USD', 'is_active': True
        }
    ]

    for data in instruments_data:
        instrument = Instrument(**data)
        db.session.add(instrument)

    db.session.commit()
    print("✅ Instruments created!")