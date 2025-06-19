"""Add tag categories and default tags support

Revision ID: add_tag_categories
Revises: [previous_revision_id]
Create Date: 2025-06-19 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_tag_categories'
down_revision = '042aaf3c4a67'  # Replace with your actual latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to existing tag table
    with op.batch_alter_table('tag', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

        # Make user_id nullable for default tags
        batch_op.alter_column('user_id', nullable=True)

        # Drop the old unique constraint on name only
        batch_op.drop_constraint('uq_tag_name', type_='unique')

        # Create new unique constraint on name + user_id
        batch_op.create_unique_constraint('uq_tag_name_user', ['name', 'user_id'])

        # Create indexes
        batch_op.create_index('idx_tag_user_category', ['user_id', 'category'])
        batch_op.create_index('idx_tag_default_active', ['is_default', 'is_active'])

    # Update existing tags with default category and timestamps
    op.execute("UPDATE tag SET category = 'Setup & Strategy' WHERE category IS NULL")
    op.execute("UPDATE tag SET created_at = datetime('now') WHERE created_at IS NULL")

    # Make category non-nullable after setting defaults
    with op.batch_alter_table('tag', schema=None) as batch_op:
        batch_op.alter_column('category', nullable=False)
        batch_op.alter_column('created_at', nullable=False)


def downgrade():
    with op.batch_alter_table('tag', schema=None) as batch_op:
        batch_op.drop_index('idx_tag_default_active')
        batch_op.drop_index('idx_tag_user_category')
        batch_op.drop_constraint('uq_tag_name_user', type_='unique')
        batch_op.create_unique_constraint('uq_tag_name', ['name'])
        batch_op.alter_column('user_id', nullable=False)
        batch_op.drop_column('created_at')
        batch_op.drop_column('is_active')
        batch_op.drop_column('is_default')
        batch_op.drop_column('category')
