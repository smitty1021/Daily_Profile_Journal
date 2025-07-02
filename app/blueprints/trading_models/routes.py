from flask import render_template, request, flash, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func, desc, asc, and_, or_
from datetime import datetime, timedelta
import json
from decimal import Decimal
import statistics

from app.blueprints.trading_models import bp
from app.models import TradingModel, Trade, EntryPoint, ExitPoint, db
from app.utils.calculations import calculate_trade_pnl, calculate_risk_reward_ratio


@bp.route('/view/<int:model_id>')
@login_required
def view_model_detail(model_id):
    """
    Detailed analytics page for a specific trading model.
    Shows comprehensive performance metrics, risk analysis, and trading statistics
    based on Random's (Matt Mickey) methodology.
    """
    # Get the trading model
    model = TradingModel.query.filter_by(
        id=model_id,
        user_id=current_user.id if not current_user.has_role('admin') else None
    ).first_or_404()

    # Get all trades for this model
    trades_query = Trade.query.filter_by(
        trading_model_id=model_id,
        user_id=current_user.id
    ).order_by(Trade.entry_timestamp.desc())

    trades = trades_query.all()

    # If no trades, show empty state
    if not trades:
        return render_template('trading_models/model_detail.html',
                               model=model,
                               trades=[],
                               analytics={},
                               has_trades=False)

    # Calculate comprehensive analytics
    analytics = calculate_model_analytics(trades)

    # Get recent trades for display
    recent_trades = trades[:10]

    # Prepare equity curve data
    equity_data = prepare_equity_curve_data(trades)

    # Get model-specific insights based on Random's methodology
    model_insights = generate_model_insights(model, analytics)

    return render_template('trading_models/model_detail.html',
                           model=model,
                           trades=recent_trades,
                           total_trades=len(trades),
                           analytics=analytics,
                           equity_data=json.dumps(equity_data),
                           model_insights=model_insights,
                           has_trades=True)


