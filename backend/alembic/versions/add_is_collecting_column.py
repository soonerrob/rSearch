"""add is_collecting column

Revision ID: add_is_collecting_column
Create Date: 2024-03-12 13:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_is_collecting_column'
down_revision: Union[str, None] = '70caa5326087'  # Points to the latest migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_collecting column with default value False
    op.add_column('audiences', sa.Column('is_collecting', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_collecting column
    op.drop_column('audiences', 'is_collecting')