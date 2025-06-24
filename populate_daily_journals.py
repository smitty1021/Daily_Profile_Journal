#!/usr/bin/env python3
"""
Daily Journal Population Script
==============================
Creates realistic daily journal entries for each day that has trades,
following Random's Four Steps methodology and daily analysis framework.

Usage: python populate_daily_journals.py
"""

import os
import sys
import random
from datetime import datetime, date, time, timedelta
from collections import defaultdict

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import DailyJournal, Trade


def get_trade_days_with_data(user_id):
    """Get all days that have trades and aggregate trade data for each day."""

    trades = Trade.query.filter_by(user_id=user_id).order_by(Trade.trade_date).all()

    # Group trades by date
    trade_days = defaultdict(list)
    for trade in trades:
        trade_days[trade.trade_date].append(trade)

    print(f"📅 Found {len(trade_days)} unique trading days with {len(trades)} total trades")
    return trade_days


def calculate_daily_performance(trades_for_day):
    """Calculate performance metrics for a specific day."""

    total_pnl = 0
    winning_trades = 0
    losing_trades = 0
    total_volume = 0

    for trade in trades_for_day:
        # Calculate P&L
        entries = list(trade.entries)
        exits = list(trade.exits)

        if entries and exits:
            entry = entries[0]
            exit_point = exits[0]

            if trade.direction == 'Long':
                pnl_per_contract = exit_point.exit_price - entry.entry_price
            else:
                pnl_per_contract = entry.entry_price - exit_point.exit_price

            point_value = trade.instrument_obj.point_value if trade.instrument_obj else 50
            trade_pnl = pnl_per_contract * entry.contracts * point_value
            total_pnl += trade_pnl
            total_volume += entry.contracts

            if trade_pnl > 0:
                winning_trades += 1
            elif trade_pnl < 0:
                losing_trades += 1

    return {
        'total_pnl': total_pnl,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'total_trades': len(trades_for_day),
        'total_volume': total_volume,
        'win_rate': (winning_trades / len(trades_for_day)) * 100 if trades_for_day else 0
    }


def get_daily_classification():
    """Get a random daily classification based on Random's methodology."""
    classifications = [
        ('DWP', 'Down With Purpose - Trending down day'),
        ('DNP', 'Down With No Purpose - Trending up day'),  # Note: DNP actually means up in Random's system
        ('Range 1', 'Range day - price returns to 9:30 mean'),
        ('Range 2', 'Range day - extended range but contained')
    ]
    return random.choice(classifications)


def get_session_behavior():
    """Get random session behavior based on Random's analysis."""
    behaviors = [
        ('Asia True', 'Asia session respected structure'),
        ('Asia False', 'Asia session broke structure'),
        ('London True', 'London session respected structure'),
        ('London False', 'London session broke structure'),
        ('Asia/London Broken', 'Both sessions broke key levels')
    ]
    return random.choice(behaviors)


