from app import create_app, db
from app.models import P12Scenario, DailyJournal
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("🔍 Checking P12 data...")

    # Check P12 scenarios
    scenarios = P12Scenario.query.all()
    print(f"\n📊 P12 Scenarios in database: {len(scenarios)}")
    for scenario in scenarios:
        print(f"   • {scenario.scenario_number}: {scenario.scenario_name}")
        print(f"     Times selected: {scenario.times_selected}")

    # Check daily journals with P12 data
    journals_with_p12 = DailyJournal.query.filter(DailyJournal.p12_scenario_id.isnot(None)).all()
    print(f"\n📖 Daily journals with P12 scenarios: {len(journals_with_p12)}")

    total_journals = DailyJournal.query.count()
    print(f"📖 Total daily journals: {total_journals}")

    # Check recent journals
    recent_date = datetime.now() - timedelta(days=30)
    recent_journals = DailyJournal.query.filter(DailyJournal.journal_date >= recent_date.date()).all()
    print(f"📖 Recent journals (last 30 days): {len(recent_journals)}")

    # Sample some data
    if journals_with_p12:
        print(f"\n📋 Sample P12 journal entries:")
        for journal in journals_with_p12[:3]:
            scenario = P12Scenario.query.get(journal.p12_scenario_id) if journal.p12_scenario_id else None
            scenario_name = scenario.scenario_number if scenario else "None"
            print(f"   • {journal.journal_date}: Scenario {scenario_name}")

    # Check if usage tracking is working
    print(f"\n🔢 P12 scenario usage counts:")
    for scenario in scenarios:
        print(f"   • Scenario {scenario.scenario_number}: {scenario.times_selected} uses")