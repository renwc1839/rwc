"""add repair worker user role

Revision ID: 20260714_0012
Revises: 20260629_0011, 5ac4aa5f38f4
Create Date: 2026-07-14 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260714_0012"
down_revision: Union[str, tuple[str, str], None] = ("20260629_0011", "5ac4aa5f38f4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'repair_worker'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be safely removed without recreating the type.
    pass
