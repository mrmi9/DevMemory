"""Add system settings table.

Revision ID: 20260529_0004
Revises: 20260529_0003
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260529_0004"
down_revision = "20260529_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("system_settings"):
        return
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.alter_column("system_settings", "value", server_default=None)


def downgrade() -> None:
    op.drop_table("system_settings")
