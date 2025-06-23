"""add_color_category_to_tags

Revision ID: 409ee41635b8
Revises: 3d2cce3f35cc
Create Date: 2025-06-22 22:29:55.583000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '409ee41635b8'
down_revision = '74826de7ba1e'
branch_labels = None
depends_on = None


def upgrade():
    # Add color_category column
    op.add_column('tag', sa.Column('color_category', sa.String(20), nullable=True))

    # Set default colors based on tag names
    connection = op.get_bind()

    # Set good tags to green
    good_tags = ["Front Run", "Confirmation", "Retest", "Proper Stop", "Let Run", "Partial Profit", "Disciplined",
                 "Patient", "Calm", "Confident", "Followed Plan"]
    for tag_name in good_tags:
        connection.execute(
            sa.text("UPDATE tag SET color_category = 'good' WHERE name = :name"),
            {'name': tag_name}
        )

    # Set bad tags to red
    bad_tags = ["Chased Entry", "Late Entry", "Moved Stop", "Cut Short", "FOMO", "Revenge Trading", "Impulsive",
                "Anxious", "Broke Rules", "Overconfident"]
    for tag_name in bad_tags:
        connection.execute(
            sa.text("UPDATE tag SET color_category = 'bad' WHERE name = :name"),
            {'name': tag_name}
        )

    # Set all others to neutral
    connection.execute(
        sa.text("UPDATE tag SET color_category = 'neutral' WHERE color_category IS NULL")
    )


def downgrade():
    op.drop_column('tag', 'color_category')