def generate_four_steps_analysis(daily_classification, session_behavior, trades_for_day):
    """Generate Four Steps analysis based on Random's methodology."""

    classification, class_desc = daily_classification
    session, session_desc = session_behavior

    # Step 1: Define HOD/LOD
    step1_templates = [
        "Dashboard analysis shows {0} bias. {1} - expecting HOD around 15:00, LOD likely already in from overnight session.",
        "% move from 18:00 open suggests {0} structure. {1} Daily range potential assessed at 1.2-1.8% based on ADR10.",
        "P12 analysis indicates {0} formation. {1} Time zone analysis shows clear directional bias for RTH session.",
        "Globex range and overnight action point to {0} day. {1} HOD/LOD zones identified using dashboard logic."
    ]

    step1 = random.choice(step1_templates).format(classification, session_desc)

    # Step 2: Incorporate Variables
    rvol = random.randint(80, 180)
    adr_remaining = random.randint(60, 120)

    step2_templates = [
        "Session behavior: {0}. RVOL running {1}% of normal. ADR suggests {2}% available range remaining for RTH.",
        "Variables aligned: {0} with {1}% RVOL confirmation. Model activation criteria met for trending setups.",
        "{0} session behavior supports bias. Volatility and volume parameters within normal ranges for execution.",
        "Key variables: {0} and elevated RVOL at {1}%. Market structure supportive of chosen trading models."
    ]

    step2 = random.choice(step2_templates).format(session_desc, rvol, adr_remaining)

    # Step 3: Set Realistic Expectance
    range_target = random.uniform(0.8, 2.2)
    completion = random.randint(40, 85)
    extension_phase = random.choice(['early extension phase', 'mid-day consolidation', 'late extension potential'])

    step3_templates = [
        "Expectance set for {0} day with {1:.1f}% range target. Early/late extension assessment: {2}.",
        "Daily range median comparison shows {1}% completion. Adjusting position sizes and targets accordingly.",
        "Historical {0} days show {1}% median performance. Setting conservative targets given current range utilization.",
        "Range analysis: {1:.1f}% of ADR10 used. Expectance calibrated for {0} day structure."
    ]

    step3 = random.choice(step3_templates).format(classification, range_target, extension_phase)

    # Step 4: Engage at Highest Statistical Structure
    models_used = list(set([trade.trading_model.name for trade in trades_for_day if trade.trading_model]))
    models_str = ', '.join(models_used) if models_used else 'Standard setups'

    step4_templates = [
        "Engaged using {0} model(s). Price clouds and statistical levels provided optimal entry structure.",
        "Highest probability setups identified: {0}. Front-run and confirmation entries executed per plan.",
        "Statistical structure engagement: {0} models activated. Entry quality rated high based on confluence.",
        "Execution at key levels using {0}. Risk/reward alignment with daily bias maintained throughout."
    ]

    step4 = random.choice(step4_templates).format(models_str)

    return "Step 1 - Define HOD/LOD: {0}\n\nStep 2 - Incorporate Variables: {1}\n\nStep 3 - Set Realistic Expectance: {2}\n\nStep 4 - Engage at Highest Statistical Structure: {3}".format(
        step1, step2, step3, step4)


def generate_premarket_analysis(daily_classification, session_behavior):
    """Generate pre-market analysis following Random's methodology."""

    classification, _ = daily_classification
    session, _ = session_behavior

    templates = [
        "Globex review: {0} session behavior with clear {1} bias developing. P12 levels defined: High {2}, Mid {3}, Low {4}. Key reaction levels identified for RTH session.",

        "Overnight structure analysis shows {0} formation. {1} Range: {2:.1f}% from 18:00 open. Dashboard logic suggests {3} bias for NY session with HOD/LOD timing estimates.",

        "Pre-market assessment: {0} day classification based on session behavior and P12 analysis. Key levels: Previous day high/low, settlement, and overnight range boundaries. Expect {1} behavior.",

        "European session showed {0} characteristics. Asia range: {1} handles. P12 scenario analysis points to {2} setup with statistical edge for RTH execution.",

        "Overnight range analysis: {0:.1f}% move from midnight open. {1} session confirms daily bias. Risk assessment: normal to elevated based on upcoming economic data."
    ]

    p12_high = random.randint(4200, 4600) if classification in ['DNP', 'Range 2'] else random.randint(4150, 4400)
    p12_mid = p12_high - random.randint(15, 35)
    p12_low = p12_mid - random.randint(15, 35)

    overnight_move = random.uniform(0.3, 1.8)
    asia_range = random.randint(25, 85)

    template = random.choice(templates)

    # Handle different template formats using positional formatting
    if 'P12 levels defined' in template:
        return template.format(session, classification, p12_high, p12_mid, p12_low)
    elif 'Range:' in template and 'Dashboard logic' in template:
        return template.format(classification, session, overnight_move, classification)
    elif 'Asia range:' in template:
        return template.format(session, asia_range, classification)
    elif 'move from midnight' in template:
        return template.format(overnight_move, session)
    else:
        return template.format(classification, session, classification)


