"""add_tag_performance_rating

Revision ID: a041d0fd112b
Revises: 83ccd12ab838
Create Date: 2025-06-22 18:33:17.262909

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a041d0fd112b'
down_revision = '83ccd12ab838'
branch_labels = None
depends_on = None


def upgrade():
    # Add performance_rating column to tag table
    op.add_column('tag', sa.Column('performance_rating', sa.String(10), nullable=True))

    # Set default value for existing tags
    op.execute("UPDATE tag SET performance_rating = 'info' WHERE performance_rating IS NULL")

    # Make column non-nullable after setting defaults
    with op.batch_alter_table('tag') as batch_op:
        batch_op.alter_column('performance_rating', nullable=False)


def downgrade():
    op.drop_column('tag', 'performance_rating')