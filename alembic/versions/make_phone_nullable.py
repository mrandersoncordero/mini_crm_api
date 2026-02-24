"""Make phone field nullable in clients table

Revision ID: make_phone_nullable
Revises: 20b4b370bab5
Create Date: 2026-02-24 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "make_phone_nullable"
down_revision: Union[str, Sequence[str], None] = "20b4b370bab5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make phone field nullable."""
    op.alter_column("clients", "phone", nullable=True)


def downgrade() -> None:
    """Make phone field not nullable."""
    op.alter_column("clients", "phone", nullable=False)