def generate_trade_plan(daily_classification, trades_for_day):
    """Generate trade plan based on daily classification and actual trades."""

    classification, _ = daily_classification
    models_used = list(set([trade.trading_model.name for trade in trades_for_day if trade.trading_model]))

    plan_templates = {
        'DWP': [
            "Plan: Target short entries on {} models. Expecting breakdown and continuation lower. Risk management: tight stops above key levels, targets at daily lows.",
            "Strategy: Activate trend-following models ({}) for downside capture. Avoid counter-trend trades. Position sizing: moderate to aggressive on A+ setups.",
            "Execution plan: Wait for proper displacement lower, then front-run continuation. Models in play: {}. Target daily extremes with scaled exits."
        ],
        'DNP': [
            "Plan: Focus on long entries via {} models. Trending upside expected with momentum continuation. Risk: structured stops below key supports.",
            "Strategy: Deploy trend models ({}) for upside participation. Avoid fading strength. Sizing: standard to large on confirmed breakouts.",
            "Execution: Target breakout continuation using {}. Plan for extended targets if momentum sustains. Partial scaling at statistical levels."
        ],
        'Range 1': [
            "Plan: Scalping focused using {} models. Expect return to 9:30 mean. Quick in/out trades with tight risk management parameters.",
            "Strategy: Range-bound approach with {} setups. Target reversals at extremes, quick profit-taking. Conservative sizing due to chop risk.",
            "Execution: Deploy mean reversion models ({}). Fast exits priority over large targets. Risk management: smaller stops, frequent reassessment."
        ],
        'Range 2': [
            "Plan: Extended range day approach using {} models. Larger range than R1 but still contained. Target range extremes with patience.",
            "Strategy: Combination approach - trend models ({}) at breaks, reversal models at extremes. Medium-term holds acceptable.",
            "Execution: Flexible model deployment ({}). Adjust targets based on range development. Standard risk parameters with range-based adjustments."
        ]
    }

    templates = plan_templates.get(classification, plan_templates['Range 1'])
    models_str = ', '.join(models_used) if models_used else 'standard setups'

    return random.choice(templates).format(models_str)


def generate_execution_notes(trades_for_day, performance):
    """Generate execution notes based on actual trades and performance."""

    models_executed = [trade.trading_model.name for trade in trades_for_day if trade.trading_model]
    directions = [trade.direction for trade in trades_for_day]

    # Count longs vs shorts
    long_count = directions.count('Long')
    short_count = directions.count('Short')

    base_notes = []

    # Trade execution summary
    if performance['total_trades'] == 1:
        base_notes.append(
            "Single trade execution: {0}. ".format(models_executed[0] if models_executed else 'Standard setup'))
    else:
        base_notes.append(
            "Executed {0} trades: {1} longs, {2} shorts. ".format(performance['total_trades'], long_count, short_count))

    # Model usage
    if models_executed:
        unique_models = list(set(models_executed))
        if len(unique_models) == 1:
            base_notes.append("Focused on {0} model throughout session. ".format(unique_models[0]))
        else:
            base_notes.append("Multiple models deployed: {0}. ".format(', '.join(unique_models)))

    # Performance assessment
    if performance['win_rate'] >= 70:
        base_notes.append("Execution quality: excellent. Rules followed consistently. ")
    elif performance['win_rate'] >= 50:
        base_notes.append("Execution quality: good. Minor timing improvements identified. ")
    else:
        base_notes.append("Execution quality: needs improvement. Rule adherence review required. ")

    # P&L context
    if performance['total_pnl'] > 500:
        base_notes.append(
            "Strong P&L day: ${0:.0f}. Target achievement exceeded expectations. ".format(performance['total_pnl']))
    elif performance['total_pnl'] > 0:
        base_notes.append("Positive P&L: ${0:.0f}. Consistent with daily goals. ".format(performance['total_pnl']))
    elif performance['total_pnl'] > -200:
        base_notes.append(
            "Small loss: ${0:.0f}. Within acceptable daily risk parameters. ".format(performance['total_pnl']))
    else:
        base_notes.append(
            "Significant loss: ${0:.0f}. Risk management review required. ".format(performance['total_pnl']))

    # Add specific execution details
    execution_details = [
        "Entry timing aligned with planned levels. Stop placement followed model requirements.",
        "Risk management executed per plan. Position sizing appropriate for setup quality.",
        "Trade management smooth - moved stops to breakeven as planned.",
        "Scaling executed at statistical targets. Runner management according to model rules.",
        "Exit timing optimal given market conditions. No premature stops or late exits."
    ]

    base_notes.append(random.choice(execution_details))

    return ' '.join(base_notes)


