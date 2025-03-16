"""add collection_progress to audiences

Revision ID: add_collection_progress_to_audiences
Revises: ef3d746cdbea
Create Date: 2025-03-12 14:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_collection_progress_to_audiences'
down_revision: Union[str, None] = 'ef3d746cdbea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add collection_progress column with default value of 0
    op.add_column('audiences', sa.Column('collection_progress', sa.Float(), nullable=True, server_default='0'))


def downgrade() -> None:
    # Remove collection_progress column
    op.drop_column('audiences', 'collection_progress') 