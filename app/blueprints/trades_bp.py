# Step 1: Update the imports and helper functions in your trades_bp.py

# --- IMPORTS SECTION (Replace the existing imports) ---
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, Response, abort)
from ..forms import TradeForm
from ..models import Trade, Instrument  # Make sure Instrument is imported
from .. import db
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
import csv
import io
from datetime import date as py_date, datetime as py_datetime, time as py_time
from app.models import TagUsageStats
# This import is required for the fix
from flask_wtf.csrf import generate_csrf

from app import db
from app.models import Trade, EntryPoint, ExitPoint, TradingModel, NewsEventItem, TradeImage, Instrument, Tag, TagCategory
from app.models import Trade, Tag, EntryPoint, ExitPoint, TradingModel, NewsEventItem, TradeImage, Instrument, TagUsageStats
from app.forms import TradeForm, EntryPointForm, ExitPointForm, TradeFilterForm, ImportTradesForm
from app.utils import (_parse_form_float, _parse_form_int, _parse_form_time,
                       get_news_event_options, record_activity)

trades_bp = Blueprint('trades', __name__,
                      template_folder='../templates/trades',
                      url_prefix='/trades')

# --- UPDATED HELPER FUNCTIONS ---

def get_instrument_point_values():
    """
    Get current instrument point values from database using the new Instrument model.
    Falls back to hardcoded values if database fails.
    """
    try:
        # Use the new Instrument model method
        return Instrument.get_instrument_point_values()
    except Exception as e:
        current_app.logger.warning(f"Failed to get instrument point values from database: {e}")
        # Fallback to Random's common instruments (FIXED VALUES)
        return {
            'NQ': 20.0,    # Random's primary instrument - CORRECTED
            'ES': 50.0,    # E-mini S&P 500
            'YM': 5.0,     # E-mini Dow Jones
            'MNQ': 2.0,    # Micro Nasdaq
            'MES': 5.0,    # Micro S&P
            'MYM': 0.5,    # Micro Dow
            'Other': 1.0   # Default fallback
        }


def _is_allowed_image(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_IMAGE_EXTENSIONS',
                                                                     {'png', 'jpg', 'jpeg', 'gif'})


def _populate_tags_choices(form):
    """Populate dynamic choices for tags dropdown - grouped by category"""
    from app.models import Tag, TagCategory
    from flask_login import current_user


    # Get all available tags for the user
    all_tags = Tag.query.filter(
        db.or_(
            Tag.is_default == True,
            Tag.user_id == current_user.id
        )
    ).filter(Tag.is_active == True).order_by(Tag.category, Tag.name).all()

    if not all_tags:
        form.tags.choices = []
        return form

    # Use a dictionary to robustly group tags by category
    grouped_tags = {category: [] for category in TagCategory}

    for tag in all_tags:
        if tag.category in grouped_tags:
            # Convert tag.id to string since we removed coerce=int
            grouped_tags[tag.category].append((str(tag.id), tag.name))

    # Build the final choices list in optgroups format
    choices = []
    for category_enum, tags_list in grouped_tags.items():
        if tags_list:  # Only add categories that actually contain tags
            choices.append((category_enum.value, tags_list))

    form.tags.choices = choices
    return form


def _populate_trade_form_choices(form):
    """Populate dynamic choices for trading models and news events"""
    form.trading_model_id.choices = [(0, 'Select Model')] + \
                                    [(tm.id, tm.name) for tm in
                                     TradingModel.query.filter_by(user_id=current_user.id, is_active=True).order_by(
                                         TradingModel.name).all()]
    if hasattr(form, 'news_event_select'):
        form.news_event_select.choices = [('', '-- None --')] + [(event, event) for event in get_news_event_options() if
                                                                 event and event.lower() != 'none']
    return form


def _populate_filter_form_choices(filter_form):
    """Populate dynamic choices for filter form - instrument choices handled in form __init__"""
    filter_form.trading_model_id.choices = [(0, 'All Models')] + \
                                           [(tm.id, tm.name) for tm in
                                            TradingModel.query.filter_by(user_id=current_user.id,
                                                                         is_active=True).order_by(
                                                TradingModel.name).all()]
    # Note: Instrument choices are now handled in TradeFilterForm.__init__() method
    # This removes the dependency on TradeForm.instrument_choices
    return filter_form


