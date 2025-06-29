"""Add many-to-many relationship for trade tags

Revision ID: 042aaf3c4a67
Revises: ae25eb922218
Create Date: 2025-06-18 17:28:49.391913

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '042aaf3c4a67'
down_revision = 'ae25eb922218'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_tag_user'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('trade_tags',
    sa.Column('trade_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
    sa.ForeignKeyConstraint(['trade_id'], ['trade.id'], ),
    sa.PrimaryKeyConstraint('trade_id', 'tag_id')
    )
    with op.batch_alter_table('trade', schema=None) as batch_op:
        batch_op.drop_column('tags')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trade', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tags', sa.VARCHAR(length=255), nullable=True))

    op.drop_table('trade_tags')
    op.drop_table('tag')
    # ### end Alembic commands ###
