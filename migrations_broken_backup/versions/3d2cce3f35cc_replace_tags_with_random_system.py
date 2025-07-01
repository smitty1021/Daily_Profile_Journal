"""replace_tags_with_random_system

Revision ID: 3d2cce3f35cc
Revises: a48b01750c17
Create Date: 2025-06-22 21:46:38.651000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '3d2cce3f35cc'
down_revision = 'a48b01750c17'
branch_labels = None
depends_on = None


def upgrade():
    """Remove old default tags and create Random's trading system tags"""

    # Get database connection
    connection = op.get_bind()

    # Remove all existing default tags first
    connection.execute(sa.text("DELETE FROM tag WHERE is_default = true"))

    # Insert Random's trading system tags
    random_tags = [
        # Setup & Strategy
        ("0930 Open", "SETUP_STRATEGY", True, True),
        ("HOD LOD", "SETUP_STRATEGY", True, True),
        ("P12", "SETUP_STRATEGY", True, True),
        ("Captain Backtest", "SETUP_STRATEGY", True, True),
        ("Quarter Trade", "SETUP_STRATEGY", True, True),
        ("05 Box", "SETUP_STRATEGY", True, True),
        ("Three Hour Quarter", "SETUP_STRATEGY", True, True),
        ("Midnight Open", "SETUP_STRATEGY", True, True),
        ("Breakout", "SETUP_STRATEGY", True, True),
        ("Mean Reversion", "SETUP_STRATEGY", True, True),

        # Market Conditions
        ("DWP", "MARKET_CONDITIONS", True, True),
        ("DNP", "MARKET_CONDITIONS", True, True),
        ("R1", "MARKET_CONDITIONS", True, True),
        ("R2", "MARKET_CONDITIONS", True, True),
        ("Asian Session", "MARKET_CONDITIONS", True, True),
        ("London Session", "MARKET_CONDITIONS", True, True),
        ("NY1 Session", "MARKET_CONDITIONS", True, True),
        ("NY2 Session", "MARKET_CONDITIONS", True, True),
        ("High Volatility", "MARKET_CONDITIONS", True, True),
        ("Low Volatility", "MARKET_CONDITIONS", True, True),
        ("News Driven", "MARKET_CONDITIONS", True, True),
        ("Extended Target", "MARKET_CONDITIONS", True, True),

        # Execution & Management
        ("Front Run", "EXECUTION_MANAGEMENT", True, True),

        ("Retest", "EXECUTION_MANAGEMENT", True, True),
        ("Chased Entry", "EXECUTION_MANAGEMENT", True, True),
        ("Late Entry", "EXECUTION_MANAGEMENT", True, True),
        ("Proper Stop", "EXECUTION_MANAGEMENT", True, True),
        ("Moved Stop", "EXECUTION_MANAGEMENT", True, True),
        ("Cut Short", "EXECUTION_MANAGEMENT", True, True),
        ("Let Run", "EXECUTION_MANAGEMENT", True, True),
        ("Partial Profit", "EXECUTION_MANAGEMENT", True, True),
        ("Limit Order", "EXECUTION_MANAGEMENT", True, True),
        ("Market Order", "EXECUTION_MANAGEMENT", True, True),

        # Psychological & Emotional
        ("Disciplined", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Patient", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Calm", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Confident", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Followed Plan", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("FOMO", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Revenge Trading", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Impulsive", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Anxious", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Broke Rules", "PSYCHOLOGICAL_EMOTIONAL", True, True),
        ("Overconfident", "PSYCHOLOGICAL_EMOTIONAL", True, True),
    ]

    # Insert the new tags
    for name, category, is_default, is_active in random_tags:
        connection.execute(
            sa.text("INSERT INTO tag (name, category, user_id, is_default, is_active, created_at) VALUES (:name, :category, :user_id, :is_default, :is_active, :created_at)"),
            {
                'name': name,
                'category': category,
                'user_id': None,
                'is_default': is_default,
                'is_active': is_active,
                'created_at': datetime.utcnow()
            }
        )


def downgrade():
    """Remove Random's tags - cannot restore old tags automatically"""
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM tag WHERE is_default = true"))