# --- VIEW TRADES LIST ---
@trades_bp.route('/', methods=['GET'])
@login_required
def view_trades_list():
    from flask_wtf.csrf import generate_csrf

    filter_form = TradeFilterForm(request.args)
    _populate_filter_form_choices(filter_form)

    query = Trade.query.filter_by(user_id=current_user.id)

    # Apply filters
    if filter_form.start_date.data:
        query = query.filter(Trade.trade_date >= filter_form.start_date.data)
    if filter_form.end_date.data:
        query = query.filter(Trade.trade_date <= filter_form.end_date.data)
    if filter_form.instrument.data:
        query = query.filter(Trade.instrument == filter_form.instrument.data)
    if filter_form.direction.data:
        query = query.filter(Trade.direction == filter_form.direction.data)
    if filter_form.trading_model_id.data and filter_form.trading_model_id.data != 0:
        query = query.filter(Trade.trading_model_id == filter_form.trading_model_id.data)
    if filter_form.tags.data:
        # Handle tag filtering for many-to-many relationship
        tag_id = None

        # Parse tag_id from form data or URL parameter
        if isinstance(filter_form.tags.data, str) and filter_form.tags.data.isdigit():
            tag_id = int(filter_form.tags.data)
        elif isinstance(filter_form.tags.data, int):
            tag_id = filter_form.tags.data
        elif hasattr(filter_form.tags.data, '__iter__') and len(filter_form.tags.data) > 0:
            # Handle list/array of tag IDs (take the first one for now)
            first_tag = filter_form.tags.data[0]
            if isinstance(first_tag, str) and first_tag.isdigit():
                tag_id = int(first_tag)
            elif isinstance(first_tag, int):
                tag_id = first_tag

        # Also check URL parameters directly as fallback
        if not tag_id:
            tag_param = request.args.get('tags')
            if tag_param and tag_param.isdigit():
                tag_id = int(tag_param)

        # Apply the filter using the correct many-to-many syntax
        if tag_id:
            query = query.filter(Trade.tags.any(Tag.id == tag_id))

    # Handle sorting
    sort_by = request.args.get('sort', 'date_desc')

    if sort_by == 'pnl_desc':
        # Filter to only include trades with exits (closed trades) when sorting by PnL
        query = query.filter(Trade.exits.any())
        # Order by date first, we'll sort by PnL in Python after pagination
        query = query.order_by(Trade.trade_date.desc(), Trade.id.desc())
    elif sort_by == 'pnl_asc':
        # Filter to only include trades with exits (closed trades) when sorting by PnL
        query = query.filter(Trade.exits.any())
        # Order by date first, we'll sort by PnL in Python after pagination
        query = query.order_by(Trade.trade_date.desc(), Trade.id.desc())
    elif sort_by == 'date_asc':
        # Sort by date ascending
        query = query.order_by(Trade.trade_date.asc(), Trade.id.asc())
    elif sort_by == 'date_desc':
        # Sort by date descending
        query = query.order_by(Trade.trade_date.desc(), Trade.id.desc())
    else:
        # Default sorting by date descending
        query = query.order_by(Trade.trade_date.desc(), Trade.id.desc())

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PER_PAGE_TRADES', 10)

    trades_pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Only sort in Python if we're sorting by PnL (which can't be done in SQL due to calculated properties)
    if sort_by == 'pnl_desc':
        trades_pagination.items = sorted(trades_pagination.items,
                                         key=lambda t: t.gross_pnl if t.gross_pnl is not None else 0,
                                         reverse=True)
    elif sort_by == 'pnl_asc':
        trades_pagination.items = sorted(trades_pagination.items,
                                         key=lambda t: t.gross_pnl if t.gross_pnl is not None else 0,
                                         reverse=False)
    # For date sorting, we let the database ORDER BY handle it (no Python sorting needed)

    return render_template("trades/view_trades_list.html",
                           title="Trades List",
                           trades=trades_pagination.items,
                           pagination=trades_pagination,
                           filter_form=filter_form,
                           csrf_token=generate_csrf())