def calculate_model_analytics(trades):
    """
    Calculate comprehensive trading model analytics based on Random's methodology.

    Returns dictionary with all performance, risk, and consistency metrics.
    """
    if not trades:
        return {}

    # Basic trade data preparation
    trade_pnls = []
    winning_trades = []
    losing_trades = []
    trade_durations = []
    daily_pnls = {}
    weekly_pnls = {}
    monthly_pnls = {}

    for trade in trades:
        # Calculate P&L for each trade
        pnl = pnl = trade.pnl if trade.pnl is not None else 0
        trade_pnls.append(float(pnl))

        # Categorize trades
        if pnl > 0:
            winning_trades.append(float(pnl))
        elif pnl < 0:
            losing_trades.append(float(pnl))

        # Calculate duration
        if trade.exit_timestamp and trade.entry_timestamp:
            duration = (trade.exit_timestamp - trade.entry_timestamp).total_seconds() / 60
            trade_durations.append(duration)

        # Group by time periods for consistency analysis
        trade_date = trade.entry_timestamp.date() if trade.entry_timestamp else None
        if trade_date:
            daily_pnls[trade_date] = daily_pnls.get(trade_date, 0) + float(pnl)

            week_key = trade_date.strftime('%Y-W%U')
            weekly_pnls[week_key] = weekly_pnls.get(week_key, 0) + float(pnl)

            month_key = trade_date.strftime('%Y-%m')
            monthly_pnls[month_key] = monthly_pnls.get(month_key, 0) + float(pnl)

    # =============================================================================
    # PERFORMANCE METRICS (Based on Random's teachings)
    # =============================================================================

    total_pnl = sum(trade_pnls)
    total_trades = len(trades)
    winning_count = len(winning_trades)
    losing_count = len(losing_trades)

    # Strike Rate (Win Rate)
    strike_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0

    # Average wins/losses
    avg_win = statistics.mean(winning_trades) if winning_trades else 0
    avg_loss = statistics.mean(losing_trades) if losing_trades else 0

    # Profit Factor
    total_wins = sum(winning_trades) if winning_trades else 0
    total_losses = abs(sum(losing_trades)) if losing_trades else 0
    profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf') if total_wins > 0 else 0

    # Expected Value per trade
    expected_value = statistics.mean(trade_pnls) if trade_pnls else 0

    # Median Profit/Loss
    median_profit = statistics.median(trade_pnls) if trade_pnls else 0

    # Trade Frequency (trades per day)
    if trades:
        first_trade_date = min(t.entry_timestamp for t in trades if t.entry_timestamp).date()
        last_trade_date = max(t.entry_timestamp for t in trades if t.entry_timestamp).date()
        trading_days = (last_trade_date - first_trade_date).days + 1
        trade_frequency = total_trades / trading_days if trading_days > 0 else 0
    else:
        trade_frequency = 0

    # Daily Expected Value
    daily_ev = expected_value * trade_frequency

    # =============================================================================
    # RISK METRICS (Critical for Random's system)
    # =============================================================================

    # Maximum Favorable Excursion of Equity (running P&L high)
    running_pnl = 0
    equity_curve = []
    peak_equity = 0
    for pnl in trade_pnls:
        running_pnl += pnl
        equity_curve.append(running_pnl)
        peak_equity = max(peak_equity, running_pnl)

    mfe_equity = peak_equity

    # Maximum Drawdown
    max_drawdown = 0
    peak = 0
    drawdown_durations = []
    current_drawdown_start = None

    for i, equity in enumerate(equity_curve):
        if equity > peak:
            peak = equity
            if current_drawdown_start is not None:
                # End of drawdown period
                drawdown_durations.append(i - current_drawdown_start)
                current_drawdown_start = None
        else:
            drawdown = peak - equity
            max_drawdown = max(max_drawdown, drawdown)
            if current_drawdown_start is None and drawdown > 0:
                current_drawdown_start = i

    # Handle ongoing drawdown
    if current_drawdown_start is not None:
        drawdown_durations.append(len(equity_curve) - current_drawdown_start)

    # Drawdown statistics
    avg_drawdown = statistics.mean([peak - eq for eq in equity_curve if peak - eq > 0]) if equity_curve else 0
    median_drawdown = statistics.median([peak - eq for eq in equity_curve if peak - eq > 0]) if equity_curve else 0
    longest_drawdown_duration = max(drawdown_durations) if drawdown_durations else 0
    median_drawdown_duration = statistics.median(drawdown_durations) if drawdown_durations else 0

    # Kelly Criterion (Optimal Risk %)
    if avg_loss != 0 and profit_factor > 1:
        kelly_fraction = (strike_rate / 100 * abs(avg_win / avg_loss) - (1 - strike_rate / 100)) / abs(
            avg_win / avg_loss)
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25% for safety
    else:
        kelly_fraction = 0

    # =============================================================================
    # TRADING STATISTICS (Random's Focus Areas)
    # =============================================================================

    # Profitable vs Losing moves
    profitable_moves = winning_count
    losing_moves = losing_count

    # Loss rate
    loss_rate = (losing_count / total_trades * 100) if total_trades > 0 else 0

    # Days analysis
    daily_pnl_values = list(daily_pnls.values())
    positive_days = len([d for d in daily_pnl_values if d > 0])
    total_days = len(daily_pnl_values)
    pct_days_positive = (positive_days / total_days * 100) if total_days > 0 else 0

    # Average trade duration
    avg_duration_minutes = statistics.mean(trade_durations) if trade_durations else 0

    # =============================================================================
    # CONSISTENCY METRICS (Key for Random's approach)
    # =============================================================================

    # Profit/Loss streaks
    def calculate_streaks(pnl_list):
        if not pnl_list:
            return [], []

        profit_streaks = []
        loss_streaks = []
        current_profit_streak = 0
        current_loss_streak = 0

        for pnl in pnl_list:
            if pnl > 0:
                current_profit_streak += 1
                if current_loss_streak > 0:
                    loss_streaks.append(current_loss_streak)
                    current_loss_streak = 0
            elif pnl < 0:
                current_loss_streak += 1
                if current_profit_streak > 0:
                    profit_streaks.append(current_profit_streak)
                    current_profit_streak = 0
            # Break even trades reset both streaks
            else:
                if current_profit_streak > 0:
                    profit_streaks.append(current_profit_streak)
                    current_profit_streak = 0
                if current_loss_streak > 0:
                    loss_streaks.append(current_loss_streak)
                    current_loss_streak = 0

        # Add final streak if exists
        if current_profit_streak > 0:
            profit_streaks.append(current_profit_streak)
        if current_loss_streak > 0:
            loss_streaks.append(current_loss_streak)

        return profit_streaks, loss_streaks

    profit_streaks, loss_streaks = calculate_streaks(trade_pnls)

    median_profit_streak = statistics.median(profit_streaks) if profit_streaks else 0
    median_loss_streak = statistics.median(loss_streaks) if loss_streaks else 0

    # Weekly/Monthly consistency
    weekly_pnl_values = list(weekly_pnls.values())
    monthly_pnl_values = list(monthly_pnls.values())

    positive_weeks = len([w for w in weekly_pnl_values if w > 0])
    positive_months = len([m for m in monthly_pnl_values if m > 0])

    weekly_consistency = (positive_weeks / len(weekly_pnl_values) * 100) if weekly_pnl_values else 0
    monthly_consistency = (positive_months / len(monthly_pnl_values) * 100) if monthly_pnl_values else 0

    # Average Weekly MFE (Random's metric)
    avg_weekly_mfe = statistics.mean([max(0, w) for w in weekly_pnl_values]) if weekly_pnl_values else 0

    # Skewness of Returns (distribution shape)
    if len(trade_pnls) >= 3:
        mean_pnl = statistics.mean(trade_pnls)
        std_pnl = statistics.stdev(trade_pnls)
        if std_pnl > 0:
            skewness = sum(((x - mean_pnl) / std_pnl) ** 3 for x in trade_pnls) / len(trade_pnls)
        else:
            skewness = 0
    else:
        skewness = 0

    # =============================================================================
    # CUSTOM RANDOM METRICS
    # =============================================================================

    # ROR (Rate of Return) - Custom calculation
    if total_trades > 0:
        initial_balance = 100000  # Assume $100k starting balance
        ror = (total_pnl / initial_balance) * 100
    else:
        ror = 0

    # Quarterly Risk-Reward Analysis
    quarterly_rr = 0
    if avg_loss != 0:
        quarterly_rr = abs(avg_win / avg_loss)

    # Compile all analytics
    analytics = {
        # Performance Metrics
        'net_pnl': round(total_pnl, 2),
        'strike_rate': round(strike_rate, 1),
        'profit_factor': round(profit_factor, 2),
        'trade_frequency': round(trade_frequency, 2),
        'expected_value': round(expected_value, 2),
        'average_profit': round(avg_win, 2),
        'median_profit': round(median_profit, 2),
        'daily_ev': round(daily_ev, 2),
        'mfe_equity': round(mfe_equity, 2),
        'pct_days_positive': round(pct_days_positive, 1),
        'skewness_returns': round(skewness, 3),
        'ror': round(ror, 2),

        # Risk Metrics
        'kelly_fraction': round(kelly_fraction * 100, 1),
        'max_drawdown': round(max_drawdown, 2),
        'median_drawdown': round(median_drawdown, 2),
        'average_drawdown': round(avg_drawdown, 2),
        'longest_drawdown_duration': longest_drawdown_duration,
        'median_drawdown_duration': round(median_drawdown_duration, 1),

        # Trading Stats
        'total_moves': total_trades,
        'profitable_moves': profitable_moves,
        'losing_moves': losing_moves,
        'average_loss': round(avg_loss, 2),
        'loss_rate': round(loss_rate, 1),
        'avg_duration_minutes': round(avg_duration_minutes, 1),

        # Consistency
        'median_profit_streak': round(median_profit_streak, 1),
        'median_loss_streak': round(median_loss_streak, 1),
        'weekly_consistency': round(weekly_consistency, 1),
        'monthly_consistency': round(monthly_consistency, 1),
        'avg_weekly_mfe': round(avg_weekly_mfe, 2),
        'quarterly_rr': round(quarterly_rr, 2),

        # Raw data for calculations
        'total_trades': total_trades,
        'winning_count': winning_count,
        'losing_count': losing_count,
        'total_days': total_days,
        'positive_days': positive_days,
        'total_weeks': len(weekly_pnl_values),
        'positive_weeks': positive_weeks,
        'total_months': len(monthly_pnl_values),
        'positive_months': positive_months,
    }

    return analytics


