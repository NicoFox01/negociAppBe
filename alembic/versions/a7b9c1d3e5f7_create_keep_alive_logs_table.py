"""create_keep_alive_logs_table

Revision ID: a7b9c1d3e5f7
Revises: c3d5e7f9a1b3
Create Date: 2026-08-23 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b9c1d3e5f7'
down_revision: Union[str, None] = 'c3d5e7f9a1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabla de logs de keep-alive (pings de Supabase Cron para evitar pausa del proyecto)
    op.create_table(
        'keep_alive_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("timezone('utc'::text, now())"), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. RLS: habilitar y permitir INSERT anónimo desde el cron de Supabase con la anon key
    # asyncpg no admite múltiples comandos en un solo prepared statement -> un execute por comando
    op.execute("ALTER TABLE public.keep_alive_logs ENABLE ROW LEVEL SECURITY;")

    op.execute(
        'CREATE POLICY "Allow anon insert" '
        'ON public.keep_alive_logs '
        'FOR INSERT TO anon '
        'WITH CHECK (true);'
    )


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS "Allow anon insert" ON public.keep_alive_logs;')
    op.drop_table('keep_alive_logs')
