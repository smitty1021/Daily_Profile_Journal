#!/usr/bin/env python3
"""
Trading Journal Data Population Script
=====================================
Populates trading models based on Random's teachings and generates ~250 realistic test trades.
Run from the root directory of your trading journal project.

Usage: python populate_trading_data.py
"""

import os
import sys
import random
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import TradingModel, Trade, EntryPoint, ExitPoint, Instrument, Tag


def create_random_trading_models(user_id):
    """Create Random's trading models based on his teachings."""

    models = [
        {
            'name': '0930 Opening Range',
            'version': '2.1',
            'is_active': True,
            'overview_logic': """The 0930 Opening Range model captures the initial momentum and direction at the New York market open. 
            Based on Random's Four Steps methodology, this model identifies "Snap" patterns (High, Low, HH/LL) in the first few minutes 
            after 9:30 AM EST. The model can trade either direction (breakout or Return to VWAP) depending on the daily classification 
            (DWP, DNP, Range 1, Range 2) determined through P12 analysis and session behavior assessment.""",

            'primary_chart_tf': '1-Minute',
            'execution_chart_tf': '1-Minute',
            'context_chart_tf': 'Daily, P12 Chart, Hourly',

            'technical_indicators_used': """- 09:30 Open Price
            - VWAP (Volume Weighted Average Price)
            - Previous Day High/Low
            - P12 High/Mid/Low levels
            - ADR (Average Daily Range) for context
            - RVOL (Relative Volume) for confirmation""",

            'instrument_applicability': 'Index Futures (ES, NQ, YM)',
            'session_applicability': '09:30-09:45 EST primary window, exits by 09:44 EST',
            'optimal_market_conditions': 'Clear daily classification (DWP/DNP), normal to high RVOL, clean break of pre-market structure',
            'sub_optimal_market_conditions': 'Range 1 days, extremely low volume, major news events during execution window',

            'entry_trigger_description': """Breakout Entry: 1-minute close above/below the identified "Snap" level (High/Low formed in first 1-3 minutes)
            RTV Entry: Return to VWAP after initial displacement, confirmed by price action
            Entry must align with daily bias from Four Steps analysis""",

            'stop_loss_strategy': 'Structural stop below/above recent swing point or 0.1% (10 basis points) maximum',
            'take_profit_strategy': """TP1: 0.1% (20 NQ handles) - Quick scalp target
            TP2: 50% of 09:30-10:00 session DRO
            Time-based exit: All positions closed by 09:44 EST""",
            'min_risk_reward_ratio': 1.5,

            'position_sizing_rules': 'Risk 2.5% baseline, up to 7-10% for A+ setups based on Four Steps confidence',
            'trade_management_breakeven_rules': 'Move stop to breakeven after TP1 hit or 1R profit achieved',
            'trade_management_partial_profit_rules': 'Take 50-75% at TP1, let remainder run to TP2 or time stop',

            'model_max_loss_per_trade': '2.5% baseline, 7-10% for A+ setups',
            'model_max_daily_loss': '5%',
            'model_max_weekly_loss': '10%',
            'model_consecutive_loss_limit': '3 trades',
        },

        {
            'name': 'HOD/LOD Reversal',
            'version': '1.8',
            'is_active': True,
            'overview_logic': """Mean reversion strategy targeting reversals at the High of Day (HOD) or Low of Day (LOD). 
            Uses Random's Four Steps to identify likely HOD/LOD zones and times, then waits for confirmation signals like 
            059 boxes, hourly momentum changes, or 1-minute rejection patterns. NOT for trend days - requires patience 
            for proper reversal confirmation.""",

            'primary_chart_tf': '1-Minute',
            'execution_chart_tf': '1-Minute',
            'context_chart_tf': 'Daily, Hourly, P12 Chart',

            'technical_indicators_used': """- Dashboard logic for HOD/LOD identification
            - % move from 18:00 open
            - Hourly quarters and 059 boxes
            - Previous session behavior (Asia/London True/False/Broken)
            - ADR and RVOL analysis""",

            'instrument_applicability': 'Index Futures (ES, NQ, YM)',
            'session_applicability': 'Active throughout RTH, best during statistical HOD/LOD times',
            'optimal_market_conditions': 'Range days, broken Asia/London sessions, clear HOD/LOD zones defined',
            'sub_optimal_market_conditions': 'Strong trend days (DWP/DNP), unclear daily structure',

            'entry_trigger_description': """Wait for price to reach defined HOD/LOD zone, then:
            - 1-minute confirmation candle (rejection pattern)
            - Hourly momentum change
            - 059 box formation
            - NOT for catching falling knives - patience required""",

            'stop_loss_strategy': '0.1% (10 basis points) above/below the HOD/LOD zone',
            'take_profit_strategy': """TP1: 50% of NY1 DRO (Daily Range Objective)
            TP2: P12 Mid level
            TP3: Previous Day Mid (PDM) or Settlement""",
            'min_risk_reward_ratio': 2.0,

            'position_sizing_rules': 'Conservative sizing due to reversal nature, 2.5% baseline risk',
            'trade_management_breakeven_rules': 'Move to breakeven after 1R profit or TP1 achievement',
            'trade_management_partial_profit_rules': 'Scale out at TP1, trail stop on remainder',

            'model_max_loss_per_trade': '2.5%',
            'model_max_daily_loss': '5%',
            'model_max_weekly_loss': '8%',
            'model_consecutive_loss_limit': '2 trades',
        },

        {
            'name': 'Captain Backtest',
            'version': '2.3',
            'is_active': True,
            'overview_logic': """Trend-following model designed to capture HOD/LOD by front-running NY2 session. 
            Requires H4 range (06:00-09:59 EST) break by 11:30, followed by pullback and continuation. 
            Higher expectancy but requires trending days (DWP/DNP). Targets 0.50% minimum with potential 
            extension to daily extremes.""",

            'primary_chart_tf': '10-Minute',
            'execution_chart_tf': '10-Minute',
            'context_chart_tf': 'Daily, P12 Chart, Hourly',

            'technical_indicators_used': """- H4 Range (06:00-09:59 EST High/Low)
            - 10-minute pullback patterns
            - Daily Range Objective (DRO) analysis
            - Hourly quarters for fine-tuning entries""",

            'instrument_applicability': 'Index Futures (ES, NQ, YM)',
            'session_applicability': 'Setup after 10:00 EST, entry by 11:30 EST, target 15:00 HOD/LOD',
            'optimal_market_conditions': 'Trending days (DWP/DNP), sufficient daily range available, clean H4 break',
            'sub_optimal_market_conditions': 'Range days, late H4 breaks after 11:30, insufficient DRO remaining',

            'entry_trigger_description': """1. H4 range must be breached by 10-minute close before 11:30 EST
            2. Wait for pullback formation on 10-minute chart
            3. Enter on 10-minute close beyond pullback extreme
            4. Use 05 boxes from hourly quarters for precision if desired""",

            'stop_loss_strategy': '0.25% (25 basis points) or structural level at previous hour 50%',
            'take_profit_strategy': """Minimum: 0.50% (50 basis points)
            Extended: Potential HOD/LOD at 15:00 if daily profile supports
            Partial scaling recommended at minimum target""",
            'min_risk_reward_ratio': 2.0,

            'position_sizing_rules': 'Standard to aggressive sizing for trending setups, 2.5-7% risk range',
            'trade_management_breakeven_rules': 'Move to breakeven after 1R (0.25%) profit',
            'trade_management_partial_profit_rules': 'Take 50% at 0.50% target, trail remainder to HOD/LOD',

            'model_max_loss_per_trade': '5%',
            'model_max_daily_loss': '7%',
            'model_max_weekly_loss': '12%',
            'model_consecutive_loss_limit': '3 trades',
        },

        {
            'name': 'P12 Scenario-Based',
            'version': '1.5',
            'is_active': True,
            'overview_logic': """Uses 12-hour Globex range (18:00-06:00 EST) High/Mid/Low as key structural levels. 
            Observes 06:00-08:30 price action relative to P12 levels to classify into 5 scenarios. 
            Provides bias for HOD/LOD location and probable price path. Trades taken at P12 levels 
            with scenario confirmation.""",

            'primary_chart_tf': '15-Minute',
            'execution_chart_tf': '5-Minute',
            'context_chart_tf': 'Daily, P12 Chart',

            'technical_indicators_used': """- P12 High/Mid/Low levels (18:00-06:00 EST range)
            - 06:00-08:30 scenario analysis window
            - Daily classification integration
            - Quarter level analysis for entries""",

            'instrument_applicability': 'Index Futures (ES, NQ, YM) - Use MQ for Nasdaq analysis',
            'session_applicability': 'Analysis 06:00-08:30, execution after 09:30 EST',
            'optimal_market_conditions': 'Clear P12 scenario development, alignment with daily bias',
            'sub_optimal_market_conditions': 'Unclear scenario, price chopping around P12 levels',

            'entry_trigger_description': """Based on scenario analysis:
            - Above Mid: Target P12 High breakout, expect low of day in
            - Below Mid: Target P12 Low breakdown, expect high of day in
            - Entry on confirmation at P12 levels with quarter precision""",

            'stop_loss_strategy': 'Below/above P12 Mid or relevant P12 level based on scenario',
            'take_profit_strategy': """Next P12 level (High/Mid/Low)
            Scenario-specific targets: 25-75 basis points
            NFP/CPI exception: 50 basis points viable""",
            'min_risk_reward_ratio': 1.5,

            'position_sizing_rules': 'Risk adjusted by scenario confidence, 2.5-10% range',
            'trade_management_breakeven_rules': 'Move to breakeven at 1:1 R:R',
            'trade_management_partial_profit_rules': 'Scale at interim levels, hold runners to final target',

            'model_max_loss_per_trade': '5%',
            'model_max_daily_loss': '8%',
            'model_max_weekly_loss': '12%',
            'model_consecutive_loss_limit': '2 trades',
        },

        {
            'name': 'Quarterly Theory & 05 Boxes',
            'version': '1.2',
            'is_active': True,
            'overview_logic': """Precision entry model using hourly quarter levels and 05 boxes for optimal 
            trade timing. Can be standalone or used to enhance other models. Focuses on statistical 
            reaction points within hourly structures. Emphasizes scaling and precise risk management.""",

            'primary_chart_tf': '1-Minute',
            'execution_chart_tf': '1-Minute',
            'context_chart_tf': 'Hourly, Daily',

            'technical_indicators_used': """- Hourly quarter levels (00, 15, 30, 45 minute marks)
            - 05 boxes (statistical reaction zones)
            - Volume analysis at quarter levels
            - Previous hour structure""",

            'instrument_applicability': 'Index Futures (ES, NQ, YM)',
            'session_applicability': 'Active throughout RTH, best at hourly turn times',
            'optimal_market_conditions': 'Clear hourly structure, normal volume, defined quarter reactions',
            'sub_optimal_market_conditions': 'High volatility news events, extremely low volume',

            'entry_trigger_description': """Entry at quarter levels on:
            - Rejection patterns at 05 boxes
            - Confirmation of hourly direction
            - Volume spike at quarter levels
            - Structure alignment with higher timeframes""",

            'stop_loss_strategy': 'Previous quarter level or 0.15% maximum',
            'take_profit_strategy': """Fixed target: 0.15%
            Scaling option: 50% at 1:1 R:R, trail remainder
            Next quarter level as extended target""",
            'min_risk_reward_ratio': 1.0,

            'position_sizing_rules': 'Conservative due to frequent entries, 1-3% risk per trade',
            'trade_management_breakeven_rules': 'Quick move to breakeven at 0.5R',
            'trade_management_partial_profit_rules': 'Heavy scaling at first target, small runner positions',

            'model_max_loss_per_trade': '3%',
            'model_max_daily_loss': '6%',
            'model_max_weekly_loss': '10%',
            'model_consecutive_loss_limit': '4 trades',
        },

        {
            'name': 'Midnight Open Retracement',
            'version': '1.0',
            'is_active': True,
            'overview_logic': """Statistical retracement model targeting moves back to Midnight Open price. 
            Active 08:00-11:15 EST window. Uses hourly footprints and distribution analysis to identify 
            optimal entry points for mean reversion to Midnight Open level.""",

            'primary_chart_tf': '3-Minute',
            'execution_chart_tf': '1-Minute',
            'context_chart_tf': 'Hourly, Daily',

            'technical_indicators_used': """- Midnight Open price (00:00 EST)
            - Hourly footprints (overlapping wicks)
            - 3-minute distribution analysis
            - Asia Range context
            - RTH Gap measurements""",

            'instrument_applicability': 'Index Futures (ES, NQ, YM)',
            'session_applicability': '08:00-11:15 EST execution window',
            'optimal_market_conditions': 'Clear overextension from Midnight Open, defined hourly footprints',
            'sub_optimal_market_conditions': 'Price near Midnight Open, unclear distribution patterns',

            'entry_trigger_description': """Entry when:
            - Price overextended from Midnight Open
            - Reaction at hourly footprint level
            - Distribution extreme reached (bullish/bearish)
            - 1-minute confirmation of reversal""",

            'stop_loss_strategy': 'Beyond footprint extreme or distribution limit',
            'take_profit_strategy': """Primary: Midnight Open price level
            Statistical: 0.12-0.13% on NASDAQ
            Secondary: Asia Range opposing side or RTH Gap fill""",
            'min_risk_reward_ratio': 1.2,

            'position_sizing_rules': 'Increase size with multiple confluences, 2-7% risk range',
            'trade_management_breakeven_rules': 'Move to breakeven halfway to target',
            'trade_management_partial_profit_rules': 'Scale heavily at Midnight Open, minimal runners',

            'model_max_loss_per_trade': '4%',
            'model_max_daily_loss': '8%',
            'model_max_weekly_loss': '12%',
            'model_consecutive_loss_limit': '3 trades',
        }
    ]

    created_models = []
    for model_data in models:
        model_data['user_id'] = user_id
        model = TradingModel(**model_data)
        db.session.add(model)
        created_models.append(model)

    db.session.commit()
    print(f"✅ Created {len(created_models)} trading models based on Random's teachings")
    return created_models


