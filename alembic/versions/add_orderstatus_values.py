"""Add IN_PROGRESS and REJECTED to orderstatus enum

Revision ID: add_orderstatus_values
Revises: 
Create Date: 2026-04-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_orderstatus_values'
down_revision: Union[str, None] = '05363254d9d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values to orderstatus
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'IN_PROGRESS'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'REJECTED'")


def downgrade() -> None:
    pass