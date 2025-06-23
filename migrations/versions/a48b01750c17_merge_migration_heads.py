"""merge_migration_heads

Revision ID: a48b01750c17
Revises: add_tag_performance_rating_corrected, cc84d7c42c2b
Create Date: 2025-06-22 21:46:22.784846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a48b01750c17'
down_revision = ('add_tag_performance_rating_corrected', 'cc84d7c42c2b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
