"""add_missing_subreddit_fields

Revision ID: 3df60bc2636f
Revises: d3b86475982a
Create Date: 2025-03-12 20:26:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3df60bc2636f'
down_revision: Union[str, None] = 'd3b86475982a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing fields to subreddits table
    op.add_column('subreddits', sa.Column('relevance_score', sa.Float(), nullable=True, server_default='0.0'))


def downgrade() -> None:
    # Remove added columns
    op.drop_column('subreddits', 'relevance_score')
