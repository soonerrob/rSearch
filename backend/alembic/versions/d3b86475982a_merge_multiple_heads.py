"""merge_multiple_heads

Revision ID: d3b86475982a
Revises: 11afc683328f, add_collection_progress_to_audiences, add_rel_score
Create Date: 2025-03-12 15:24:30.395875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3b86475982a'
down_revision: Union[str, None] = ('11afc683328f', 'add_collection_progress_to_audiences', 'add_rel_score')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
