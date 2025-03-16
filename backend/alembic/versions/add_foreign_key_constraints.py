"""add foreign key constraints

Revision ID: add_foreign_key_constraints
Revises: merge_heads
Create Date: 2025-03-14 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_foreign_key_constraints'
down_revision: Union[str, None] = 'merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add foreign key constraint to redditpost
    op.create_foreign_key(
        'fk_redditpost_subreddit',
        'redditpost',
        'subreddits',
        ['subreddit_name'],
        ['name'],
        ondelete='CASCADE'
    )

    # Add foreign key constraints to audience_subreddits
    op.create_foreign_key(
        'fk_audience_subreddits_audience',
        'audience_subreddits',
        'audiences',
        ['audience_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_audience_subreddits_subreddit',
        'audience_subreddits',
        'subreddits',
        ['subreddit_name'],
        ['name'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Remove foreign key constraints
    op.drop_constraint('fk_redditpost_subreddit', 'redditpost', type_='foreignkey')
    op.drop_constraint('fk_audience_subreddits_audience', 'audience_subreddits', type_='foreignkey')
    op.drop_constraint('fk_audience_subreddits_subreddit', 'audience_subreddits', type_='foreignkey') 