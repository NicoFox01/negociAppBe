"""add_missing_notification_types

Revision ID: f1a2b3c4d5e6
Revises: 9a1b2c3d4e5f
Create Date: 2026-05-29 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '9a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE 'STOCK_LOW_ALERT'")
    op.execute("ALTER TYPE notificationtype ADD VALUE 'PRODUCTION_REQUEST'")
    op.execute("ALTER TYPE notificationtype ADD VALUE 'PRODUCTION_COMPLETED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE 'PRODUCTION_CANCELLED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE 'SALE_CANCELLED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE 'SALE_REJECTED'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums natively.
    # A full enum type recreation would be needed in production.
    pass
