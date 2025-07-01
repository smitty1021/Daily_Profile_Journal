"""add_tag_performance_rating_corrected

Revision ID: ac4a3df0b6a6
Revises: a041d0fd112b
Create Date: 2025-06-22 18:52:39.079377

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tag_performance_rating_corrected'
down_revision = 'a041d0fd112b'
branch_labels = None
depends_on = None


def upgrade():
    # First, check if column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tag')]

    if 'performance_rating' not in columns:
        # Add performance_rating column as string first
        op.add_column('tag', sa.Column('performance_rating', sa.String(10), nullable=True))

    # Set default value for existing tags to 'INFO' (enum name, not value)
    op.execute(
        "UPDATE tag SET performance_rating = 'INFO' WHERE performance_rating IS NULL OR performance_rating = 'info'")

    # Now make it non-nullable
    with op.batch_alter_table('tag') as batch_op:
        batch_op.alter_column('performance_rating', nullable=False, server_default='INFO')


def downgrade():
    op.drop_column('tag', 'performance_rating')