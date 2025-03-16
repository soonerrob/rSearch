"""add relevance_score to subreddits

Revision ID: add_rel_score
Revises: ef3d746cdbea
Create Date: 2025-03-12 14:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_rel_score'
down_revision: Union[str, None] = 'ef3d746cdbea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add relevance_score column with default value of 0
    op.add_column('subreddits', sa.Column('relevance_score', sa.Float(), nullable=True, server_default='0'))


def downgrade() -> None:
    # Remove relevance_score column
    op.drop_column('subreddits', 'relevance_score') 