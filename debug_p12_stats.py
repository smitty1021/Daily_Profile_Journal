from app import create_app, db
from app.models import P12Scenario, DailyJournal
from datetime import datetime, timedelta
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("🔍 Debugging P12 statistics calculations...")

    # Test 6 months lookback
    six_months_ago = datetime.now() - timedelta(days=180)
    recent_journals_6m = DailyJournal.query.filter(
        DailyJournal.journal_date >= six_months_ago.date(),
        DailyJournal.p12_scenario_id.isnot(None)
    ).count()
    print(f"📊 P12 journals (last 6 months): {recent_journals_6m}")

    # Test 30 days lookback
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_journals_30d = DailyJournal.query.filter(
        DailyJournal.journal_date >= thirty_days_ago.date(),
        DailyJournal.p12_scenario_id.isnot(None)
    ).count()
    print(f"📊 P12 journals (last 30 days): {recent_journals_30d}")

    # Test scenario distribution for 30 days
    scenario_distribution = db.session.query(
        P12Scenario.scenario_number,
        func.count(DailyJournal.id).label('count')
    ).join(
        DailyJournal, P12Scenario.id == DailyJournal.p12_scenario_id
    ).filter(
        DailyJournal.journal_date >= thirty_days_ago.date()
    ).group_by(P12Scenario.scenario_number).all()

    print(f"📊 Scenario distribution (last 30 days):")
    for scenario, count in scenario_distribution:
        print(f"   • Scenario {scenario}: {count}")

    # Check what date range actually has data
    oldest_p12_journal = DailyJournal.query.filter(
        DailyJournal.p12_scenario_id.isnot(None)
    ).order_by(DailyJournal.journal_date).first()

    newest_p12_journal = DailyJournal.query.filter(
        DailyJournal.p12_scenario_id.isnot(None)
    ).order_by(DailyJournal.journal_date.desc()).first()

    if oldest_p12_journal and newest_p12_journal:
        print(f"📅 P12 data date range:")
        print(f"   • Oldest: {oldest_p12_journal.journal_date}")
        print(f"   • Newest: {newest_p12_journal.journal_date}")