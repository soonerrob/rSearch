"""add_reddit_parent_id_to_comments

Revision ID: 5af8a464ac30
Revises: f184c96f5c04
Create Date: 2024-03-16 12:34:56.789012

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5af8a464ac30'
down_revision: Union[str, None] = 'f184c96f5c04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reddit_parent_id column
    op.add_column('comments', sa.Column('reddit_parent_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_comments_reddit_parent_id'), 'comments', ['reddit_parent_id'], unique=False)


def downgrade() -> None:
    # Remove reddit_parent_id column and its index
    op.drop_index(op.f('ix_comments_reddit_parent_id'), table_name='comments')
    op.drop_column('comments', 'reddit_parent_id')
