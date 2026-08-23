from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from sqlalchemy.orm import joinedload

from app.api.deps import get_db, get_current_user
from app.models.enums import Roles
from app.models.user import Users
from app.models.inventory import InventoryTransaction
from app.schemas.inventory import (
    InventoryTransactionSchema,
    InventoryTransactionCreate,
    InventoryTransactionAdjustment,
    ProductWasteCreate,
    ProductWasteSchema,
    PaginatedProductWasteResponse
)
from app.services import inventory_services

router = APIRouter()


@router.post("/transaction", response_model=InventoryTransactionSchema)
async def create_manual_transaction(
    transaction: InventoryTransactionCreate,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para realizar ajustes de inventario."
        )

    return await inventory_services.register_transaction(
        db=db,
        product_id=transaction.product_id,
        quantity=transaction.quantity,
        transaction_type=transaction.transaction_type,
        tenant_id=current_user.tenant_id,
        reference_id=transaction.reference_id,
        user_id=current_user.id
    )


@router.get("/history/{product_id}", response_model=List[InventoryTransactionSchema])
async def read_product_history(
    product_id: UUID,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para ver el historial de inventario."
        )

    return await inventory_services.get_product_history(
        db=db,
        product_id=product_id,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )


@router.post("/adjust", response_model=InventoryTransactionSchema)
async def create_adjustment(
    adjustment: InventoryTransactionAdjustment,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    return await inventory_services.register_transaction(
        db=db,
        product_id=adjustment.product_id,
        quantity=adjustment.quantity,
        transaction_type=adjustment.transaction_type,
        tenant_id=current_user.tenant_id,
        reference_id=None,
        reason=adjustment.reason,
        user_id=current_user.id
    )


class PaginatedInventoryResponse(BaseModel):
    items: List[InventoryTransactionSchema]
    total: int
    skip: int
    limit: int


@router.get("/transactions")
async def list_transactions(
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    result = await db.execute(
        select(InventoryTransaction)
        .options(joinedload(InventoryTransaction.user))
        .where(InventoryTransaction.tenant_id == current_user.tenant_id)
        .order_by(InventoryTransaction.created_at.desc())
        .offset(skip).limit(limit)
    )
    transactions = result.scalars().unique().all()

    for t in transactions:
        if t.user:
            t.user_name = t.user.username
            t.user_full_name = t.user.full_name

    count_result = await db.execute(
        select(func.count())
        .select_from(InventoryTransaction)
        .where(InventoryTransaction.tenant_id == current_user.tenant_id)
    )
    total = count_result.scalar() or 0

    return PaginatedInventoryResponse(
        items=[InventoryTransactionSchema.model_validate(t) for t in transactions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/waste", response_model=ProductWasteSchema)
async def register_product_waste(
    waste: ProductWasteCreate,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Registra merma de un producto: descuenta stock y guarda el motivo."""
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="No tienes permisos")

    return await inventory_services.register_waste(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=waste.product_id,
        quantity=waste.quantity,
        reason=waste.reason,
        notes=waste.notes,
        user_id=current_user.id
    )


@router.get("/waste", response_model=PaginatedProductWasteResponse)
async def list_product_waste(
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    period: str = Query(default="today", pattern="^(today|week|month|all)$"),
    skip: int = 0,
    limit: int = 50
):
    """Lista registros de merma. period=today|week|month|all."""
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="No tienes permisos")

    wastes, total = await inventory_services.get_waste_list(
        db=db,
        tenant_id=current_user.tenant_id,
        period=period,
        skip=skip,
        limit=limit
    )

    items = []
    for w in wastes:
        schema = ProductWasteSchema.model_validate(w)
        if w.product:
            schema.product_name = w.product.name
        if w.user:
            schema.recorded_by_name = w.user.full_name or w.user.username
        items.append(schema)

    return PaginatedProductWasteResponse(items=items, total=total, skip=skip, limit=limit)