def create_realistic_trades(user_id, trading_models, num_trades=250):
    """Generate realistic test trades with proper statistics."""

    # Ensure instruments exist
    ensure_instruments_exist()

    # Get instruments
    instruments = Instrument.query.filter_by(is_active=True).all()
    if not instruments:
        print("❌ No instruments found. Please run instrument seeding first.")
        return []

    # Define realistic trade parameters based on Random's teachings
    instruments_data = {
        'ES': {'point_value': 50, 'tick_size': 0.25, 'typical_range': (10, 40)},
        'NQ': {'point_value': 20, 'tick_size': 0.25, 'typical_range': (20, 80)},
        'YM': {'point_value': 5, 'tick_size': 1.0, 'typical_range': (50, 200)},
        'RTY': {'point_value': 50, 'tick_size': 0.1, 'typical_range': (8, 30)}
    }

    # Trade outcome distributions (based on typical prop trading stats)
    win_rate = 0.65  # 65% win rate
    breakeven_rate = 0.05  # 5% breakeven

    # R-multiple distributions for winners and losers
    winner_r_multiples = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    winner_weights = [0.15, 0.20, 0.25, 0.15, 0.10, 0.08, 0.04, 0.02, 0.008, 0.002]

    loser_r_multiples = [-1.0, -0.8, -0.6, -0.4, -0.3, -0.15]
    loser_weights = [0.40, 0.25, 0.15, 0.10, 0.07, 0.03]

    # Time ranges for different models
    model_time_ranges = {
        '0930 Opening Range': [(9, 30), (9, 44)],
        'HOD/LOD Reversal': [(10, 0), (15, 30)],
        'Captain Backtest': [(10, 0), (15, 0)],
        'P12 Scenario-Based': [(9, 30), (16, 0)],
        'Quarterly Theory & 05 Boxes': [(9, 30), (16, 0)],
        'Midnight Open Retracement': [(8, 0), (11, 15)]
    }

    trades = []
    start_date = date.today() - timedelta(days=180)  # 6 months of data

    print(f"📊 Generating {num_trades} realistic trades...")

    for i in range(num_trades):
        # Random date within the last 6 months, weekdays only
        days_back = random.randint(0, 180)
        trade_date = start_date + timedelta(days=days_back)

        # Skip weekends
        while trade_date.weekday() >= 5:
            trade_date += timedelta(days=1)

        # Random instrument and model
        instrument = random.choice(instruments)
        model = random.choice(trading_models)
        instr_data = instruments_data.get(instrument.symbol, instruments_data['ES'])

        # Determine outcome
        outcome_rand = random.random()
        if outcome_rand < win_rate:
            outcome = 'win'
            r_multiple = random.choices(winner_r_multiples, winner_weights)[0]
        elif outcome_rand < win_rate + breakeven_rate:
            outcome = 'breakeven'
            r_multiple = 0
        else:
            outcome = 'loss'
            r_multiple = random.choices(loser_r_multiples, loser_weights)[0]

        # Generate direction
        direction = random.choice(['Long', 'Short'])

        # Generate entry time based on model
        time_range = model_time_ranges.get(model.name, [(9, 30), (16, 0)])
        start_hour, start_min = time_range[0]
        end_hour, end_min = time_range[1] if len(time_range) > 1 else (16, 0)

        entry_hour = random.randint(start_hour, end_hour)
        entry_minute = random.randint(0 if entry_hour > start_hour else start_min,
                                      59 if entry_hour < end_hour else end_min)

        # Generate realistic prices
        base_price = get_realistic_price(instrument.symbol, trade_date)
        tick_size = instr_data['tick_size']

        # Entry price (rounded to tick size)
        entry_price = round(base_price + random.uniform(-5, 5), 2)
        entry_price = round(entry_price / tick_size) * tick_size

        # Stop loss distance (realistic for each instrument)
        stop_distance_range = instr_data['typical_range']
        stop_distance_ticks = random.randint(stop_distance_range[0], stop_distance_range[1])
        stop_distance = stop_distance_ticks * tick_size

        # Calculate stop loss
        if direction == 'Long':
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance

        # Calculate target based on R-multiple
        risk_per_share = abs(entry_price - stop_loss)
        target_distance = abs(r_multiple) * risk_per_share

        if outcome == 'win':
            if direction == 'Long':
                exit_price = entry_price + target_distance
            else:
                exit_price = entry_price - target_distance
        elif outcome == 'breakeven':
            exit_price = entry_price
        else:  # loss
            exit_price = stop_loss + random.uniform(-0.5, 0.5) * tick_size

        # Contract size (realistic based on account size assumptions)
        if instrument.symbol == 'ES':
            contracts = random.choice([1, 2, 3, 4, 5])
        elif instrument.symbol == 'NQ':
            contracts = random.choice([1, 2, 3, 4, 5, 6, 8, 10])
        elif instrument.symbol == 'YM':
            contracts = random.choice([1, 2, 3, 4, 5])
        else:  # RTY
            contracts = random.choice([1, 2, 3])

        # Calculate P&L
        if direction == 'Long':
            price_diff = exit_price - entry_price
        else:
            price_diff = entry_price - exit_price

        gross_pnl = price_diff * contracts * instr_data['point_value']

        # Exit time (some time after entry)
        exit_minutes_later = random.randint(5, 180)  # 5 minutes to 3 hours
        exit_time = datetime.combine(trade_date, datetime.min.time().replace(
            hour=entry_hour, minute=entry_minute)) + timedelta(minutes=exit_minutes_later)

        # Ensure exit time is within market hours
        if exit_time.hour >= 16:
            exit_time = exit_time.replace(hour=15, minute=random.randint(45, 59))

        # Generate ratings (1-5 scale)
        base_rating = 4 if outcome == 'win' else random.choice([2, 3, 3, 4])
        ratings_variance = 1

        # Create trade
        trade = Trade(
            instrument_id=instrument.id,
            trade_date=trade_date,
            direction=direction,
            initial_stop_loss=stop_loss,
            terminus_target=exit_price if outcome == 'win' else entry_price + (
                2 * target_distance if direction == 'Long' else -2 * target_distance),
            is_dca=random.choice([True, False]) if random.random() < 0.15 else False,
            mae=random.uniform(0, stop_distance * 0.8) if outcome != 'loss' else stop_distance,
            mfe=target_distance if outcome == 'win' else random.uniform(0, target_distance * 0.6),
            how_closed=get_realistic_close_reason(outcome),
            news_event=get_random_news_event() if random.random() < 0.1 else None,
            rules_rating=max(1, min(5, base_rating + random.randint(-ratings_variance, ratings_variance))),
            management_rating=max(1, min(5, base_rating + random.randint(-ratings_variance, ratings_variance))),
            target_rating=max(1, min(5, base_rating + random.randint(-ratings_variance, ratings_variance))),
            entry_rating=max(1, min(5, base_rating + random.randint(-ratings_variance, ratings_variance))),
            preparation_rating=max(1, min(5, base_rating + random.randint(-ratings_variance, ratings_variance))),
            trade_notes=get_random_trade_note(model.name, outcome),
            trading_model_id=model.id,
            user_id=user_id
        )

        db.session.add(trade)
        db.session.flush()  # Get trade ID

        # Create entry point
        entry = EntryPoint(
            trade_id=trade.id,
            entry_time=datetime.min.time().replace(hour=entry_hour, minute=entry_minute),
            contracts=contracts,
            entry_price=entry_price
        )
        db.session.add(entry)

        # Create exit point
        exit_point = ExitPoint(
            trade_id=trade.id,
            exit_time=exit_time.time(),
            contracts=contracts,
            exit_price=exit_price
        )
        db.session.add(exit_point)

        trades.append(trade)

        if (i + 1) % 50 == 0:
            print(f"  📝 Generated {i + 1}/{num_trades} trades...")

    db.session.commit()
    print(f"✅ Created {len(trades)} realistic trades")
    return trades


