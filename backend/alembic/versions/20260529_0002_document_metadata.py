"""Add document metadata fields.

Revision ID: 20260529_0002
Revises: 20260529_0001
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260529_0002"
down_revision = "20260529_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    json_default = sa.text("'[]'::json") if bind.dialect.name == "postgresql" else sa.text("'[]'")
    op.add_column("documents", sa.Column("chapter", sa.String(length=160), nullable=False, server_default=""))
    op.add_column("documents", sa.Column("tags", sa.JSON(), nullable=False, server_default=json_default))
    op.alter_column("documents", "chapter", server_default=None)
    op.alter_column("documents", "tags", server_default=None)


def downgrade() -> None:
    op.drop_column("documents", "tags")
    op.drop_column("documents", "chapter")
