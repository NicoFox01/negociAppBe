"""add_user_id_to_inventory_transactions

Revision ID: e4f7a2b1c8d9
Revises: d2c1f3e5a6b7
Create Date: 2026-05-25 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e4f7a2b1c8d9'
down_revision: Union[str, None] = 'd2c1f3e5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inventory_transactions', sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, index=True))


def downgrade() -> None:
    op.drop_column('inventory_transactions', 'user_id')