def ensure_instruments_exist():
    """Ensure basic instruments exist."""
    instruments_data = [
        {'symbol': 'ES', 'name': 'E-mini S&P 500', 'point_value': 50.0},
        {'symbol': 'NQ', 'name': 'E-mini NASDAQ-100', 'point_value': 20.0},
        {'symbol': 'YM', 'name': 'E-mini Dow Jones', 'point_value': 5.0},
        {'symbol': 'RTY', 'name': 'E-mini Russell 2000', 'point_value': 50.0}
    ]

    for instr_data in instruments_data:
        existing = Instrument.query.filter_by(symbol=instr_data['symbol']).first()
        if not existing:
            instrument = Instrument(
                symbol=instr_data['symbol'],
                name=instr_data['name'],
                point_value=instr_data['point_value'],
                is_active=True
            )
            db.session.add(instrument)

    db.session.commit()


def get_realistic_price(symbol, trade_date):
    """Get realistic price ranges for instruments."""
    # These are approximate price ranges as of the knowledge cutoff
    price_ranges = {
        'ES': (4000, 4800),
        'NQ': (12000, 16000),
        'YM': (33000, 38000),
        'RTY': (1800, 2200)
    }

    min_price, max_price = price_ranges.get(symbol, (4000, 4800))
    return random.uniform(min_price, max_price)


