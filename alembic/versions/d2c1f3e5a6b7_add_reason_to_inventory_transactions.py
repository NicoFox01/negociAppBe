"""add_reason_to_inventory_transactions

Revision ID: d2c1f3e5a6b7
Revises: 8170ed9d4e97
Create Date: 2026-05-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2c1f3e5a6b7'
down_revision: Union[str, None] = '6b2f0122295c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inventory_transactions', sa.Column('reason', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('inventory_transactions', 'reason')
