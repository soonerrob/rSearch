"""update datetime columns to timestamptz

Revision ID: 93604021eee1
Revises: a4df81dcae01
Create Date: 2024-03-19 12:34:56.789012

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '93604021eee1'
down_revision: Union[str, None] = 'a4df81dcae01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update all datetime columns to use timestamptz
    op.alter_column('redditpost', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'')
    op.alter_column('redditpost', 'collected_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using='collected_at AT TIME ZONE \'UTC\'')
    
    # For comment.created_utc, we keep it as double precision since it's a Unix timestamp
    
    op.alter_column('audiences', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'')
    
    op.alter_column('subreddits', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'')


def downgrade() -> None:
    # Convert back to timezone-naive datetime
    op.alter_column('redditpost', 'created_at',
                    type_=sa.DateTime(timezone=False),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'')
    op.alter_column('redditpost', 'collected_at',
                    type_=sa.DateTime(timezone=False),
                    postgresql_using='collected_at AT TIME ZONE \'UTC\'')
    
    # For comment.created_utc, no change needed since it's a Unix timestamp
    
    op.alter_column('audiences', 'created_at',
                    type_=sa.DateTime(timezone=False),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'')
    
    op.alter_column('subreddits', 'created_at',
                    type_=sa.DateTime(timezone=False),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'')
