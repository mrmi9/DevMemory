"""Add study card review schedule fields.

Revision ID: 20260529_0003
Revises: 20260529_0002
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260529_0003"
down_revision = "20260529_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("study_cards", sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("study_cards", sa.Column("last_reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("study_cards", sa.Column("next_review_at", sa.DateTime(), nullable=True))
    op.alter_column("study_cards", "review_count", server_default=None)


def downgrade() -> None:
    op.drop_column("study_cards", "next_review_at")
    op.drop_column("study_cards", "last_reviewed_at")
    op.drop_column("study_cards", "review_count")
