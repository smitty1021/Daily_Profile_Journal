from flask import Blueprint, render_template, session, current_app
from flask_login import login_required
from ..models import Activity

# Defines the blueprint. The first argument, 'main', is the internal name.
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    """
    Renders the main dashboard page after a user has logged in.
    """
    # The 'base.html' template (which this extends) handles the sidebar state
    # by reading directly from the session, so no special logic is needed here.
    return render_template('main/index.html', title="Dashboard", Activity=Activity)