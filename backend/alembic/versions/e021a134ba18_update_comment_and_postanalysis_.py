"""update_comment_and_postanalysis_constraints_v2

Revision ID: e021a134ba18
Revises: 0f7557a2ba0f
Create Date: 2024-03-16 16:35:54.112

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e021a134ba18'
down_revision: Union[str, None] = '0f7557a2ba0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get connection
    connection = op.get_bind()

    # Update theme_scores in postanalysis
    connection.execute(sa.text("UPDATE postanalysis SET theme_scores = '{}' WHERE theme_scores IS NULL"))
    op.alter_column('postanalysis', 'theme_scores',
                existing_type=postgresql.JSONB(),
                nullable=False,
                server_default='{}')

    # Update comment table - path
    connection.execute(sa.text("UPDATE comment SET path = '{}' WHERE path IS NULL"))
    op.alter_column('comment', 'path',
                existing_type=postgresql.ARRAY(sa.INTEGER()),
                nullable=False,
                server_default='{}')

    # Clean up invalid references in comment table
    connection.execute(sa.text("""
        DELETE FROM comment 
        WHERE post_id IS NULL 
        OR post_id NOT IN (SELECT reddit_id FROM redditpost)
    """))

    # Make post_id not null
    op.alter_column('comment', 'post_id',
                existing_type=sa.VARCHAR(),
                nullable=False)

    # Drop existing foreign key if it exists
    try:
        op.drop_constraint('comment_post_id_fkey', 'comment', type_='foreignkey')
    except:
        pass

    # Create new foreign key with cascade delete
    op.create_foreign_key(
        'comment_post_id_fkey',
        'comment',
        'redditpost',
        ['post_id'],
        ['reddit_id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('comment_post_id_fkey', 'comment', type_='foreignkey')
    
    # Revert comment table changes
    op.alter_column('comment', 'post_id',
                existing_type=sa.VARCHAR(),
                nullable=True)
    op.alter_column('comment', 'path',
                existing_type=postgresql.ARRAY(sa.INTEGER()),
                nullable=True)
    
    # Revert postanalysis changes
    op.alter_column('postanalysis', 'theme_scores',
                existing_type=postgresql.JSONB(),
                nullable=True)
