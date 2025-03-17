"""comment schema update

Revision ID: comment_schema_update
Revises: 
Create Date: 2024-03-16 23:30:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'comment_schema_update'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old comment table if it exists
    op.execute('DROP TABLE IF EXISTS comment CASCADE')
    
    # Drop and recreate comments table
    op.execute('DROP TABLE IF EXISTS comments CASCADE')
    
    # Create new comments table
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reddit_id', sa.String(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('path', postgresql.ARRAY(sa.Integer()), nullable=True, server_default='{}'),
        sa.Column('is_submitter', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('distinguished', sa.String(), nullable=True),
        sa.Column('stickied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('awards', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('edited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('engagement_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['post_id'], ['redditpost.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reddit_id')
    )
    op.create_index(op.f('ix_comments_reddit_id'), 'comments', ['reddit_id'], unique=True)


def downgrade() -> None:
    # Drop new comments table
    op.execute('DROP TABLE IF EXISTS comments CASCADE')
    
    # Recreate old comment table
    op.create_table(
        'comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('comment_id', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('body', sa.String(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_utc', sa.Float(), nullable=False),
        sa.Column('path', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('is_submitter', sa.Boolean(), nullable=False),
        sa.Column('permalink', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['redditpost.reddit_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    ) 