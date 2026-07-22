"""add booking application profile and progress

Revision ID: 20260721_0014
Revises: 20260719_0013
Create Date: 2026-07-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260721_0014"
down_revision: Union[str, None] = "20260719_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.add_column(sa.Column("tenant_profile", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("progress_steps", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("room_number", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("lease_start", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("lease_end", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("contract_status", sa.String(length=32), nullable=False, server_default="not_ready"))
        batch_op.add_column(sa.Column("admin_note", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_column("admin_note")
        batch_op.drop_column("contract_status")
        batch_op.drop_column("lease_end")
        batch_op.drop_column("lease_start")
        batch_op.drop_column("room_number")
        batch_op.drop_column("progress_steps")
        batch_op.drop_column("tenant_profile")
