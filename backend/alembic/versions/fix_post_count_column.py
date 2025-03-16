"""fix post_count column

Revision ID: fix_post_count_column
Revises: add_foreign_key_constraints
Create Date: 2025-03-14 14:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fix_post_count_column'
down_revision: Union[str, None] = 'add_foreign_key_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add post_count column with default value of 0
    op.alter_column('audiences', 'post_count',
                   existing_type=sa.Integer(),
                   nullable=False,
                   server_default='0')


def downgrade() -> None:
    # Remove default value and make nullable
    op.alter_column('audiences', 'post_count',
                   existing_type=sa.Integer(),
                   nullable=True,
                   server_default=None) 