def get_realistic_close_reason(outcome):
    """Get realistic close reasons."""
    if outcome == 'win':
        return random.choice(['Target Hit', 'Partial Scale', 'Time Stop', 'Trailing Stop'])
    elif outcome == 'breakeven':
        return random.choice(['Breakeven Stop', 'Time Stop', 'Scratch'])
    else:
        return random.choice(['Stop Loss', 'Manual Close', 'Risk Management'])


def get_random_news_event():
    """Get random news events."""
    events = [
        'FOMC Meeting', 'NFP Release', 'CPI Data', 'JOLTS Report',
        'GDP Data', 'Retail Sales', 'PPI Data', 'Powell Speech',
        'OPEC Meeting', 'Earnings Season', 'Geopolitical Event'
    ]
    return random.choice(events)


def get_random_trade_note(model_name, outcome):
    """Generate realistic trade notes based on Random's methodology."""

    notes_by_model = {
        '0930 Opening Range': [
            "Clean snap pattern identified at open. {}",
            "VWAP rejection provided good RTV entry. {}",
            "Strong volume confirmation at break. {}",
            "Daily classification supported directional bias. {}",
            "Time stop at 09:44 as planned. {}"
        ],
        'HOD/LOD Reversal': [
            "Perfect HOD rejection with 059 box confirmation. {}",
            "Hourly momentum change signaled reversal. {}",
            "Dashboard logic correctly identified zone. {}",
            "Patient wait for confirmation paid off. {}",
            "Mean reversion to P12 mid as expected. {}"
        ],
        'Captain Backtest': [
            "H4 range break with clean pullback setup. {}",
            "Front-ran NY2 session successfully. {}",
            "Daily profile supported trending move. {}",
            "Extended target to HOD as planned. {}",
            "Momentum carried through to 15:00. {}"
        ],
        'P12 Scenario-Based': [
            "Scenario 5B played out perfectly. {}",
            "Price above mid, targeted high breakout. {}",
            "Quarter level entry provided precision. {}",
            "P12 structure held as expected. {}",
            "Scenario analysis gave clear bias. {}"
        ],
        'Quarterly Theory & 05 Boxes': [
            "059 box provided perfect entry signal. {}",
            "Quarter level reaction as expected. {}",
            "Volume spike confirmed direction. {}",
            "Scaled out at statistical targets. {}",
            "Hourly structure respected. {}"
        ],
        'Midnight Open Retracement': [
            "Clean retracement to midnight open. {}",
            "Hourly footprint provided entry. {}",
            "Distribution extreme reached. {}",
            "Asia range context supported trade. {}",
            "Statistical target achieved. {}"
        ]
    }

    outcome_modifiers = {
        'win': "Executed according to plan.",
        'loss': "Stop loss hit, followed rules.",
        'breakeven': "Scratched for small gain/loss."
    }

    base_notes = notes_by_model.get(model_name, ["Standard setup executed. {}"])
    note_template = random.choice(base_notes)
    modifier = outcome_modifiers.get(outcome, "Trade completed.")

    return note_template.format(modifier)


