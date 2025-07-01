"""Add pnl column to trade table - manual migration

Revision ID: add_pnl_manual
Revises: 0ee5b3d14ef5
Create Date: 2025-06-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_pnl_manual'
down_revision = '0ee5b3d14ef5'  # Use the latest revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Add the pnl column
    op.add_column('trade', sa.Column('pnl', sa.Float(), nullable=True))

    # Add index for better filtering performance
    op.create_index('ix_trade_pnl', 'trade', ['pnl'])


def downgrade():
    # Remove index and column
    op.drop_index('ix_trade_pnl', 'trade')
    op.drop_column('trade', 'pnl')