"""
Database migration to add P12 scenarios functionality
Run this script to add the necessary tables and relationships
"""

from app import create_app, db
from app.models import P12Scenario
from datetime import datetime


def upgrade_database():
    """Add P12 scenarios table and update daily journal."""
    app = create_app()

    with app.app_context():
        print("🚀 Starting P12 scenarios database migration...")

        try:
            # Create P12Scenario table
            db.create_all()
            print("✅ P12Scenario table created")

            # Add p12_scenario_id column to daily_journal table if it doesn't exist
            inspector = db.inspect(db.engine)
            daily_journal_columns = [col['name'] for col in inspector.get_columns('daily_journal')]

            if 'p12_scenario_id' not in daily_journal_columns:
                db.engine.execute("""
                    ALTER TABLE daily_journal 
                    ADD COLUMN p12_scenario_id INTEGER,
                    ADD COLUMN p12_high DECIMAL(10,2),
                    ADD COLUMN p12_mid DECIMAL(10,2), 
                    ADD COLUMN p12_low DECIMAL(10,2),
                    ADD COLUMN p12_notes TEXT
                """)
                print("✅ Added P12 columns to daily_journal table")

                # Add foreign key constraint
                db.engine.execute("""
                    ALTER TABLE daily_journal
                    ADD CONSTRAINT fk_daily_journal_p12_scenario
                    FOREIGN KEY (p12_scenario_id) REFERENCES p12_scenario(id)
                """)
                print("✅ Added foreign key constraint")

            # Initialize default scenarios
            initialize_default_scenarios()

            print("🎉 P12 scenarios migration completed successfully!")

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            raise