def create_sample_tags(user_id):
    """Create sample tags based on Random's methodology."""

    # Import TagCategory enum
    from app.models import TagCategory

    tags_data = [
        # Setup & Strategy tags
        ('Four Steps Complete', TagCategory.SETUP_STRATEGY, 'good'),
        ('P12 Analysis Done', TagCategory.SETUP_STRATEGY, 'good'),
        ('Daily Classification Clear', TagCategory.SETUP_STRATEGY, 'good'),
        ('A+ Setup', TagCategory.SETUP_STRATEGY, 'good'),
        ('Confluence Entry', TagCategory.SETUP_STRATEGY, 'good'),
        ('Missed Setup', TagCategory.SETUP_STRATEGY, 'bad'),
        ('Poor Entry Timing', TagCategory.SETUP_STRATEGY, 'bad'),
        ('Against Daily Bias', TagCategory.SETUP_STRATEGY, 'bad'),

        # Market Conditions
        ('DWP Day', TagCategory.MARKET_CONDITIONS, 'neutral'),
        ('DNP Day', TagCategory.MARKET_CONDITIONS, 'neutral'),
        ('Range 1 Day', TagCategory.MARKET_CONDITIONS, 'neutral'),
        ('Range 2 Day', TagCategory.MARKET_CONDITIONS, 'neutral'),
        ('High RVOL', TagCategory.MARKET_CONDITIONS, 'neutral'),
        ('Low Volume', TagCategory.MARKET_CONDITIONS, 'bad'),
        ('News Event', TagCategory.MARKET_CONDITIONS, 'neutral'),
        ('Trending Market', TagCategory.MARKET_CONDITIONS, 'good'),
        ('Choppy Market', TagCategory.MARKET_CONDITIONS, 'bad'),

        # Execution & Management
        ('Perfect Execution', TagCategory.EXECUTION_MANAGEMENT, 'good'),
        ('Good Risk Management', TagCategory.EXECUTION_MANAGEMENT, 'good'),
        ('Scaled Properly', TagCategory.EXECUTION_MANAGEMENT, 'good'),
        ('Moved to BE', TagCategory.EXECUTION_MANAGEMENT, 'good'),
        ('Followed Rules', TagCategory.EXECUTION_MANAGEMENT, 'good'),
        ('Oversized Position', TagCategory.EXECUTION_MANAGEMENT, 'bad'),
        ('Poor Exit', TagCategory.EXECUTION_MANAGEMENT, 'bad'),
        ('Moved Stop Too Early', TagCategory.EXECUTION_MANAGEMENT, 'bad'),
        ('Revenge Trading', TagCategory.EXECUTION_MANAGEMENT, 'bad'),

        # Psychological & Emotional
        ('Disciplined', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'good'),
        ('Patient Entry', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'good'),
        ('Calm Execution', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'good'),
        ('FOMO Entry', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'bad'),
        ('Emotional Trade', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'bad'),
        ('Tilted', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'bad'),
        ('Overconfident', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'bad'),
        ('Fear Based Exit', TagCategory.PSYCHOLOGICAL_EMOTIONAL, 'bad')
    ]

    created_tags = []
    for name, category, color in tags_data:
        tag = Tag(
            name=name,
            category=category,
            user_id=user_id,
            is_default=False,
            is_active=True,
            color_category=color
        )
        db.session.add(tag)
        created_tags.append(tag)

    db.session.commit()
    print(f"✅ Created {len(created_tags)} sample tags")
    return created_tags


