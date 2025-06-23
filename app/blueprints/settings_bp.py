from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Settings, Tag, TagCategory
from app.forms import TagForm
import json

settings_bp = Blueprint('settings', __name__, template_folder='../templates/settings')


@settings_bp.route('/')
@login_required
def view_settings():
    """Main settings page with tags management integrated"""
    # Get user's tags organized by category
    tags_by_category = Tag.get_tags_by_category(current_user.id)

    # Handle theme changes
    if request.method == 'POST' and request.form.get('form_name') == 'change_theme':
        theme = request.form.get('theme', 'dark')
        session['theme'] = theme

        # Update user settings
        user_settings = Settings.get_for_user(current_user.id)
        user_settings.theme = theme
        try:
            db.session.commit()
            flash(f'Theme changed to {theme.title()}', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating theme for user {current_user.id}: {e}")
            flash('Error updating theme', 'danger')

        return redirect(url_for('settings.view_settings'))

    return render_template('settings/settings.html',
                           title='Settings',
                           tags_by_category=tags_by_category,
                           TagCategory=TagCategory)
    # REMOVED: csrf_token=generate_csrf() - let the template use csrf_token() function


@settings_bp.route('/tags/create', methods=['POST'])
@login_required
def create_tag():
    """Create a new user tag via AJAX"""
    try:
        # Debug logging
        current_app.logger.info(f"Create tag request from user {current_user.id}")
        current_app.logger.info(f"Request JSON: {request.json}")

        name = request.json.get('name', '').strip()
        category_name = request.json.get('category', '')

        if not name or not category_name:
            return jsonify({'success': False, 'message': 'Name and category are required'})

        # Validate category
        try:
            category = TagCategory[category_name]
        except KeyError:
            return jsonify({'success': False, 'message': 'Invalid category'})

        # Check for duplicates (including defaults)
        existing = Tag.query.filter(
            db.or_(
                db.and_(Tag.name == name, Tag.user_id == current_user.id),
                db.and_(Tag.name == name, Tag.is_default == True)
            )
        ).first()

        if existing:
            return jsonify({'success': False, 'message': 'Tag already exists'})

        # Create new tag
        new_tag = Tag(
            name=name,
            category=category,
            user_id=current_user.id,
            is_default=False,
            is_active=True
        )

        db.session.add(new_tag)
        db.session.commit()

        current_app.logger.info(f"Successfully created tag: {name}")

        return jsonify({
            'success': True,
            'message': f'Tag "{name}" created successfully',
            'tag': {
                'id': new_tag.id,
                'name': new_tag.name,
                'category': new_tag.category.name,
                'is_default': new_tag.is_default
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating tag: {e}")
        return jsonify({'success': False, 'message': f'Error creating tag: {str(e)}'})


@settings_bp.route('/tags/<int:tag_id>/edit', methods=['POST'])
@login_required
def edit_tag(tag_id):
    """Edit a user tag via AJAX"""
    try:
        tag = Tag.query.get_or_404(tag_id)

        # Users can only edit their own tags (not defaults)
        if tag.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permission denied'})

        name = request.json.get('name', '').strip()
        category_name = request.json.get('category', '')

        if not name or not category_name:
            return jsonify({'success': False, 'message': 'Name and category are required'})

        # Validate category
        try:
            category = TagCategory[category_name]
        except KeyError:
            return jsonify({'success': False, 'message': 'Invalid category'})

        # Check for duplicates (excluding current tag)
        existing = Tag.query.filter(
            Tag.id != tag_id,
            db.or_(
                db.and_(Tag.name == name, Tag.user_id == current_user.id),
                db.and_(Tag.name == name, Tag.is_default == True)
            )
        ).first()

        if existing:
            return jsonify({'success': False, 'message': 'Tag name already exists'})

        # Update tag
        tag.name = name
        tag.category = category
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Tag "{name}" updated successfully',
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'category': tag.category.name,
                'is_default': tag.is_default
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing tag {tag_id}: {e}")
        return jsonify({'success': False, 'message': 'Error updating tag'})


@settings_bp.route('/tags')
@login_required
def manage_tags():
    """User tags management page"""
    # Get default tags (available to all users)
    default_tags = Tag.query.filter_by(is_default=True, is_active=True).order_by(Tag.name).all()

    # Get user's personal tags
    user_tags = Tag.query.filter_by(user_id=current_user.id).order_by(Tag.name).all()

    # Get user's selected default tags (many-to-many relationship)
    user_selected_defaults = current_user.selected_default_tags if hasattr(current_user,
                                                                           'selected_default_tags') else []

    return render_template('settings/tags.html',
                           title='Manage Tags',
                           default_tags=default_tags,
                           user_tags=user_tags,
                           user_selected_defaults=user_selected_defaults)


@settings_bp.route('/tags/toggle-default/<int:tag_id>', methods=['POST'])
@login_required
def toggle_default_tag(tag_id):
    """Toggle a default tag for the current user"""
    tag = Tag.query.get_or_404(tag_id)

    if not tag.is_default:
        return jsonify({'success': False, 'message': 'Can only toggle default tags'})

    # Add/remove tag from user's selected defaults
    if tag in current_user.selected_default_tags:
        current_user.selected_default_tags.remove(tag)
        action = 'removed'
    else:
        current_user.selected_default_tags.append(tag)
        action = 'added'

    db.session.commit()

    return jsonify({
        'success': True,
        'action': action,
        'message': f'Tag "{tag.name}" {action} successfully'
    })


@settings_bp.route('/tags/restore-defaults', methods=['POST'])
@login_required
def restore_default_tags():
    """Restore all default tags for the user"""
    default_tags = Tag.query.filter_by(is_default=True, is_active=True).all()
    current_user.selected_default_tags = default_tags
    db.session.commit()

    flash(f'Restored {len(default_tags)} default tags', 'success')
    return redirect(url_for('settings.manage_tags'))


@settings_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    """Delete a user tag (including defaults copied to user)"""
    try:
        tag = Tag.query.get_or_404(tag_id)

        # Users can delete any tag in their collection (including copied defaults)
        # But they can't delete the master default tags (user_id=None)
        if tag.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permission denied'})

        tag_name = tag.name
        db.session.delete(tag)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Tag "{tag_name}" deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting tag {tag_id}: {e}")
        return jsonify({'success': False, 'message': 'Error deleting tag'})


@settings_bp.route('/tags/reset-defaults', methods=['POST'])
@login_required
def reset_default_tags():
    """Reset user's tags to current defaults"""
    try:
        # Delete user's custom tags
        Tag.query.filter_by(user_id=current_user.id).delete()

        # Copy current defaults
        copied_count = Tag.copy_defaults_to_user(current_user.id)

        flash(f'Reset complete! {copied_count} default tags have been restored.', 'success')
        return redirect(url_for('settings.view_settings'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting tags for user {current_user.id}: {e}")
        flash('Error resetting tags', 'danger')
        return redirect(url_for('settings.view_settings'))