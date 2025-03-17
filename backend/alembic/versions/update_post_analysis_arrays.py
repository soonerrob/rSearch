"""update post analysis arrays

Revision ID: update_post_analysis_arrays
Revises: add_post_analysis_table
Create Date: 2024-03-19 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

# revision identifiers, used by Alembic.
revision = 'update_post_analysis_arrays'
down_revision = 'add_post_analysis_table'
branch_labels = None
depends_on = None

def upgrade():
    # Add new array columns
    op.add_column('postanalysis', sa.Column('matching_themes_array', ARRAY(sa.String), nullable=True))
    op.add_column('postanalysis', sa.Column('keywords_array', ARRAY(sa.String), nullable=True))
    op.add_column('postanalysis', sa.Column('theme_scores_jsonb', JSONB, nullable=True))

def downgrade():
    # Drop new columns
    op.drop_column('postanalysis', 'matching_themes_array')
    op.drop_column('postanalysis', 'keywords_array')
    op.drop_column('postanalysis', 'theme_scores_jsonb') 