def assign_random_tags_to_trades(trades, tags):
    """Assign random tags to trades based on outcome and model."""

    print("🏷️  Assigning tags to trades...")

    # Categorize tags for easier selection
    good_tags = [tag for tag in tags if tag.color_category == 'good']
    bad_tags = [tag for tag in tags if tag.color_category == 'bad']
    neutral_tags = [tag for tag in tags if tag.color_category == 'neutral']

    for trade in trades:
        # Determine trade outcome
        if hasattr(trade, 'gross_pnl'):
            if trade.gross_pnl > 0:
                outcome = 'win'
            elif trade.gross_pnl < 0:
                outcome = 'loss'
            else:
                outcome = 'breakeven'
        else:
            # Fallback: determine from exit vs entry prices
            entry = trade.entries.first()
            exit_point = trade.exits.first()
            if entry and exit_point:
                if trade.direction == 'Long':
                    pnl = exit_point.exit_price - entry.entry_price
                else:
                    pnl = entry.entry_price - exit_point.exit_price

                if pnl > 0:
                    outcome = 'win'
                elif pnl < 0:
                    outcome = 'loss'
                else:
                    outcome = 'breakeven'
            else:
                outcome = 'win'  # Default

        # Select tags based on outcome
        selected_tags = []

        # Always add 1-2 neutral tags (market conditions, setup type)
        neutral_count = random.randint(1, 2)
        selected_tags.extend(random.sample(neutral_tags, min(neutral_count, len(neutral_tags))))

        if outcome == 'win':
            # Add 2-4 good tags
            good_count = random.randint(2, 4)
            selected_tags.extend(random.sample(good_tags, min(good_count, len(good_tags))))

            # Maybe add 1 bad tag (even good trades can have issues)
            if random.random() < 0.2:
                selected_tags.append(random.choice(bad_tags))

        elif outcome == 'loss':
            # Add 1-3 bad tags
            bad_count = random.randint(1, 3)
            selected_tags.extend(random.sample(bad_tags, min(bad_count, len(bad_tags))))

            # Maybe add 1 good tag (even bad trades can have good elements)
            if random.random() < 0.3:
                selected_tags.append(random.choice(good_tags))

        else:  # breakeven
            # Add mix of good and bad
            if random.random() < 0.5:
                selected_tags.append(random.choice(good_tags))
            if random.random() < 0.5:
                selected_tags.append(random.choice(bad_tags))

        # Remove duplicates and assign
        unique_tags = list(set(selected_tags))
        trade.tags = unique_tags

    db.session.commit()
    print(f"✅ Assigned tags to {len(trades)} trades")