def initialize_default_scenarios():
    """Initialize the 5 default P12 scenarios."""
    print("📝 Initializing default P12 scenarios...")

    default_scenarios = [
        {
            'scenario_number': 1,
            'scenario_name': 'P12 Mid Rejection, Stay Outside',
            'short_description': 'Price tests P12 Mid, rejects it, stays outside P12 range',
            'detailed_description': 'Price tests the P12 Mid from either direction, gets rejected, and then stays outside the P12 range (either above P12 High or below P12 Low). This represents a strong directional move that began during the Globex session and continues through the early morning hours.',
            'hod_lod_implication': 'HOD/LOD likely already established during P12 formation (18:00-06:00 EST). The extreme is probably already in from the overnight session.',
            'directional_bias': 'neutral',  # Can be either depending on direction
            'alert_criteria': 'Watch for price to test the P12 Mid level and show rejection (bounce/reversal). Look for clear rejection candlestick patterns or failure to penetrate the midpoint.',
            'confirmation_criteria': 'Breakout and sustained hold beyond P12 High (for longs) or P12 Low (for shorts). Price should not return back into the P12 range.',
            'entry_strategy': 'Enter long on breakout above P12 High after mid rejection, or short on breakdown below P12 Low after mid rejection. Use pullbacks to the P12 High/Low as entry points.',
            'typical_targets': 'Previous day extremes, settlement levels, or statistical daily range extensions (0.5-1.0% moves)',
            'stop_loss_guidance': 'Place stops back inside the P12 range, typically beyond the P12 Mid level',
            'risk_percentage': 0.35,
            'is_active': True
        },
        {
            'scenario_number': 2,
            'scenario_name': 'Look Outside P12 and Fail',
            'short_description': 'Price breaks P12 High/Low but fails, returning aggressively inside',
            'detailed_description': 'Price initially looks above P12 High (or below P12 Low) but then fails to hold, returning back inside the P12 range aggressively, often moving toward the P12 Mid. This represents a false breakout and potential reversal.',
            'hod_lod_implication': 'HOD/LOD likely set by the "look outside" move. The failed breakout often marks the daily extreme.',
            'directional_bias': 'bearish',  # Reversal scenario
            'alert_criteria': 'Price moves outside P12 High/Low but shows immediate weakness and starts sucking back into the range. Look for volume expansion on the failure.',
            'confirmation_criteria': 'Price closes back inside the P12 range and breaches the P12 Mid, confirming the reversal.',
            'entry_strategy': 'Enter short after "look above P12H and fail" - ideally on close back below P12H or break of P12 Mid. Reverse for long entries after failed breakdown.',
            'typical_targets': 'Opposite P12 extreme (P12 Low if failed above, P12 High if failed below), or P12 Mid as interim target',
            'stop_loss_guidance': 'Place stops beyond the failed breakout extreme with some buffer',
            'risk_percentage': 0.50,
            'is_active': True
        },
        {
            'scenario_number': 3,
            'scenario_name': 'Range Between P12 Mid and Extreme, Then Breakout',
            'short_description': 'Price ping-pongs between P12 Mid and P12 High/Low, then breaks out',
            'detailed_description': 'Price initially consolidates between P12 Mid and either P12 High or P12 Low, creating a smaller range within the P12 structure, then decisively breaks out of this sub-range.',
            'hod_lod_implication': 'HOD/LOD likely already established. The breakout direction suggests continuation of the underlying trend.',
            'directional_bias': 'neutral',  # Depends on breakout direction
            'alert_criteria': 'Observe price ranging/consolidating between P12 Mid and one of the extremes (High or Low). Look for multiple tests of these levels.',
            'confirmation_criteria': 'Decisive close above the consolidation range (if bullish breakout) or below (if bearish breakout) with volume confirmation.',
            'entry_strategy': 'Enter on the breakout of the sub-range (P12M-P12H or P12M-P12L). Wait for pullback confirmation or use hourly quarters for precision entries.',
            'typical_targets': 'Extension beyond the P12 range, previous day levels, or statistical daily targets',
            'stop_loss_guidance': 'Place stops back within the consolidation range, typically beyond the P12 Mid',
            'risk_percentage': 0.35,
            'is_active': True
        },
        {
            'scenario_number': 4,
            'scenario_name': 'Look and Stay Outside P12',
            'short_description': 'Price breaks P12 High/Low and holds, using level as support/resistance',
            'detailed_description': 'Price breaks out of P12 High (or Low) cleanly and maintains the breakout, finding support/resistance at the breached P12 level. This indicates strong underlying momentum and trend continuation.',
            'hod_lod_implication': 'HOD/LOD likely already established during the overnight session. Strong trend continuation expected.',
            'directional_bias': 'bullish',  # Strong trend continuation
            'alert_criteria': 'Price holds above P12 High after breaking out (or below P12 Low). Look for the P12 level to act as dynamic support/resistance.',
            'confirmation_criteria': 'Finding consolidation/footing outside the P12 range while respecting the breached P12 level as support/resistance.',
            'entry_strategy': 'Enter on retests of the breached P12 High (as support) or P12 Low (as resistance). Use the P12 level as a dynamic entry zone.',
            'typical_targets': 'Extended daily targets, previous week/month extremes, or major psychological levels',
            'stop_loss_guidance': 'Place stops back inside the P12 range with structural confirmation',
            'risk_percentage': 0.25,
            'is_active': True
        },
        {
            'scenario_number': 5,
            'scenario_name': 'Swiping the Mid - Expect HOD/LOD in RTH',
            'short_description': 'Price disrespects P12 Mid, choppy action, both extremes likely in RTH',
            'detailed_description': 'Price shows no respect for the P12 Mid, swiping back and forth across it during the 06:00-08:30 EST window. This indicates an indecisive overnight market and suggests both HOD and LOD will be formed during the RTH session (after 09:30 EST).',
            'hod_lod_implication': 'Both HOD and LOD expected to be formed during RTH session. High probability of Range 1 day if 09:30 opens near P12 Mid.',
            'directional_bias': 'choppy',
            'alert_criteria': 'Price action is choppy and repeatedly crosses the P12 Mid without showing respect for the level. Multiple back-and-forth moves.',
            'confirmation_criteria': 'The choppy pattern itself IS the confirmation. Expect HOD/LOD formation after 09:30 EST market open.',
            'entry_strategy': 'Avoid P12-based trades. Focus on post-09:30 setups like opening range breakouts, HOD/LOD reversal trades, or hourly quarter plays.',
            'typical_targets': 'Wait for RTH price action to develop clear levels and targets',
            'stop_loss_guidance': 'Use tighter stops due to choppy conditions. Focus on clear structural levels.',
            'risk_percentage': 0.25,
            'is_active': True
        }
    ]

    for scenario_data in default_scenarios:
        existing = P12Scenario.query.filter_by(scenario_number=scenario_data['scenario_number']).first()
        if not existing:
            scenario = P12Scenario(**scenario_data)
            db.session.add(scenario)
            print(f"✅ Added Scenario {scenario_data['scenario_number']}: {scenario_data['scenario_name']}")

    try:
        db.session.commit()
        print("✅ Default scenarios saved successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving scenarios: {e}")
        raise


if __name__ == "__main__":
    upgrade_database()