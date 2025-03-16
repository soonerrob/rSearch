"""add_collection_progress_column

Revision ID: 11afc683328f
Revises: add_is_collecting_column
Create Date: 2025-03-12 14:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '11afc683328f'
down_revision: Union[str, None] = 'add_is_collecting_column'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add collection_progress column with default value 0
    op.add_column('audiences', sa.Column('collection_progress', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove collection_progress column
    op.drop_column('audiences', 'collection_progress')
