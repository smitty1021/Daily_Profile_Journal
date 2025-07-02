from app import create_app, db
from app.models import P12Scenario, DailyJournal

app = create_app()

with app.app_context():
    print("🔧 Fixing P12 scenario usage tracking...")

    # Get all scenarios
    scenarios = P12Scenario.query.all()

    for scenario in scenarios:
        # Count how many journals use this scenario
        usage_count = DailyJournal.query.filter_by(p12_scenario_id=scenario.id).count()

        # Update the times_selected counter
        scenario.times_selected = usage_count

        print(f"✅ Scenario {scenario.scenario_number}: {usage_count} uses")

    # Commit the changes
    db.session.commit()

    print(f"\n🎉 Usage tracking fixed! All P12 scenario usage counts updated.")

    # Verify the fix
    print(f"\n📊 Updated usage counts:")
    for scenario in P12Scenario.query.all():
        print(f"   • Scenario {scenario.scenario_number}: {scenario.times_selected} uses")