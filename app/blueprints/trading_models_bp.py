# CORRECTED trading_models_bp.py
# This version fixes all the issues with your existing project structure

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import TradingModel, Trade  # Import your TradingModel from app/models.py
from app.forms import TradingModelForm  # Import your TradingModelForm from app/forms.py
import statistics
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Define the blueprint:
trading_models_bp = Blueprint('trading_models', __name__,
                              template_folder='../templates/models')


# Replace the existing models_list route with this:
@trading_models_bp.route('/')
@login_required
def models_list():
    """View all trading models (default + personal)"""
    user_models = TradingModel.query.filter_by(user_id=current_user.id, is_default=False).all()
    default_models = TradingModel.get_default_models()

    # Get trade counts for all models
    models_with_counts = []

    # Process user models
    for model in user_models:
        trade_count = Trade.query.filter_by(
            trading_model_id=model.id,
            user_id=current_user.id
        ).count()
        models_with_counts.append({
            'model': model,
            'trade_count': trade_count,
            'is_default': False
        })

    # Process default models
    for model in default_models:
        trade_count = Trade.query.filter_by(
            trading_model_id=model.id,
            user_id=current_user.id
        ).count()
        models_with_counts.append({
            'model': model,
            'trade_count': trade_count,
            'is_default': True
        })

    return render_template('view_trading_models_list.html',
                           title='Trading Models',
                           user_models=user_models,
                           default_models=default_models,
                           models_with_counts=models_with_counts)


