"""add property manager owner to properties

Revision ID: 20260719_0013
Revises: 20260714_0012
Create Date: 2026-07-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260719_0013"
down_revision: Union[str, None] = "20260714_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("properties") as batch_op:
        batch_op.add_column(sa.Column("property_manager_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_properties_property_manager_id", ["property_manager_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_properties_property_manager_id_users",
            "users",
            ["property_manager_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("properties") as batch_op:
        batch_op.drop_constraint("fk_properties_property_manager_id_users", type_="foreignkey")
        batch_op.drop_index("ix_properties_property_manager_id")
        batch_op.drop_column("property_manager_id")
