"""add product_waste table and order delivery notification type

Revision ID: c3d5e7f9a1b3
Revises: f1a2b3c4d5e6
Create Date: 2026-08-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d5e7f9a1b3'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nuevo valor para notificaciones de entrega de órdenes de compra
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ORDER_DELIVERY_TODAY'")

    # Crear el tipo enum para motivo de merma si no existe
    op.execute("DO $$ BEGIN CREATE TYPE wastereason AS ENUM ('ROTTEN', 'BROKEN', 'EXPIRED', 'OTHER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    op.create_table(
        'product_waste',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False, index=True),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', postgresql.ENUM('ROTTEN', 'BROKEN', 'EXPIRED', 'OTHER', name='wastereason', create_type=False), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('product_waste')
    op.execute('DROP TYPE IF EXISTS wastereason')
    # PostgreSQL does not support removing values from enums natively.
    pass