def generate_eod_review(performance, daily_classification):
    """Generate end-of-day review following Random's framework."""

    classification, _ = daily_classification

    review_sections = []

    # Performance summary
    if performance['total_pnl'] > 0:
        review_sections.append(
            "Day result: +${0:.0f} ({1:.0f}% win rate). Daily classification ({2}) played out as expected.".format(
                performance['total_pnl'], performance['win_rate'], classification))
    else:
        review_sections.append(
            "Day result: ${0:.0f} ({1:.0f}% win rate). Daily classification ({2}) assessment needs refinement.".format(
                performance['total_pnl'], performance['win_rate'], classification))

    # What worked well
    worked_well = [
        "Four Steps analysis provided clear daily bias and execution framework.",
        "Model selection aligned perfectly with market conditions and daily classification.",
        "Risk management parameters kept losses controlled and let winners run appropriately.",
        "Entry timing and patience at statistical levels resulted in high-quality setups.",
        "P12 analysis and scenario mapping gave excellent structural guidance."
    ]

    if performance['win_rate'] >= 60:
        review_sections.append("What worked: " + random.choice(worked_well))

    # Areas for improvement
    improvements = [
        "Could improve entry precision using quarter level analysis for better risk/reward.",
        "Position sizing could be optimized - missed opportunity for larger size on A+ setups.",
        "Trade management could be enhanced - earlier breakeven moves on strong setups.",
        "Daily classification assessment needs refinement - mixed signals caused hesitation.",
        "Model activation criteria should be stricter - avoided some marginal setups."
    ]

    review_sections.append("Improvement areas: " + random.choice(improvements))

    # Lessons learned
    lessons = [
        "Patience at key levels continues to be rewarded with high-quality entries.",
        "Daily bias from Four Steps framework remains essential for trade direction confidence.",
        "Risk management discipline prevents small losses from becoming large ones.",
        "Model-specific execution rules provide consistency and remove emotional decisions.",
        "Market structure recognition improving - better at identifying trending vs ranging conditions."
    ]

    review_sections.append("Key lesson: " + random.choice(lessons))

    # Tomorrow's preparation
    tomorrow_prep = [
        "Review overnight action and update P12 levels for tomorrow's analysis.",
        "Check economic calendar for potential market-moving events during RTH.",
        "Assess daily range utilization and adjust position sizing parameters if needed.",
        "Review model performance and consider any activation criteria adjustments.",
        "Prepare dashboard analysis and update HOD/LOD probability assessments."
    ]

    review_sections.append("Tomorrow's prep: " + random.choice(tomorrow_prep))

    return ' '.join(review_sections)