# --- ADD TRADE ---
@trades_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_trade():
    form = TradeForm()

    _populate_tags_choices(form)  # Call the function defined above
    _populate_trade_form_choices(form)

    if request.method == 'GET':
        if not form.entries.entries:
            form.entries.append_entry(None)
        if not form.exits.entries:
            form.exits.append_entry(None)

    instrument_point_values = get_instrument_point_values()

    if form.validate_on_submit():
        try:
            instrument = form.instrument.data
            point_value_for_trade = Instrument.get_point_value(instrument)

            new_trade = Trade(user_id=current_user.id)
            # --- (All your new_trade.field = form.field.data assignments remain the same) ---
            new_trade.instrument = instrument
            new_trade.trade_date = form.trade_date.data
            new_trade.direction = form.direction.data
            new_trade.point_value = point_value_for_trade
            new_trade.initial_stop_loss = _parse_form_float(form.initial_stop_loss.data)
            new_trade.terminus_target = _parse_form_float(form.terminus_target.data)
            new_trade.is_dca = form.is_dca.data
            new_trade.mae = _parse_form_float(form.mae.data)
            new_trade.mfe = _parse_form_float(form.mfe.data)
            new_trade.how_closed = form.how_closed.data if form.how_closed.data else None
            new_trade.rules_rating = form.rules_rating.data
            new_trade.management_rating = form.management_rating.data
            new_trade.target_rating = form.target_rating.data
            new_trade.entry_rating = form.entry_rating.data
            new_trade.preparation_rating = form.preparation_rating.data
            new_trade.trade_notes = form.trade_notes.data
            new_trade.psych_scored_highest = form.psych_scored_highest.data
            new_trade.psych_scored_lowest = form.psych_scored_lowest.data
            new_trade.overall_analysis_notes = form.overall_analysis_notes.data
            new_trade.trade_management_notes = form.trade_management_notes.data
            new_trade.errors_notes = form.errors_notes.data
            new_trade.improvements_notes = form.improvements_notes.data
            new_trade.screenshot_link = form.screenshot_link.data
            new_trade.trading_model_id = form.trading_model_id.data if form.trading_model_id.data and form.trading_model_id.data != 0 else None
            new_trade.news_event = form.news_event_select.data if form.news_event_select.data else None

            # --- MODIFIED: The old tags assignment has been removed ---

            db.session.add(new_trade)
            db.session.flush()

            # --- MODIFIED: Added the logic to process and link the selected tags ---
            if form.tags.data:
                # Filter out any non-digit strings and convert to integers
                tag_ids = []
                for tag_id in form.tags.data:
                    if isinstance(tag_id, str) and tag_id.isdigit():
                        tag_ids.append(int(tag_id))
                    elif isinstance(tag_id, int):
                        tag_ids.append(tag_id)

                # Get the actual tag objects
                selected_tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
                new_trade.tags = selected_tags
                TagUsageStats.record_tag_usage(current_user.id, tag_ids)

                # --- (The rest of the function for processing entries, exits, and images remains the same) ---
            for entry_data in form.entries.data:
                if entry_data.get('entry_time') and entry_data.get('contracts') is not None and entry_data.get(
                        'entry_price') is not None:
                    entry = EntryPoint(trade_id=new_trade.id, entry_time=entry_data['entry_time'],
                                       contracts=entry_data['contracts'], entry_price=entry_data['entry_price'])
                    db.session.add(entry)
            for exit_data in form.exits.data:
                if exit_data.get('exit_time') and exit_data.get('contracts') is not None and exit_data.get(
                        'exit_price') is not None:
                    exit_point = ExitPoint(trade_id=new_trade.id, exit_time=exit_data['exit_time'],
                                           contracts=exit_data['contracts'], exit_price=exit_data['exit_price'])
                    db.session.add(exit_point)
                elif any(val for key, val in exit_data.items() if key != 'id' and val is not None and val != ''):
                    flash(
                        f"An exit for trade was partially filled and not saved. Please provide all of time, contracts, and price for a complete exit log.",
                        "warning")
            if form.trade_images.data:
                for image_file in form.trade_images.data:
                    if image_file and _is_allowed_image(image_file.filename):
                        original_filename = secure_filename(image_file.filename)
                        file_ext = os.path.splitext(original_filename)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder)
                        file_path = os.path.join(upload_folder, unique_filename)
                        try:
                            image_file.save(file_path)
                            trade_image = TradeImage(trade_id=new_trade.id, user_id=current_user.id,
                                                     filename=original_filename, filepath=unique_filename,
                                                     filesize=os.path.getsize(file_path), mime_type=image_file.mimetype)
                            db.session.add(trade_image)
                        except Exception as e_save:
                            current_app.logger.error(
                                f"Failed to save image {original_filename} for trade {new_trade.id}: {e_save}",
                                exc_info=True)
                            flash(f"Could not save image: {original_filename}", "warning")
                    elif image_file:
                        flash(f"Image type not allowed for file: {image_file.filename}", "warning")
            db.session.commit()
            record_activity('trade_logged', f"Logged new trade ID: {new_trade.id} for {new_trade.instrument}")
            flash(
                f'Trade for {new_trade.instrument} on {new_trade.trade_date.strftime("%Y-%m-%d")} logged successfully!',
                'success')
            return redirect(url_for('trades.view_trades_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error logging new trade for user {current_user.username}: {e}", exc_info=True)
            flash(f'An error occurred while logging the trade: {str(e)}', 'danger')

    elif request.method == 'POST':
        flash('Please correct the errors in the form and try again.', 'warning')
        if not form.entries.entries:
            form.entries.append_entry(None)
        if not form.exits.entries and len(form.exits.data) == 0:
            form.exits.append_entry(None)

    return render_template('trades/add_trade.html',
                           title='Log New Trade',
                           form=form,
                           instrument_point_values=instrument_point_values,
                           default_trade_date=py_date.today().strftime('%Y-%m-%d'))

# --- VIEW TRADE DETAIL ---
@trades_bp.route('/<int:trade_id>/view')
@login_required
def view_trade_detail(trade_id):
    trade = db.get_or_404(Trade, trade_id)
    if trade.user_id != current_user.id:
        abort(403)
    return render_template('trades/view_trade_detail.html', title="Trade Details", trade=trade)


# --- EDIT TRADE ---
@trades_bp.route('/<int:trade_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trade(trade_id):
    trade_to_edit = db.get_or_404(Trade, trade_id)
    if trade_to_edit.user_id != current_user.id:
        abort(403)

    form = TradeForm(obj=trade_to_edit)
    _populate_trade_form_choices(form)
    _populate_tags_choices(form)

    if request.method == 'GET':
        while len(form.entries) > 0: form.entries.pop_entry()
        for entry in trade_to_edit.entries.all():
            entry_form_data = {
                'id': entry.id, 'entry_time': entry.entry_time,
                'contracts': entry.contracts, 'entry_price': entry.entry_price
            }
            form.entries.append_entry(data=entry_form_data)
        if not form.entries.entries: form.entries.append_entry(None)

        while len(form.exits) > 0: form.exits.pop_entry()
        for exit_item in trade_to_edit.exits.all():
            exit_form_data = {
                'id': exit_item.id, 'exit_time': exit_item.exit_time,
                'contracts': exit_item.contracts, 'exit_price': exit_item.exit_price
            }
            form.exits.append_entry(data=exit_form_data)
        if not form.exits.entries: form.exits.append_entry(None)
        if trade_to_edit.tags:
            form.tags.data = [str(tag.id) for tag in trade_to_edit.tags]

    if form.validate_on_submit():
        try:
            # Populate main trade object fields from the form
            trade_to_edit.instrument = form.instrument.data
            trade_to_edit.trade_date = form.trade_date.data
            trade_to_edit.direction = form.direction.data
            trade_to_edit.point_value = Instrument.get_point_value(form.instrument.data)
            trade_to_edit.initial_stop_loss = _parse_form_float(form.initial_stop_loss.data)
            trade_to_edit.terminus_target = _parse_form_float(form.terminus_target.data)
            trade_to_edit.is_dca = form.is_dca.data
            trade_to_edit.mae = _parse_form_float(form.mae.data)
            trade_to_edit.mfe = _parse_form_float(form.mfe.data)
            trade_to_edit.trading_model_id = form.trading_model_id.data if form.trading_model_id.data and form.trading_model_id.data != 0 else None
            trade_to_edit.news_event = form.news_event_select.data if form.news_event_select.data else None
            trade_to_edit.how_closed = form.how_closed.data if form.how_closed.data else None
            trade_to_edit.rules_rating = form.rules_rating.data
            trade_to_edit.management_rating = form.management_rating.data
            trade_to_edit.target_rating = form.target_rating.data
            trade_to_edit.entry_rating = form.entry_rating.data
            trade_to_edit.preparation_rating = form.preparation_rating.data
            trade_to_edit.trade_notes = form.trade_notes.data
            trade_to_edit.psych_scored_highest = form.psych_scored_highest.data
            trade_to_edit.psych_scored_lowest = form.psych_scored_lowest.data
            trade_to_edit.overall_analysis_notes = form.overall_analysis_notes.data
            trade_to_edit.trade_management_notes = form.trade_management_notes.data
            trade_to_edit.errors_notes = form.errors_notes.data
            trade_to_edit.improvements_notes = form.improvements_notes.data
            trade_to_edit.screenshot_link = form.screenshot_link.data
            if form.tags.data:
                # Filter out any non-digit strings and convert to integers
                tag_ids = []
                for tag_id in form.tags.data:
                    if isinstance(tag_id, str) and tag_id.isdigit():
                        tag_ids.append(int(tag_id))
                    elif isinstance(tag_id, int):
                        tag_ids.append(tag_id)

                # Get the actual tag objects
                selected_tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
                trade_to_edit.tags = selected_tags
                TagUsageStats.record_tag_usage(current_user.id, tag_ids)
            else:
                trade_to_edit.tags = []

            # Handle Entries: Update existing, Add new, Delete removed
            current_entry_ids_in_db = {entry.id for entry in trade_to_edit.entries}
            submitted_entry_ids = set()
            new_entries_to_add = []

            for entry_form_data in form.entries.data:
                entry_id = entry_form_data.get('id')
                if entry_form_data.get('entry_time') and entry_form_data.get(
                        'contracts') is not None and entry_form_data.get('entry_price') is not None:
                    if entry_id:
                        entry_to_update = EntryPoint.query.get(entry_id)
                        if entry_to_update and entry_to_update.trade_id == trade_to_edit.id:
                            entry_to_update.entry_time = entry_form_data['entry_time']
                            entry_to_update.contracts = entry_form_data['contracts']
                            entry_to_update.entry_price = entry_form_data['entry_price']
                            submitted_entry_ids.add(entry_id)
                    else:
                        new_entries_to_add.append(EntryPoint(
                            trade_id=trade_to_edit.id, entry_time=entry_form_data['entry_time'],
                            contracts=entry_form_data['contracts'], entry_price=entry_form_data['entry_price']
                        ))
            for id_to_delete in current_entry_ids_in_db - submitted_entry_ids:
                entry_to_delete = EntryPoint.query.get(id_to_delete)
                if entry_to_delete: db.session.delete(entry_to_delete)
            for new_entry in new_entries_to_add:
                db.session.add(new_entry)

            # Handle Exits: Update existing, Add new, Delete removed
            current_exit_ids_in_db = {exit_item.id for exit_item in trade_to_edit.exits}
            submitted_exit_ids = set()
            new_exits_to_add = []
            for exit_form_data in form.exits.data:
                exit_id = exit_form_data.get('id')
                if exit_form_data.get('exit_time') and exit_form_data.get(
                        'contracts') is not None and exit_form_data.get('exit_price') is not None:
                    if exit_id:
                        exit_to_update = ExitPoint.query.get(exit_id)
                        if exit_to_update and exit_to_update.trade_id == trade_to_edit.id:
                            exit_to_update.exit_time = exit_form_data['exit_time']
                            exit_to_update.contracts = exit_form_data['contracts']
                            exit_to_update.exit_price = exit_form_data['exit_price']
                            submitted_exit_ids.add(exit_id)
                    else:
                        new_exits_to_add.append(ExitPoint(
                            trade_id=trade_to_edit.id, exit_time=exit_form_data['exit_time'],
                            contracts=exit_form_data['contracts'], exit_price=exit_form_data['exit_price']
                        ))
            for id_to_delete in current_exit_ids_in_db - submitted_exit_ids:
                exit_to_delete = ExitPoint.query.get(id_to_delete)
                if exit_to_delete: db.session.delete(exit_to_delete)
            for new_exit in new_exits_to_add:
                db.session.add(new_exit)

            # Handle image deletion
            for image in trade_to_edit.images:  # Iterate over a copy if modifying the list
                if request.form.get(f'delete_image_{image.id}'):
                    image_path_to_delete = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filepath)
                    if os.path.exists(image_path_to_delete):
                        try:
                            os.remove(image_path_to_delete)
                        except OSError:
                            current_app.logger.warning(f"Could not delete image file on disk: {image.filepath}")
                    db.session.delete(image)

            # Handle new image uploads
            if form.trade_images.data:
                for image_file in form.trade_images.data:
                    if image_file and _is_allowed_image(image_file.filename):
                        original_filename = secure_filename(image_file.filename)
                        file_ext = os.path.splitext(original_filename)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        file_path = os.path.join(upload_folder, unique_filename)
                        try:
                            image_file.save(file_path)
                            trade_image = TradeImage(
                                trade_id=trade_to_edit.id, user_id=current_user.id, filename=original_filename,
                                filepath=unique_filename, filesize=os.path.getsize(file_path),
                                mime_type=image_file.mimetype)
                            db.session.add(trade_image)
                        except Exception as e_save:
                            current_app.logger.error(
                                f"Failed to save new image during edit {original_filename} for trade {trade_to_edit.id}: {e_save}",
                                exc_info=True)

            db.session.commit()
            TagUsageStats.cleanup_unused_stats(current_user.id)
            flash('Trade updated successfully!', 'success')
            return redirect(url_for('trades.view_trade_detail', trade_id=trade_to_edit.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error editing trade {trade_id}: {e}", exc_info=True)
            flash(f'An error occurred while updating the trade: {str(e)}', 'danger')

    return render_template('trades/edit_trade.html', title="Edit Trade", form=form, trade=trade_to_edit)


# --- DELETE TRADE (Single) ---
@trades_bp.route('/<int:trade_id>/delete', methods=['POST'])
@login_required
def delete_trade(trade_id):
    trade_to_delete = db.get_or_404(Trade, trade_id)
    if trade_to_delete.user_id != current_user.id:
        abort(403)
    try:
        for img in trade_to_delete.images:
            if img.filepath:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], img.filepath))
                except OSError:
                    current_app.logger.warning(f"Could not delete image file: {img.filepath}")
        db.session.delete(trade_to_delete)  # Cascades should handle entries, exits, images in DB
        db.session.commit()
        TagUsageStats.cleanup_unused_stats(current_user.id)
        flash('Trade deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting trade {trade_id}: {e}", exc_info=True)
        flash('Error deleting trade. Please try again.', 'danger')
    return redirect(url_for('trades.view_trades_list'))


# --- BULK DELETE TRADES ---
@trades_bp.route('/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_trades():
    trade_ids_to_delete = request.form.getlist('trade_ids')
    if not trade_ids_to_delete:
        flash('No trades selected for deletion.', 'warning')
        return redirect(url_for('trades.view_trades_list'))

    deleted_count = 0
    error_count = 0
    for trade_id_str in trade_ids_to_delete:
        try:
            trade_id = int(trade_id_str)
            trade = Trade.query.get(trade_id)
            if trade and trade.user_id == current_user.id:
                for img in trade.images:
                    if img.filepath:
                        try:
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], img.filepath))
                        except OSError:
                            pass
                db.session.delete(trade)
                deleted_count += 1
            else:
                error_count += 1
        except ValueError:
            error_count += 1
        except Exception as e:
            error_count += 1
            current_app.logger.error(f"Error during bulk delete of trade ID {trade_id_str}: {e}", exc_info=True)

    if deleted_count > 0:
        try:
            db.session.commit()
            TagUsageStats.cleanup_unused_stats(current_user.id)
            flash(f'Successfully deleted {deleted_count} trade(s).', 'success')
        except Exception as e_commit:
            db.session.rollback()
            flash('An error occurred during bulk deletion commit.', 'danger')
            current_app.logger.error(f"Error committing bulk delete: {e_commit}", exc_info=True)
    if error_count > 0:
        flash(f'Could not delete {error_count} selected item(s) due to errors or permissions.', 'warning')

    return redirect(url_for('trades.view_trades_list'))


