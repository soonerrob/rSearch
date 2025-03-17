"""update_remaining_datetime_columns_to_timestamptz

Revision ID: 900859e8d54c
Revises: 93604021eee1
Create Date: 2025-03-16 21:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '900859e8d54c'
down_revision: Union[str, None] = '93604021eee1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update created_at and updated_at columns in audiences table to use timestamptz
    op.alter_column('audiences', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               postgresql_using='created_at AT TIME ZONE \'UTC\'')
    
    op.alter_column('audiences', 'updated_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               postgresql_using='updated_at AT TIME ZONE \'UTC\'')


def downgrade() -> None:
    # Revert created_at and updated_at columns in audiences table back to timestamp without timezone
    op.alter_column('audiences', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
               postgresql_using='created_at AT TIME ZONE \'UTC\'')
    
    op.alter_column('audiences', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
               postgresql_using='updated_at AT TIME ZONE \'UTC\'')
