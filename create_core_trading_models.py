# Create this file: create_core_trading_models.py
# Run this to populate your TradingModel table with Random's core models

from app import create_app, db
from app.models import TradingModel, User, UserRole


def create_core_trading_models():
    """Create the 6 core trading models based on Random's teachings."""
    app = create_app()

    with app.app_context():
        print("🚀 Creating core trading models...")

        # Find or create a system user for these models
        system_user = User.query.filter_by(username='system').first()
        if not system_user:
            # Create system user if it doesn't exist
            system_user = User(
                username='system',
                email='system@tradingjournal.local',
                name='System Administrator',
                role=UserRole.ADMIN,
                is_active=True,
                is_email_verified=True
            )
            system_user.set_password('system123')  # Change this!
            db.session.add(system_user)
            db.session.flush()  # Get the user ID

        # Core trading models based on Random's methodology
        core_models = [
            {
                'name': '0930 Opening Snap',
                'version': '1.0',
                'is_active': True,
                'overview_logic': 'Capitalize on the opening volatility and directional snap that occurs in the first 15 minutes of RTH.',
                'entry_trigger_description': 'Clear directional move (snap/breaker) within first 15 minutes of market open',
                'stop_loss_strategy': 'Structural stop based on opening range violation',
                'take_profit_strategy': 'Target completion by 09:44 EST',
                'optimal_market_conditions': 'Clear P12 scenario support, no pre-market HOD/LOD already established',
                'sub_optimal_market_conditions': 'Extreme chop, P12 scenario 5 (swiping mid), pre-market extremes already in'
            },
            {
                'name': 'HOD/LOD Reversal',
                'version': '1.0',
                'is_active': True,
                'overview_logic': 'Mean reversion trades at statistical high/low of day zones using Four Steps analysis.',
                'entry_trigger_description': 'Price reaches statistical HOD/LOD zone with reversal confirmation',
                'stop_loss_strategy': 'Beyond the statistical zone with structural confirmation',
                'take_profit_strategy': 'Target midpoint reversion or next key level',
                'optimal_market_conditions': 'R1, R2 days or exhausted DWP/DNP, P12 scenario supports reversal',
                'sub_optimal_market_conditions': 'Strong early DWP/DNP against reversal direction, P12 scenario 4'
            },
            {
                'name': 'Captain Backtest',
                'version': '1.0',
                'is_active': True,
                'overview_logic': 'Trend-following model that front-runs NY2 session based on H4 breakouts.',
                'entry_trigger_description': 'H4 range (06:00-09:59) broken by 11:30 EST in direction of trend',
                'stop_loss_strategy': 'Back inside the H4 range with structural confirmation',
                'take_profit_strategy': 'NY2 session targets based on daily range expectations',
                'optimal_market_conditions': 'DWP or DNP classification, clear trend, adequate daily range',
                'sub_optimal_market_conditions': 'Range 1/2 days, insufficient daily range, P12 scenario 5'
            },
            {
                'name': 'P12 Scenario-Based',
                'version': '1.0',
                'is_active': True,
                'overview_logic': 'Framework for trading based on P12 scenario identification between 06:00-08:30 EST.',
                'entry_trigger_description': 'Price interaction with P12 levels per identified scenario logic',
                'stop_loss_strategy': 'Scenario-specific structural levels (typically 0.35% or 0.50%)',
                'take_profit_strategy': 'Scenario-specific targets (typically 0.5% with P12 level targets)',
                'optimal_market_conditions': 'Clear P12 scenario identified, confirmation signals present',
                'sub_optimal_market_conditions': 'No clear scenario by 08:30, extreme news events, compressed P12 range'
            },
            {
                'name': 'Quarterly & 05 Box',
                'version': '1.0',
                'is_active': True,
                'overview_logic': 'Scalping model using hourly quarters and 05 box breakouts during 10:00-14:00 EST.',
                'entry_trigger_description': 'Clear 05 box or Q1 bias with proper market context',
                'stop_loss_strategy': 'Structural levels based on quarter violations',
                'take_profit_strategy': 'Quick scalp targets, quarter-based objectives',
                'optimal_market_conditions': 'Active during 10:00-14:00 EST, clear quarter patterns',
                'sub_optimal_market_conditions': 'Near projected HOD/LOD, daily classification implies fades'
            },
            {
                'name': 'Midnight Open Retracement',
                'version': '1.0',
                'is_active': True,
                'overview_logic': 'Trade retracements back to midnight open level during specific market conditions.',
                'entry_trigger_description': 'Price moves away from midnight open and sets up for retracement',
                'stop_loss_strategy': 'Beyond the retracement failure point',
                'take_profit_strategy': 'Midnight open level or partial profit scaling',
                'optimal_market_conditions': 'Clear separation from midnight open, proper daily context',
                'sub_optimal_market_conditions': 'Price chopping around midnight open, no clear directional bias'
            }
        ]

        created_count = 0
        for model_data in core_models:
            # Check if model already exists
            existing = TradingModel.query.filter_by(
                name=model_data['name'],
                user_id=system_user.id
            ).first()

            if not existing:
                model_data['user_id'] = system_user.id
                model = TradingModel(**model_data)
                db.session.add(model)
                created_count += 1
                print(f"✅ Created: {model_data['name']}")
            else:
                print(f"⏭️  Exists: {model_data['name']}")

        try:
            db.session.commit()
            print(f"🎉 Successfully created {created_count} core trading models!")
            print(f"📊 Total models in database: {TradingModel.query.count()}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating models: {e}")
            raise


if __name__ == "__main__":
    create_core_trading_models()