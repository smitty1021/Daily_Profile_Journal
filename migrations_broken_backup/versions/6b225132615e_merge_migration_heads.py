"""Merge migration heads

Revision ID: 6b225132615e
Revises: 3273ad4c23d1, add_pnl_manual
Create Date: 2025-06-30 21:11:15.798904

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b225132615e'
down_revision = ('3273ad4c23d1', 'add_pnl_manual')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