def generate_psych_ratings(performance):
    """Generate psychology ratings based on performance."""

    # Base ratings influenced by performance
    base_rating = 4 if performance['total_pnl'] > 0 else 3
    if performance['win_rate'] >= 75:
        base_rating = 5
    elif performance['total_pnl'] < -300:
        base_rating = 2

    # Add some variance
    variance = 1

    ratings = {}
    psych_factors = [
        'discipline', 'motivation', 'focus', 'mastery',
        'composure', 'resilience', 'mind', 'energy'
    ]

    for factor in psych_factors:
        # Some factors might be different based on specific performance aspects
        if factor == 'discipline':
            # Higher discipline rating if followed rules (good win rate or small losses)
            rating = base_rating + (1 if performance['win_rate'] >= 60 or abs(performance['total_pnl']) < 200 else -1)
        elif factor == 'composure':
            # Higher composure if managed losses well
            rating = base_rating + (1 if performance['total_pnl'] > -200 else -1)
        elif factor == 'energy':
            # Random variance for energy
            rating = base_rating + random.randint(-1, 1)
        else:
            rating = base_rating + random.randint(-variance, variance)

        # Ensure ratings stay within 1-5 range
        ratings[factor] = max(1, min(5, rating))

    return ratings


def create_daily_journal_entry(trade_date, trades_for_day, user_id):
    """Create a comprehensive daily journal entry."""

    # Check if journal already exists
    existing = DailyJournal.query.filter_by(
        user_id=user_id,
        journal_date=trade_date
    ).first()

    if existing:
        return existing

    # Calculate performance metrics
    performance = calculate_daily_performance(trades_for_day)

    # Generate daily classification and session behavior
    daily_classification = get_daily_classification()
    session_behavior = get_session_behavior()

    # Generate psychology ratings
    psych_ratings = generate_psych_ratings(performance)

    # Count unique models used
    unique_models = len(set([t.trading_model.name for t in trades_for_day if t.trading_model]))

    # Create journal entry using the correct field names from the actual model
    journal = DailyJournal(
        user_id=user_id,
        journal_date=trade_date,

        # Pre-market section (using actual field names from your model)
        p12_expected_outcomes=generate_four_steps_analysis(daily_classification, session_behavior, trades_for_day),
        realistic_expectance_notes=generate_premarket_analysis(daily_classification, session_behavior),
        engagement_structure_notes=generate_trade_plan(daily_classification, trades_for_day),
        key_levels_notes=generate_execution_notes(trades_for_day, performance),

        # Mental state ratings
        mental_feeling_rating=psych_ratings.get('energy', 3),
        mental_mind_rating=psych_ratings.get('mind', 3),
        mental_energy_rating=psych_ratings.get('energy', 3),
        mental_motivation_rating=psych_ratings.get('motivation', 3),

        # Post-market analysis
        market_observations=generate_eod_review(performance, daily_classification),
        self_observations="Executed trades according to plan. " + ("Performance exceeded expectations." if performance[
                                                                                                               'total_pnl'] > 0 else "Room for improvement in execution."),

        # Daily reflection
        did_well_today="Applied Four Steps methodology consistently. " + (
            "Good risk management and trade execution." if performance[
                                                               'win_rate'] >= 60 else "Maintained discipline despite challenging conditions."),
        did_not_go_well_today="Minor timing issues on entries." if performance[
                                                                       'win_rate'] < 60 else "No major execution issues identified.",
        learned_today=random.choice([
            "Patience at key levels continues to pay off.",
            "Model selection alignment with daily bias is crucial.",
            "Risk management discipline prevents larger losses.",
            "P12 analysis provides excellent structural guidance."
        ]),
        improve_action_next_day=random.choice([
            "Focus on tighter entry timing using quarter levels.",
            "Review daily classification criteria for better accuracy.",
            "Implement stricter model activation requirements.",
            "Enhance position sizing based on setup quality."
        ]),

        # Psychology ratings (1-5 scale) - using actual field names
        review_psych_discipline_rating=psych_ratings['discipline'],
        review_psych_motivation_rating=psych_ratings['motivation'],
        review_psych_focus_rating=psych_ratings['focus'],
        review_psych_mastery_rating=psych_ratings['mastery'],
        review_psych_composure_rating=psych_ratings['composure'],
        review_psych_resilience_rating=psych_ratings['resilience'],
        review_psych_mind_rating=psych_ratings['mind'],
        review_psych_energy_rating=psych_ratings['energy'],

        # Key events
        key_events_today="Traded {0} times using {1} models. Daily classification: {2}. Session behavior: {3}.".format(
            performance['total_trades'], unique_models, daily_classification[0], session_behavior[0])
    )

    return journal