# --- EXPORT TRADES ---
@trades_bp.route('/export_csv', methods=['GET'])
@login_required
def export_trades_csv():
    filter_form = TradeFilterForm(request.args, meta={'csrf': False})
    _populate_filter_form_choices(filter_form)

    query = Trade.query.filter_by(user_id=current_user.id)
    if filter_form.start_date.data: query = query.filter(Trade.trade_date >= filter_form.start_date.data)
    if filter_form.end_date.data: query = query.filter(Trade.trade_date <= filter_form.end_date.data)
    if filter_form.instrument.data: query = query.filter(Trade.instrument == filter_form.instrument.data)
    if filter_form.direction.data: query = query.filter(Trade.direction == filter_form.direction.data)
    if filter_form.trading_model_id.data and filter_form.trading_model_id.data != 0:
        query = query.filter(Trade.trading_model_id == filter_form.trading_model_id.data)
    if filter_form.tags.data: query = query.filter(Trade.tags == filter_form.tags.data)

    trades_to_export = query.order_by(Trade.trade_date.asc()).all()

    if not trades_to_export:
        flash('No trades found matching current filters to export.', 'warning')
        return redirect(url_for('trades.view_trades_list', **request.args))

    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        'ID', 'Date', 'Instrument', 'Direction', 'Point Value',
        'Total Entry Contracts', 'Avg Entry Price', 'Total Exit Contracts', 'Avg Exit Price',
        'Gross P&L', 'R-Value (Initial)', 'Dollar Risk (Initial)',
        'Initial SL', 'Terminus Target', 'MAE', 'MFE', 'How Closed',
        'Trading Model', 'Tags', 'Trade Notes', 'Overall Analysis', 'Management Notes',
        'Errors', 'Improvements', 'External Screenshot Link'
        # Detailed entries/exits would require a more complex CSV or separate export
    ]
    writer.writerow(headers)
    for trade in trades_to_export:
        writer.writerow([
            trade.id, trade.trade_date.strftime('%Y-%m-%d'), trade.instrument, trade.direction, trade.point_value,
            trade.total_contracts_entered, trade.average_entry_price,
            trade.total_contracts_exited, trade.average_exit_price,
            trade.gross_pnl, trade.pnl_in_r, trade.dollar_risk,
            trade.initial_stop_loss, trade.terminus_target, trade.mae, trade.mfe,
            trade.how_closed, trade.trading_model.name if trade.trading_model else '',
            ', '.join([tag.name for tag in trade.tags]) if trade.tags else '', trade.trade_notes, trade.overall_analysis_notes, trade.trade_management_notes,
            trade.errors_notes, trade.improvements_notes, trade.screenshot_link
        ])
    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=trades_export.csv"})


