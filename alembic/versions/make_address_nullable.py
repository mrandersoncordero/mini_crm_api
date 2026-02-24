"""Make address field nullable in clients table

Revision ID: make_address_nullable
Revises: make_phone_nullable
Create Date: 2026-02-24 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "make_address_nullable"
down_revision: Union[str, Sequence[str], None] = "make_phone_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make address field nullable."""
    op.alter_column("clients", "address", nullable=True)


def downgrade() -> None:
    """Make address field not nullable."""
    op.alter_column("clients", "address", nullable=False)
