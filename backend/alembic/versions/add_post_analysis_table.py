"""add post analysis table

Revision ID: add_post_analysis_table
Revises: 0a6ff755ea3d
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_post_analysis_table'
down_revision: Union[str, None] = '0a6ff755ea3d'  # Point to current head
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'post_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('matching_themes', sa.String(), nullable=False, server_default=''),
        sa.Column('theme_scores', sa.String(), nullable=False, server_default='{}'),
        sa.Column('keywords', sa.String(), nullable=False, server_default=''),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['redditposts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_analysis_post_id'), 'post_analysis', ['post_id'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_post_analysis_post_id'), table_name='post_analysis')
    op.drop_table('post_analysis') 