def populate_daily_journals(user_id):
    """Main function to populate daily journal entries."""

    print("📖 DAILY JOURNAL POPULATION")
    print("=" * 50)

    # Get all trade days
    trade_days = get_trade_days_with_data(user_id)

    if not trade_days:
        print("❌ No trades found for user. Please run trade population first.")
        return []

    created_journals = []

    print(f"\n📝 Creating daily journal entries for {len(trade_days)} trading days...")

    for trade_date, trades_for_day in trade_days.items():
        try:
            journal = create_daily_journal_entry(trade_date, trades_for_day, user_id)

            if journal.id is None:  # New journal
                db.session.add(journal)
                db.session.flush()
                created_journals.append(journal)

            print(f"   ✅ {trade_date.strftime('%Y-%m-%d')}: {len(trades_for_day)} trades")

        except Exception as e:
            print(f"   ❌ {trade_date.strftime('%Y-%m-%d')}: Error - {e}")
            continue

    # Commit all journals
    db.session.commit()

    print(f"\n📊 SUMMARY:")
    print(f"   • Created: {len(created_journals)} new daily journal entries")
    print(f"   • Skipped: {len(trade_days) - len(created_journals)} existing entries")
    print(f"   • Total: {len(trade_days)} trading days covered")

    # Print sample statistics
    if created_journals:
        print(f"\n📈 SAMPLE JOURNAL STATISTICS:")

        # Average psychology ratings
        all_ratings = {
            'discipline': [],
            'motivation': [],
            'focus': [],
            'mastery': [],
            'composure': [],
            'resilience': [],
            'mind': [],
            'energy': []
        }

        for journal in created_journals:
            all_ratings['discipline'].append(journal.review_psych_discipline_rating or 0)
            all_ratings['motivation'].append(journal.review_psych_motivation_rating or 0)
            all_ratings['focus'].append(journal.review_psych_focus_rating or 0)
            all_ratings['mastery'].append(journal.review_psych_mastery_rating or 0)
            all_ratings['composure'].append(journal.review_psych_composure_rating or 0)
            all_ratings['resilience'].append(journal.review_psych_resilience_rating or 0)
            all_ratings['mind'].append(journal.review_psych_mind_rating or 0)
            all_ratings['energy'].append(journal.review_psych_energy_rating or 0)

        print("   Average Psychology Ratings:")
        for factor, ratings in all_ratings.items():
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                print(f"     • {factor.title()}: {avg_rating:.1f}/5.0")

    return created_journals


def main():
    """Main execution function."""

    print("📖 DAILY JOURNAL POPULATION SCRIPT")
    print("=" * 50)
    print("This script will create daily journal entries for each day with trades.")
    print("Each entry includes:")
    print("• Four Steps analysis following Random's methodology")
    print("• Pre-market analysis and trade planning")
    print("• Execution notes based on actual trades")
    print("• End-of-day review and lessons learned")
    print("• Psychology ratings (1-5 scale)")
    print("=" * 50)

    # Get user confirmation
    confirm = input("\nDo you want to proceed? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled.")
        return

    # Initialize Flask app
    app = create_app()

    with app.app_context():
        print("\n🔧 Connecting to database...")

        # For this script, we'll assume user ID 1 exists
        user_id = 1
        print(f"👤 Using User ID: {user_id}")

        try:
            journals = populate_daily_journals(user_id)

            print(f"\n🎉 Daily journal population complete!")
            print(f"✅ Created {len(journals)} comprehensive daily journal entries")
            print(f"📚 Each entry follows Random's Four Steps methodology")
            print(f"🧠 Psychology tracking integrated with trade performance")

        except Exception as e:
            print(f"\n❌ Error during journal population: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()