"""merge heads

Revision ID: merge_heads
Revises: 68d16e518e8c, remove_subreddit_names_from_audiences
Create Date: 2025-03-14 13:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'merge_heads'
down_revision: Union[str, None] = ('68d16e518e8c', 'remove_subreddit_names_from_audiences')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 