def print_statistics(trades, models):
    """Print useful statistics about the generated data."""

    print("\n" + "=" * 60)
    print("📊 GENERATED DATA STATISTICS")
    print("=" * 60)

    # Model distribution
    model_counts = {}
    for trade in trades:
        model_name = trade.trading_model.name if trade.trading_model else 'Unknown'
        model_counts[model_name] = model_counts.get(model_name, 0) + 1

    print(f"\n📋 Trading Models Created: {len(models)}")
    for model in models:
        print(f"   • {model.name} v{model.version}")

    print(f"\n📈 Trade Distribution by Model:")
    for model_name, count in model_counts.items():
        percentage = (count / len(trades)) * 100
        print(f"   • {model_name}: {count} trades ({percentage:.1f}%)")

    # Instrument distribution
    instrument_counts = {}
    for trade in trades:
        symbol = trade.instrument
        instrument_counts[symbol] = instrument_counts.get(symbol, 0) + 1

    print(f"\n🎯 Trade Distribution by Instrument:")
    for symbol, count in instrument_counts.items():
        percentage = (count / len(trades)) * 100
        print(f"   • {symbol}: {count} trades ({percentage:.1f}%)")

    # Direction distribution
    long_trades = sum(1 for trade in trades if trade.direction == 'Long')
    short_trades = len(trades) - long_trades

    print(f"\n📊 Direction Distribution:")
    print(f"   • Long: {long_trades} trades ({(long_trades / len(trades) * 100):.1f}%)")
    print(f"   • Short: {short_trades} trades ({(short_trades / len(trades) * 100):.1f}%)")

    # Calculate basic P&L statistics
    total_pnl = 0
    winning_trades = 0
    losing_trades = 0
    breakeven_trades = 0

    for trade in trades:
        entries = list(trade.entries)
        exits = list(trade.exits)

        if entries and exits:
            entry = entries[0]
            exit_point = exits[0]

            if trade.direction == 'Long':
                pnl_per_contract = exit_point.exit_price - entry.entry_price
            else:
                pnl_per_contract = entry.entry_price - exit_point.exit_price

            # Get point value
            point_value = trade.instrument_obj.point_value if trade.instrument_obj else 50
            trade_pnl = pnl_per_contract * entry.contracts * point_value
            total_pnl += trade_pnl

            if trade_pnl > 0:
                winning_trades += 1
            elif trade_pnl < 0:
                losing_trades += 1
            else:
                breakeven_trades += 1

    win_rate = (winning_trades / len(trades)) * 100 if trades else 0

    print(f"\n💰 Performance Statistics:")
    print(f"   • Total P&L: ${total_pnl:,.2f}")
    print(f"   • Win Rate: {win_rate:.1f}% ({winning_trades}/{len(trades)})")
    print(f"   • Losing Trades: {losing_trades}")
    print(f"   • Breakeven Trades: {breakeven_trades}")
    print(f"   • Average P&L per Trade: ${total_pnl / len(trades):,.2f}")

    print(f"\n📅 Date Range:")
    if trades:
        min_date = min(trade.trade_date for trade in trades)
        max_date = max(trade.trade_date for trade in trades)
        print(f"   • From: {min_date.strftime('%Y-%m-%d')}")
        print(f"   • To: {max_date.strftime('%Y-%m-%d')}")

    print("\n" + "=" * 60)
    print("✅ DATA POPULATION COMPLETE")
    print("=" * 60)
    print("\nYour trading journal is now populated with:")
    print(f"• {len(models)} comprehensive trading models based on Random's teachings")
    print(f"• {len(trades)} realistic trades with proper entry/exit data")
    print(f"• Sample tags for trade categorization")
    print(f"• Realistic performance statistics for testing")
    print("\nYou can now test all journal functions and calculations!")


