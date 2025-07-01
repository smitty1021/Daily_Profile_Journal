"""add tag usage analytics

Revision ID: 83ccd12ab838
Revises: 1884c589f6fd
Create Date: 2025-06-20 20:01:56.790479

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '83ccd12ab838'
down_revision = '1884c589f6fd'
branch_labels = None
depends_on = None


def upgrade():
    # Create tag usage statistics table
    op.create_table('tag_usage_stats',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('tag_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
                    sa.Column('last_used', sa.DateTime(), nullable=True),
                    sa.Column('first_used', sa.DateTime(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('tag_id', 'user_id', name='unique_tag_user_usage')
                    )

    # Add indexes for performance
    op.create_index('idx_tag_usage_user_count', 'tag_usage_stats', ['user_id', 'usage_count'])
    op.create_index('idx_tag_usage_last_used', 'tag_usage_stats', ['last_used'])


def downgrade():
    op.drop_index('idx_tag_usage_last_used', 'tag_usage_stats')
    op.drop_index('idx_tag_usage_user_count', 'tag_usage_stats')
    op.drop_table('tag_usage_stats')