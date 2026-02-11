from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.inventory import InventoryTransaction
from app.models.products import Product
from app.schemas.inventory import InventoryTransactionCreate, InventoryTransactionSchema
from app.models.enums import TransactionType

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
ARG = ZoneInfo("America/Argentina/Buenos_Aires")

async def register_transaction(
    db: AsyncSession, 
    product_id: UUID, 
    quantity: int, 
    transaction_type: TransactionType, 
    tenant_id: UUID, 
    reference_id: Optional[UUID]
):
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
    if quantity <=0:
        raise HTTPException(status_code=404, detail="Se debe agregar una cantidad superior a 0")
    if transaction_type == TransactionType.IN:
        product.stock_quantity += quantity
    if transaction_type == TransactionType.OUT:
        if product.stock_quantity < quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente")
        product.stock_quantity -= quantity
    new_transaction = InventoryTransaction(
        tenant_id = tenant_id,
        product_id = product_id,
        transaction_type = transaction_type,
        quantity = quantity,
        reference_id = reference_id
    )
    await db.add(new_transaction)
    await db.add(product)
    await db.commit()
    await db.refresh(new_transaction)
    return new_transaction

async def get_product_history(db: AsyncSession, product_id: UUID, tenant_id:UUID):
    product_history = await db.execute(select(InventoryTransaction).where(
        InventoryTransaction.product_id == product_id,
        InventoryTransaction.tenant_id == tenant_id
    ).order_by(InventoryTransaction.created_at.desc()))
    return product_history.scalars().all()