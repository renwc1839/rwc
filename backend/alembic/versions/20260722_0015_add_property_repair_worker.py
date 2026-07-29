"""add responsible repair worker to properties

Revision ID: 20260722_0015
Revises: 20260721_0014
Create Date: 2026-07-22 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0015"
down_revision: Union[str, None] = "20260721_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("properties") as batch_op:
        batch_op.add_column(sa.Column("repair_worker_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_properties_repair_worker_id", ["repair_worker_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_properties_repair_worker_id_users",
            "users",
            ["repair_worker_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("properties") as batch_op:
        batch_op.drop_constraint("fk_properties_repair_worker_id_users", type_="foreignkey")
        batch_op.drop_index("ix_properties_repair_worker_id")
        batch_op.drop_column("repair_worker_id")
