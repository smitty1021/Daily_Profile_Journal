"""Remove duplicate unique constraint on tag name - SQLite version

Revision ID: fix_tag_unique_constraint_sqlite
Revises: 409ee41635b8
Create Date: 2025-06-23 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_tag_unique_constraint_sqlite'
down_revision = '409ee41635b8'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support dropping constraints, so we need to recreate the table

    # Step 1: Create a new table with the correct constraints
    op.create_table('tag_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('category', sa.Enum('SETUP_STRATEGY', 'MARKET_CONDITIONS', 'EXECUTION_MANAGEMENT', 'PSYCHOLOGICAL_EMOTIONAL', name='tagcategory'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('color_category', sa.String(length=20), nullable=True, default='neutral'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_tag_user'),
        sa.PrimaryKeyConstraint('id'),
        # Only keep the composite unique constraint, not the simple name constraint
        sa.UniqueConstraint('name', 'user_id', name='uq_tag_name_user')
    )

    # Step 2: Copy data from old table to new table
    op.execute("INSERT INTO tag_new SELECT * FROM tag")

    # Step 3: Drop the old table
    op.drop_table('tag')

    # Step 4: Rename the new table to the original name
    op.rename_table('tag_new', 'tag')

    # Step 5: Recreate indexes
    op.create_index('idx_tag_default_active', 'tag', ['is_default', 'is_active'])
    op.create_index('idx_tag_user_category', 'tag', ['user_id', 'category'])


def downgrade():
    # To downgrade, we would recreate with the old constraint structure
    # But this is complex and likely not needed for your use case
    pass