def main():
    """Main execution function."""

    print("🚀 TRADING JOURNAL DATA POPULATION")
    print("=" * 50)
    print("This script will populate your trading journal with:")
    print("• Trading models based on Random's teachings")
    print("• ~250 realistic test trades")
    print("• Sample tags and categorization")
    print("=" * 50)

    # Get user confirmation
    confirm = input("\nDo you want to proceed? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled.")
        return

    # Initialize Flask app
    app = create_app()

    with app.app_context():
        print("\n🔧 Initializing database connection...")

        # For this script, we'll assume user ID 1 exists
        # In production, you might want to specify the user
        user_id = 1

        print(f"👤 Using User ID: {user_id}")

        try:
            # Step 1: Create trading models
            print("\n📋 Creating trading models...")
            models = create_random_trading_models(user_id)

            # Step 2: Create sample tags
            print("\n🏷️  Creating sample tags...")
            tags = create_sample_tags(user_id)

            # Step 3: Generate realistic trades
            print("\n📊 Generating realistic trades...")
            trades = create_realistic_trades(user_id, models, 250)

            # Step 4: Assign tags to trades
            assign_random_tags_to_trades(trades, tags)

            # Step 5: Print statistics
            print_statistics(trades, models)

        except Exception as e:
            print(f"\n❌ Error during population: {e}")
            db.session.rollback()
            raise

        print(f"\n🎉 Successfully populated trading journal!")
        print(f"📁 Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Unknown')}")


if __name__ == "__main__":
    main()