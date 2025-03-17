"""update_theme_scores

Revision ID: 9976d8ed077e
Revises: 0f7557a2ba0f
Create Date: 2024-03-16 16:35:54.112

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9976d8ed077e'
down_revision: Union[str, None] = '0f7557a2ba0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get connection
    connection = op.get_bind()

    # Update theme_scores in postanalysis
    connection.execute(sa.text("UPDATE postanalysis SET theme_scores = '{}' WHERE theme_scores IS NULL"))
    
    # Make theme_scores not null with default
    op.alter_column('postanalysis', 'theme_scores',
                existing_type=postgresql.JSONB(),
                nullable=False,
                server_default='{}')


def downgrade() -> None:
    # Revert postanalysis changes
    op.alter_column('postanalysis', 'theme_scores',
                existing_type=postgresql.JSONB(),
                nullable=True,
                server_default=None)