@trading_models_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_trading_model():
    """Handles the creation of a new trading model."""
    form = TradingModelForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        # Check if a model with the same name already exists for THIS user
        existing_model = TradingModel.query.filter_by(name=name, user_id=current_user.id).first()
        if existing_model:
            flash(f'A trading model with the name "{name}" already exists for you. Please choose a different name.',
                  'warning')
        else:
            new_model = TradingModel(user_id=current_user.id)  # Associate with the logged-in user
            form.populate_obj(new_model)  # Populates the new_model object with form data

            db.session.add(new_model)
            try:
                db.session.commit()
                current_app.logger.info(f"User {current_user.username} added new trading model: {name}")
                flash(f'Trading model "{name}" has been added successfully!', 'success')
                return redirect(url_for('trading_models.models_list'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error adding trading model for user {current_user.username}: {e}",
                                         exc_info=True)
                flash(f'An error occurred while adding the trading model: {str(e)}', 'danger')
    else:
        if request.method == 'POST':  # If form submitted but not valid
            flash('Please correct the errors in the form.', 'danger')

    return render_template('add_trading_model.html', title="Add New Trading Model", form=form)


@trading_models_bp.route('/edit/<int:model_id>', methods=['GET', 'POST'])
@login_required
def edit_trading_model(model_id):
    """Handles editing an existing trading model."""
    # Fetch the model ensuring it belongs to the current user
    model_to_edit = TradingModel.query.filter_by(id=model_id, user_id=current_user.id).first_or_404()
    form = TradingModelForm(obj=model_to_edit)  # Pre-populate the form with the model's current data

    if form.validate_on_submit():
        new_name = form.name.data.strip()
        # Check if another model (excluding the current one) by the same user has the new name
        conflicting_model = TradingModel.query.filter(
            TradingModel.name == new_name,
            TradingModel.id != model_id,  # Exclude the current model being edited
            TradingModel.user_id == current_user.id
        ).first()

        if conflicting_model:
            flash(f'Another trading model with the name "{new_name}" already exists for you.', 'warning')
        else:
            form.populate_obj(model_to_edit)  # Update the model_to_edit object with new form data
            try:
                db.session.commit()
                current_app.logger.info(
                    f"User {current_user.username} edited trading model ID: {model_id}, Name: {new_name}")
                flash(f'Trading model "{model_to_edit.name}" has been updated successfully!', 'success')
                return redirect(url_for('trading_models.models_list'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Error updating trading model ID {model_id} for user {current_user.username}: {e}", exc_info=True)
                flash(f'An error occurred while updating the trading model: {str(e)}', 'danger')
    elif request.method == 'POST':  # If form submitted but not valid
        flash('Please correct the errors in the form before saving.', 'danger')

    return render_template('edit_trading_model.html', title="Edit Trading Model", form=form, model=model_to_edit)


@trading_models_bp.route('/delete/<int:model_id>', methods=['POST'])  # Use POST for delete actions
@login_required
def delete_trading_model(model_id):
    """Handles deleting a trading model."""
    # Fetch the model ensuring it belongs to the current user
    model_to_delete = TradingModel.query.filter_by(id=model_id, user_id=current_user.id).first_or_404()

    # Check if the model is associated with any trades before deleting
    if model_to_delete.trades.first():
        flash(
            f'Cannot delete model "{model_to_delete.name}" as it is currently associated with existing trades. Please mark it as inactive or reassign trades first.',
            'danger')
        return redirect(url_for('trading_models.models_list'))

    try:
        model_name_for_log = model_to_delete.name  # Get name before deleting
        db.session.delete(model_to_delete)
        db.session.commit()
        current_app.logger.info(
            f"User {current_user.username} deleted trading model: {model_name_for_log} (ID: {model_id})")
        flash(f'Trading model "{model_name_for_log}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting trading model ID {model_id} for user {current_user.username}: {e}",
                                 exc_info=True)
        flash(f'An error occurred while deleting the trading model: {str(e)}', 'danger')

    return redirect(url_for('trading_models.models_list'))


@trading_models_bp.route('/view/<int:model_id>')
@login_required
def view_model_detail(model_id):
    """
    Detailed analytics page for a specific trading model.
    Shows comprehensive performance metrics based on Random's (Matt Mickey) methodology.
    """
    # Get the trading model - allow viewing of default models
    if current_user.is_admin():
        model = TradingModel.query.get_or_404(model_id)
    else:
        # Users can view their own models OR default models
        model = TradingModel.query.filter(
            db.or_(
                db.and_(TradingModel.id == model_id, TradingModel.user_id == current_user.id),
                db.and_(TradingModel.id == model_id, TradingModel.is_default == True)
            )
        ).first_or_404()

    # Get all trades for this model (only user's trades)
    trades_query = Trade.query.filter_by(
        trading_model_id=model_id,
        user_id=current_user.id
    ).order_by(Trade.trade_date.desc(), Trade.id.desc())

    trades = trades_query.all()

    # If no trades, show empty state
    if not trades:
        return render_template('model_detail.html',
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

    return render_template('model_detail.html',
                           model=model,
                           trades=recent_trades,
                           total_trades=len(trades),
                           analytics=analytics,
                           equity_data=json.dumps(equity_data),
                           model_insights=model_insights,
                           has_trades=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_model_analytics(trades):
    """Calculate comprehensive trading model analytics based on Random's methodology."""
    if not trades:
        return {}

    # Basic trade data preparation
    trade_pnls = []
    winning_trades = []
    losing_trades = []
    daily_pnls = {}
    weekly_pnls = {}

    for trade in trades:
        # Use the stored P&L from your database
        pnl = trade.pnl if trade.pnl is not None else 0
        trade_pnls.append(float(pnl))

        if pnl > 0:
            winning_trades.append(float(pnl))
        elif pnl < 0:
            losing_trades.append(float(pnl))

        # Group by time periods
        trade_date = trade.trade_date
        if trade_date:
            daily_pnls[trade_date] = daily_pnls.get(trade_date, 0) + float(pnl)
            week_key = trade_date.strftime('%Y-W%U')
            weekly_pnls[week_key] = weekly_pnls.get(week_key, 0) + float(pnl)

    # Core calculations
    total_pnl = sum(trade_pnls)
    total_trades = len(trades)
    winning_count = len(winning_trades)
    strike_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0

    avg_win = statistics.mean(winning_trades) if winning_trades else 0
    avg_loss = statistics.mean(losing_trades) if losing_trades else 0

    total_wins = sum(winning_trades) if winning_trades else 0
    total_losses = abs(sum(losing_trades)) if losing_trades else 0
    profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf') if total_wins > 0 else 0

    expected_value = statistics.mean(trade_pnls) if trade_pnls else 0

    # Kelly Fraction calculation
    if avg_loss != 0 and profit_factor > 1:
        kelly_fraction = (strike_rate / 100 * abs(avg_win / avg_loss) - (1 - strike_rate / 100)) / abs(
            avg_win / avg_loss)
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
    else:
        kelly_fraction = 0

    # Drawdown analysis
    running_pnl = 0
    equity_curve = []
    peak_equity = 0
    max_drawdown = 0
    peak = 0

    for pnl in trade_pnls:
        running_pnl += pnl
        equity_curve.append(running_pnl)
        peak_equity = max(peak_equity, running_pnl)

        if running_pnl > peak:
            peak = running_pnl
        else:
            drawdown = peak - running_pnl
            max_drawdown = max(max_drawdown, drawdown)

    # Consistency metrics
    daily_pnl_values = list(daily_pnls.values())
    weekly_pnl_values = list(weekly_pnls.values())

    positive_days = len([d for d in daily_pnl_values if d > 0])
    positive_weeks = len([w for w in weekly_pnl_values if w > 0])

    pct_days_positive = (positive_days / len(daily_pnl_values) * 100) if daily_pnl_values else 0
    weekly_consistency = (positive_weeks / len(weekly_pnl_values) * 100) if weekly_pnl_values else 0

    return {
        'net_pnl': round(total_pnl, 2),
        'strike_rate': round(strike_rate, 1),
        'profit_factor': round(profit_factor, 2),
        'expected_value': round(expected_value, 2),
        'kelly_fraction': round(kelly_fraction * 100, 1),
        'max_drawdown': round(max_drawdown, 2),
        'mfe_equity': round(peak_equity, 2),
        'pct_days_positive': round(pct_days_positive, 1),
        'weekly_consistency': round(weekly_consistency, 1),
        'total_moves': total_trades,
        'average_profit': round(avg_win, 2),
        'average_loss': round(avg_loss, 2),
        'trade_frequency': round(total_trades / max(len(daily_pnl_values), 1), 2),
        'median_drawdown': round(
            statistics.median([peak - eq for eq in equity_curve if peak - eq > 0]) if equity_curve else 0, 2),
        'longest_drawdown_duration': 0,  # Simplified for now
        'avg_duration_minutes': 30,  # Placeholder - calculate based on your trade duration logic
        'monthly_consistency': weekly_consistency,  # Simplified
        'median_profit_streak': 2,  # Placeholder
        'median_loss_streak': 1,  # Placeholder
        'avg_weekly_mfe': round(statistics.mean([max(0, w) for w in weekly_pnl_values]) if weekly_pnl_values else 0, 2),
        'ror': round((total_pnl / 100000) * 100, 2),  # Assume $100k account
        'quarterly_rr': round(abs(avg_win / avg_loss) if avg_loss != 0 else 0, 2),
        'skewness_returns': 0,  # Placeholder
        'daily_ev': round(expected_value * (total_trades / max(len(daily_pnl_values), 1)), 2)
    }


def prepare_equity_curve_data(trades):
    """Prepare equity curve data for chart visualization."""
    if not trades:
        return []

    sorted_trades = sorted(trades, key=lambda t: (t.trade_date, t.id))

    equity_data = []
    running_pnl = 0

    for i, trade in enumerate(sorted_trades):
        # Use stored P&L from database
        pnl = float(trade.pnl) if trade.pnl is not None else 0
        running_pnl += pnl

        equity_data.append({
            'trade_number': i + 1,
            'date': trade.trade_date.strftime('%Y-%m-%d') if trade.trade_date else '',
            'pnl': round(pnl, 2),
            'running_pnl': round(running_pnl, 2),
            'instrument': trade.instrument if trade.instrument else 'Unknown'
        })

    return equity_data


def generate_model_insights(model, analytics):
    """Generate model insights based on Random's methodology."""
    insights = {
        'strengths': [],
        'areas_for_improvement': [],
        'random_methodology_notes': [],
        'recommended_actions': []
    }

    if not analytics:
        return insights

    # Strike rate analysis
    strike_rate = analytics.get('strike_rate', 0)
    if strike_rate >= 60:
        insights['strengths'].append(f"Excellent strike rate of {strike_rate}% - well above Random's targets")
    elif strike_rate >= 45:
        insights['strengths'].append(f"Solid strike rate of {strike_rate}% - acceptable for trending strategies")
    else:
        insights['areas_for_improvement'].append(f"Strike rate of {strike_rate}% needs improvement")

    # Profit factor analysis
    profit_factor = analytics.get('profit_factor', 0)
    if profit_factor >= 2.0:
        insights['strengths'].append(f"Outstanding profit factor of {profit_factor:.2f}")
    elif profit_factor >= 1.2:
        insights['strengths'].append(f"Profitable model with factor of {profit_factor:.2f}")
    else:
        insights['areas_for_improvement'].append(f"Poor profit factor of {profit_factor:.2f} - review needed")

    # Model-specific insights
    model_name = model.name.lower()
    if '0930' in model_name or 'snap' in model_name:
        insights['random_methodology_notes'].append("9:30 models should focus on quick scalps with tight risk")
    elif 'hod' in model_name or 'lod' in model_name:
        insights['random_methodology_notes'].append("HOD/LOD models require patience for structural setups")
    elif 'p12' in model_name:
        insights['random_methodology_notes'].append("P12 models should align with daily bias and session behavior")

    return insights