def prepare_equity_curve_data(trades):
    """
    Prepare equity curve data for chart visualization.
    Based on Random's emphasis on equity curve analysis.
    """
    if not trades:
        return []

    # Sort trades by entry timestamp
    sorted_trades = sorted(trades, key=lambda t: t.entry_timestamp if t.entry_timestamp else datetime.min)

    equity_data = []
    running_pnl = 0

    for i, trade in enumerate(sorted_trades):
        pnl = float(calculate_trade_pnl(trade))
        running_pnl += pnl

        equity_data.append({
            'trade_number': i + 1,
            'date': trade.entry_timestamp.strftime('%Y-%m-%d %H:%M') if trade.entry_timestamp else '',
            'pnl': round(pnl, 2),
            'running_pnl': round(running_pnl, 2),
            'instrument': trade.instrument.symbol if trade.instrument else 'Unknown'
        })

    return equity_data


def generate_model_insights(model, analytics):
    """
    Generate model-specific insights based on Random's (Matt Mickey) methodology.
    Provides actionable feedback for improving the trading model.
    """
    insights = {
        'strengths': [],
        'areas_for_improvement': [],
        'random_methodology_notes': [],
        'recommended_actions': []
    }

    if not analytics:
        return insights

    # Analyze based on Random's key metrics

    # Strike Rate Analysis
    strike_rate = analytics.get('strike_rate', 0)
    if strike_rate >= 60:
        insights['strengths'].append(f"Excellent strike rate of {strike_rate}% - well above Random's typical targets")
    elif strike_rate >= 45:
        insights['strengths'].append(
            f"Solid strike rate of {strike_rate}% - within acceptable range for trending strategies")
    else:
        insights['areas_for_improvement'].append(
            f"Strike rate of {strike_rate}% needs improvement - review entry criteria")

    # Profit Factor Analysis
    profit_factor = analytics.get('profit_factor', 0)
    if profit_factor >= 2.0:
        insights['strengths'].append(
            f"Outstanding profit factor of {profit_factor:.2f} - excellent risk/reward management")
    elif profit_factor >= 1.5:
        insights['strengths'].append(f"Good profit factor of {profit_factor:.2f} - model is profitable")
    elif profit_factor >= 1.2:
        insights['areas_for_improvement'].append(
            f"Marginal profit factor of {profit_factor:.2f} - tighten stop losses or improve targets")
    else:
        insights['areas_for_improvement'].append(
            f"Poor profit factor of {profit_factor:.2f} - fundamental review needed")

    # Consistency Analysis
    weekly_consistency = analytics.get('weekly_consistency', 0)
    if weekly_consistency >= 70:
        insights['strengths'].append(f"Excellent weekly consistency at {weekly_consistency}%")
    elif weekly_consistency >= 50:
        insights['areas_for_improvement'].append(f"Weekly consistency of {weekly_consistency}% could be improved")
    else:
        insights['areas_for_improvement'].append(
            f"Poor weekly consistency at {weekly_consistency}% - review model activation criteria")

    # Kelly Fraction Analysis
    kelly_fraction = analytics.get('kelly_fraction', 0)
    if kelly_fraction >= 15:
        insights['strengths'].append(f"High optimal risk of {kelly_fraction}% suggests strong edge")
        insights['recommended_actions'].append("Consider increasing position size based on Kelly criterion")
    elif kelly_fraction >= 5:
        insights['random_methodology_notes'].append(
            f"Moderate optimal risk of {kelly_fraction}% - suitable for consistent allocation")
    else:
        insights['areas_for_improvement'].append(
            f"Low optimal risk of {kelly_fraction}% - model needs refinement before scaling")

    # Drawdown Analysis
    max_drawdown = analytics.get('max_drawdown', 0)
    if max_drawdown <= 2:
        insights['strengths'].append(f"Excellent drawdown control at ${max_drawdown:.0f}")
    elif max_drawdown <= 5:
        insights['random_methodology_notes'].append(f"Acceptable drawdown of ${max_drawdown:.0f} - monitor closely")
    else:
        insights['areas_for_improvement'].append(f"High drawdown of ${max_drawdown:.0f} - review risk management rules")

    # Model-Specific Insights (based on model name)
    model_name = model.name.lower()
    if '0930' in model_name or 'snap' in model_name:
        insights['random_methodology_notes'].append(
            "9:30 models should focus on quick scalps with tight risk management")
        if analytics.get('avg_duration_minutes', 0) > 30:
            insights['areas_for_improvement'].append("9:30 trades holding too long - review time-based exits")

    elif 'hod' in model_name or 'lod' in model_name:
        insights['random_methodology_notes'].append("HOD/LOD models require patience for proper structural setups")
        if analytics.get('trade_frequency', 0) > 2:
            insights['areas_for_improvement'].append("HOD/LOD taking too many trades - be more selective")

    elif 'p12' in model_name:
        insights['random_methodology_notes'].append("P12 models should align with daily bias and session behavior")
        insights['recommended_actions'].append("Review P12 scenario classification accuracy")

    # Overall Recommendations
    if analytics.get('total_trades', 0) < 30:
        insights['recommended_actions'].append("Gather more trade data for statistically significant analysis")

    total_pnl = analytics.get('net_pnl', 0)
    if total_pnl > 0:
        insights['recommended_actions'].append("Consider transitioning to live trading or increasing position size")
    else:
        insights['recommended_actions'].append("Focus on back-testing and paper trading until consistent profitability")

    return insights