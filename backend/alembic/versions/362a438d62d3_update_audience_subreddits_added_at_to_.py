"""update_audience_subreddits_added_at_to_timestamptz

Revision ID: 362a438d62d3
Revises: 900859e8d54c
Create Date: 2025-03-16 16:22:14.159528

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '362a438d62d3'
down_revision: Union[str, None] = '900859e8d54c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update added_at column in audience_subreddits to use timestamptz
    op.execute('ALTER TABLE audience_subreddits ALTER COLUMN added_at TYPE timestamp with time zone')


def downgrade() -> None:
    # Revert added_at column in audience_subreddits back to timestamp without time zone
    op.execute('ALTER TABLE audience_subreddits ALTER COLUMN added_at TYPE timestamp without time zone')