# --- IMPORT TRADES ---
# In app/blueprints/trades_bp.py

# ... (other imports and routes as before) ...

@trades_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_trades():
    form = ImportTradesForm()
    if form.validate_on_submit():
        csv_file = form.csv_file.data
        try:
            stream = io.StringIO(csv_file.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.DictReader(stream)

            imported_count = 0
            error_count = 0
            error_details = []

            # MODIFIED: Updated header names to match the new CSV template
            header_map = {
                'date': 'Date (Req: YYYY-MM-DD)', 'instrument': 'Instrument (Req)', 'direction': 'Direction (Req)',
                'entry_time': 'Entry Time {i} (Req: HH:MM)', 'entry_contracts': 'Entry Contracts {i} (Req)',
                'entry_price': 'Entry Price {i} (Req)',
                'exit_time': 'Exit Time {i} (Req: HH:MM)', 'exit_contracts': 'Exit Contracts {i} (Req)',
                'exit_price': 'Exit Price {i} (Req)',
                'model': 'Trading Model', 'tags': 'Tags', 'how_closed': 'How Closed', 'sl': 'Initial SL',
                'tp': 'Terminus Target', 'mae': 'MAE', 'mfe': 'MFE', 'notes': 'Trade Notes'
            }
            # For optional entries/exits, the header might not have "(Req)"
            header_map_optional = {
                'entry_time': 'Entry Time {i} (HH:MM)', 'entry_contracts': 'Entry Contracts {i}',
                'entry_price': 'Entry Price {i}',
                'exit_time': 'Exit Time {i} (HH:MM)', 'exit_contracts': 'Exit Contracts {i}',
                'exit_price': 'Exit Price {i}'
            }

            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # --- 1. Validate required main trade data using new headers ---
                    trade_date_str = row.get(header_map['date'])
                    instrument = row.get(header_map['instrument'])
                    direction = row.get(header_map['direction'])

                    if not all([trade_date_str, instrument, direction]):
                        error_details.append(
                            f"Row {row_num + 1}: Missing required fields (Date, Instrument, or Direction).");
                        error_count += 1;
                        continue

                    trade_date = py_datetime.strptime(trade_date_str, '%Y-%m-%d').date()

                    # --- 2. Create the main Trade object ---
                    new_trade = Trade(user_id=current_user.id, trade_date=trade_date, instrument=instrument,
                                      direction=direction, point_value=Instrument.get_point_value(instrument))

                    # --- 3. Process Entries and Exits ---
                    entries_found = 0
                    # Look for up to 5 entries (you can increase this number)
                    for i in range(1, 6):
                        # Try both required and optional header formats
                        entry_time_hdr = header_map['entry_time'].format(i=i) if i == 1 else header_map_optional[
                            'entry_time'].format(i=i)
                        entry_contracts_hdr = header_map['entry_contracts'].format(i=i) if i == 1 else \
                        header_map_optional['entry_contracts'].format(i=i)
                        entry_price_hdr = header_map['entry_price'].format(i=i) if i == 1 else header_map_optional[
                            'entry_price'].format(i=i)

                        entry_time_str = row.get(entry_time_hdr) or row.get(
                            header_map_optional['entry_time'].format(i=i))
                        entry_contracts_str = row.get(entry_contracts_hdr) or row.get(
                            header_map_optional['entry_contracts'].format(i=i))
                        entry_price_str = row.get(entry_price_hdr) or row.get(
                            header_map_optional['entry_price'].format(i=i))

                        if entry_time_str and entry_contracts_str and entry_price_str:
                            new_trade.entries.append(EntryPoint(
                                entry_time=py_datetime.strptime(entry_time_str, '%H:%M').time(),
                                contracts=_parse_form_int(entry_contracts_str),
                                entry_price=_parse_form_float(entry_price_str)
                            ))
                            entries_found += 1

                    if entries_found == 0:
                        error_details.append(
                            f"Row {row_num + 1}: At least one full entry (Time, Contracts, Price) is required.");
                        error_count += 1;
                        continue

                    # Process Exit 1 (Required)
                    exit_time_1_str = row.get(header_map['exit_time'].format(i=1))
                    exit_contracts_1_str = row.get(header_map['exit_contracts'].format(i=1))
                    exit_price_1_str = row.get(header_map['exit_price'].format(i=1))

                    if not all([exit_time_1_str, exit_contracts_1_str, exit_price_1_str]):
                        error_details.append(f"Row {row_num + 1}: Missing required fields for first exit.");
                        error_count += 1;
                        continue

                    new_trade.exits.append(ExitPoint(
                        exit_time=py_datetime.strptime(exit_time_1_str, '%H:%M').time(),
                        contracts=_parse_form_int(exit_contracts_1_str),
                        exit_price=_parse_form_float(exit_price_1_str)
                    ))

                    # Look for optional additional exits
                    for i in range(2, 6):
                        exit_time_hdr = header_map_optional['exit_time'].format(i=i)
                        exit_contracts_hdr = header_map_optional['exit_contracts'].format(i=i)
                        exit_price_hdr = header_map_optional['exit_price'].format(i=i)

                        exit_time_str = row.get(exit_time_hdr)
                        exit_contracts_str = row.get(exit_contracts_hdr)
                        exit_price_str = row.get(exit_price_hdr)

                        if exit_time_str and exit_contracts_str and exit_price_str:
                            new_trade.exits.append(ExitPoint(
                                exit_time=py_datetime.strptime(exit_time_str, '%H:%M').time(),
                                contracts=_parse_form_int(exit_contracts_str),
                                exit_price=_parse_form_float(exit_price_str)
                            ))

                    # --- 4. Populate optional main trade fields ---
                    model_name = row.get(header_map['model'])
                    if model_name:
                        model = TradingModel.query.filter_by(user_id=current_user.id, name=model_name).first()
                        if model: new_trade.trading_model_id = model.id

                    new_trade.tags = row.get(header_map['tags'])
                    new_trade.how_closed = row.get(header_map['how_closed'])
                    new_trade.initial_stop_loss = _parse_form_float(row.get(header_map['sl']))
                    new_trade.terminus_target = _parse_form_float(row.get(header_map['tp']))
                    new_trade.mae = _parse_form_float(row.get(header_map['mae']))
                    new_trade.mfe = _parse_form_float(row.get(header_map['mfe']))
                    new_trade.trade_notes = row.get(header_map['notes'])

                    db.session.add(new_trade)
                    imported_count += 1
                except (ValueError, TypeError) as ve:
                    error_details.append(
                        f"Row {row_num + 1}: Data conversion error - {ve}. Check number/date/time formats.");
                    error_count += 1
                except Exception as e_row:
                    error_details.append(f"Row {row_num + 1}: Unexpected error - {e_row}.");
                    error_count += 1

            if imported_count > 0:
                db.session.commit()
                flash(f'Successfully imported {imported_count} trades.', 'success')
            else:
                db.session.rollback()

            if error_count > 0:
                flash(f'Skipped or had errors with {error_count} rows during import.', 'danger')
            if error_details:
                for err_detail in error_details[:5]:
                    flash(err_detail, 'warning')
                if len(error_details) > 5:
                    flash(f"...and {len(error_details) - 5} more errors.", 'warning')

            return redirect(url_for('trades.view_trades_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'A critical error occurred while processing the file: {str(e)}', 'danger')
            current_app.logger.error(f"Fatal error during trade import process: {e}", exc_info=True)

    return render_template('trades/import_trades.html', title="Import Trades", form=form)