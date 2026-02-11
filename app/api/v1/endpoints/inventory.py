from typing import List, Optional, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.enums import Roles
from app.models.user import Users
from app.schemas.inventory import InventoryTransactionSchema, InventoryTransactionCreate
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
        reference_id=transaction.reference_id
    )

@router.get("/history/{product_id}", response_model=List[InventoryTransactionSchema])
async def read_product_history(
    product_id: UUID,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para ver el historial de inventario."
        )

    return await inventory_services.get_product_history(
        db=db,
        product_id=product_id,
        tenant_id=current_user.tenant_id
    )