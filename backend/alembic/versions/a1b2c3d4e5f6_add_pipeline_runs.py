"""add pipeline_runs table and FK on posts

Revision ID: a1b2c3d4e5f6
Revises: cc6846487867
Create Date: 2026-03-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'cc6846487867'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pipeline_runs table and add FK on posts."""
    op.create_table(
        'pipeline_runs',
        sa.Column('problem_description', sa.Text(), nullable=False, comment='Problem description used for this run.'),
        sa.Column('product_description', sa.Text(), nullable=True, comment='Product description used for this run.'),
        sa.Column('platform', sa.String(length=50), nullable=False, comment='Target platform for scraping.'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='running', comment='Current status: running, completed, failed.'),
        sa.Column('queries', sa.JSON(), nullable=True, comment='Search queries generated for this run.'),
        sa.Column('posts_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('posts_analysed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('posts_relevant', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('debates_run', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors', sa.JSON(), nullable=True, comment='Errors encountered during the run.'),
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Add pipeline_run_id FK column to posts
    op.add_column(
        'posts',
        sa.Column(
            'pipeline_run_id',
            UUID(as_uuid=True),
            sa.ForeignKey('pipeline_runs.id', ondelete='SET NULL'),
            nullable=True,
            comment='Pipeline run that discovered this post.',
        ),
    )
    op.create_index(
        op.f('ix_posts_pipeline_run_id'),
        'posts',
        ['pipeline_run_id'],
        unique=False,
    )


def downgrade() -> None:
    """Drop pipeline_run_id FK and pipeline_runs table."""
    op.drop_index(op.f('ix_posts_pipeline_run_id'), table_name='posts')
    op.drop_column('posts', 'pipeline_run_id')
    op.drop_table('pipeline_runs')
