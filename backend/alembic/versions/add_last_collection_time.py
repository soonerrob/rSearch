"""add_last_collection_time

Revision ID: add_last_collection_time
Revises: 4926322dbf18
Create Date: 2025-03-17 01:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_last_collection_time'
down_revision: Union[str, None] = '4926322dbf18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_collection_time column with timezone support
    op.add_column('audiences', sa.Column('last_collection_time', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove last_collection_time column
    op.drop_column('audiences', 'last_collection_time') 