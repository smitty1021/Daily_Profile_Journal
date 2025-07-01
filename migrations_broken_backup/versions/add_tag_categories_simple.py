"""Add tag categories and default tags support

Revision ID: add_tag_categories_simple
Revises: 042aaf3c4a67
Create Date: 2025-06-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_tag_categories_simple'
down_revision = '042aaf3c4a67'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns one by one
    op.add_column('tag', sa.Column('category', sa.String(50), nullable=True))
    op.add_column('tag', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('tag', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('tag', sa.Column('created_at', sa.DateTime(), nullable=True))

    # Update existing data
    op.execute("UPDATE tag SET category = 'SETUP_STRATEGY' WHERE category IS NULL")
    op.execute("UPDATE tag SET created_at = datetime('now') WHERE created_at IS NULL")

    # Make columns non-nullable after updating
    with op.batch_alter_table('tag') as batch_op:
        batch_op.alter_column('category', nullable=False)
        batch_op.alter_column('created_at', nullable=False)
        batch_op.alter_column('user_id', nullable=True)  # Allow NULL for default tags


def downgrade():
    op.drop_column('tag', 'created_at')
    op.drop_column('tag', 'is_active')
    op.drop_column('tag', 'is_default')
    op.drop_column('tag', 'category')

    with op.batch_alter_table('tag') as batch_op:
        batch_op.alter_column('user_id', nullable=False)