"""update_to_random_trading_system_tags

Revision ID: cc84d7c42c2b
Revises: add_tag_performance_rating_corrected
Create Date: 2025-06-22 21:04:26.506302

"""
from alembic import op
import sqlalchemy as sa
from app.models import Tag, TagCategory, db


def upgrade():
    """Remove old default tags and create Random's trading system tags"""

    # Get database connection
    connection = op.get_bind()

    # Remove all existing default tags
    connection.execute("DELETE FROM tag WHERE is_default = true")

    # Create Random's default tags using the updated method
    # This will be handled by running: flask seed-default-tags
    pass


def downgrade():
    """Remove Random's tags and restore old system"""
    connection = op.get_bind()

    # Remove Random's tags
    connection.execute("DELETE FROM tag WHERE is_default = true")

    # Note: Old tags cannot be automatically restored
    # Manual restoration required if needed
    pass
