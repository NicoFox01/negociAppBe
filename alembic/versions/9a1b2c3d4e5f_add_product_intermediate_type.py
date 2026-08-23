"""add_product_intermediate_type

Revision ID: 9a1b2c3d4e5f
Revises: e4f7a2b1c8d9
Create Date: 2026-05-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, None] = 'e4f7a2b1c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE producttype ADD VALUE 'PRODUCT_INTERMEDIATE'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums natively.
    # A full enum type recreation would be needed in production.
    pass
