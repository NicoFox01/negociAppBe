from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.inventory import InventoryTransaction, ProductWaste
from app.models.products import Product
from app.models.user import Users
from app.schemas.inventory import InventoryTransactionCreate, InventoryTransactionSchema
from app.models.enums import TransactionType, WasteReason

from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

from app.utils.pagination import paginate
from sqlalchemy.orm import joinedload
from sqlalchemy import func

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

WASTE_REASON_DISPLAY = {
    "ROTTEN": "Podrido",
    "BROKEN": "Roto",
    "EXPIRED": "Vencido",
    "OTHER": "Otro"
}

async def register_transaction(
    db: AsyncSession, 
    product_id: UUID, 
    quantity: float, 
    transaction_type: TransactionType, 
    tenant_id: UUID, 
    reference_id: Optional[UUID],
    reason: Optional[str] = None,
    user_id: Optional[UUID] = None,
    auto_commit: bool = True
):
    """
    Registra un movimiento de inventario y actualiza el stock del producto.

    auto_commit=True (default): commitea la transacción (uso aislado).
    auto_commit=False: NO commitea; el caller es responsable del commit
    para garantizar atomicidad en flujos compuestos (ventas, recepciones).
    """
    result = await db.execute(
        select(Product)
        .with_for_update()
        .where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404,  detail="Producto no encontrado")
    quantity = Decimal(str(quantity))
    if quantity == 0:
        raise HTTPException(status_code=404, detail="La cantidad no puede ser 0")
    if transaction_type == TransactionType.ADJUSTMENT:
        if quantity < 0:
            if product.stock_quantity < abs(quantity):
                raise HTTPException(status_code=400, detail="Stock insuficiente para merma")
        product.stock_quantity += quantity
    elif transaction_type == TransactionType.IN:
        product.stock_quantity += quantity
    elif transaction_type == TransactionType.OUT:
        if product.stock_quantity < quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente")
        product.stock_quantity -= quantity
    
    new_transaction = InventoryTransaction(
        tenant_id = tenant_id,
        product_id = product_id,
        user_id = user_id,
        transaction_type = transaction_type,
        quantity = quantity,
        reference_id = reference_id,
        reason = reason
    )
    db.add(new_transaction)
    db.add(product)
    if auto_commit:
        await db.commit()
        await db.refresh(new_transaction)
    else:
        await db.flush()
    return new_transaction

async def get_product_history(db: AsyncSession, product_id: UUID, tenant_id:UUID,  skip: int = 0, limit: int = 10):
    query = select(InventoryTransaction).options(
        joinedload(InventoryTransaction.user)
    ).where(
        InventoryTransaction.product_id == product_id,
        InventoryTransaction.tenant_id == tenant_id
    ).order_by(InventoryTransaction.created_at.desc())
    product_history = await db.execute(paginate(query, skip, limit))
    transactions = product_history.scalars().unique().all()
    for t in transactions:
        if t.user:
            t.user_name = t.user.username
            t.user_full_name = t.user.full_name
    return transactions


async def register_waste(
    db: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    quantity: float,
    reason: WasteReason,
    notes: Optional[str],
    user_id: UUID
) -> ProductWaste:
    """
    Registra merma de un producto: descuenta stock (OUT) y guarda el registro.
    Atómico: si falla el descuento no se guarda la merma y viceversa.
    """
    transaction = await register_transaction(
        db=db,
        product_id=product_id,
        quantity=quantity,
        transaction_type=TransactionType.OUT,
        tenant_id=tenant_id,
        reference_id=None,
        reason=f"MERMA: {reason.value}",
        user_id=user_id,
        auto_commit=False
    )
    try:
        waste = ProductWaste(
            tenant_id=tenant_id,
            product_id=product_id,
            quantity=Decimal(str(quantity)),
            reason=reason,
            notes=notes,
            recorded_by=user_id
        )
        db.add(waste)
        await db.commit()
        await db.refresh(waste)
        return waste
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error registrando merma")


async def get_waste_list(
    db: AsyncSession,
    tenant_id: UUID,
    period: str = "today",
    skip: int = 0,
    limit: int = 50
) -> tuple[List[ProductWaste], int]:
    """Lista registros de merma con filtro por período (today/week/month/all)."""
    conditions = [ProductWaste.tenant_id == tenant_id]

    if period != "all":
        now = datetime.now(ARG)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "today":
            start = today_start
        elif period == "week":
            start = today_start - timedelta(days=today_start.weekday())
        elif period == "month":
            start = today_start.replace(day=1)
        else:
            start = today_start
        conditions.append(ProductWaste.created_at >= start)

    total_result = await db.execute(
        select(func.count(ProductWaste.id)).where(*conditions)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(ProductWaste)
        .options(joinedload(ProductWaste.product), joinedload(ProductWaste.user))
        .where(*conditions)
        .order_by(ProductWaste.created_at.desc())
        .offset(skip).limit(limit)
    )
    wastes = result.scalars().unique().all()
    return wastes, int(total)