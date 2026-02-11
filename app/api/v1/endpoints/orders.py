from datetime import date
from typing import List, Optional, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user,get_db
from app.models.enums import Roles, PurchaseOrderStatus
from app.models.user import Users
from app.schemas.orders import OrderSchema, OrderUpdate, OrderItemSchema
from app.services import order_services

router = APIRouter()

@router.post("/generate", response_model=List[OrderSchema])
async def generate_orders(
    request_ids: List[UUID] = Body(...),
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para generar órdenes."
        )

    return await order_services.create_orders_from_requests(
        db=db, tenant_id=current_user.tenant_id, request_ids=request_ids
    )


@router.get("/", response_model=List[OrderSchema])
async def read_orders(
    status: Optional[PurchaseOrderStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para ver órdenes."
        )

    return await order_services.get_orders(
        db=db,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit,
        status=status,
    )


@router.get("/{order_id}", response_model=OrderSchema)
async def read_order(
    order_id: UUID,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para ver esta orden."
        )

    order = await order_services.get_orders_by_id(
        db=db, order_id=order_id, tenant_id=current_user.tenant_id
    )
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


@router.patch("/{order_id}/receive", response_model=OrderSchema)
async def receive_order_items(
    order_id: UUID,
    items: List[Dict[str, float]] = Body(..., description="List of dictionaries with 'product_id' (UUID) and 'quantity' (float)"),
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive items for a purchase order.
    Updates the received quantity and adjusts inventory stock (IN).
    Only for COMPANY role (or authorized employees).
    Expects a list of dicts: [{"product_id": "...", "quantity": 10}, ...]
    """
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]: 
         # Assuming only company admins or specific roles can receive stock for now
        raise HTTPException(
            status_code=403, detail="No tienes permisos para recibir órdenes."
        )

    # Validate input structure briefly
    validated_items = []
    for item in items:
        if "product_id" not in item or "quantity" not in item:
             raise HTTPException(status_code=400, detail="Cada item debe tener 'product_id' y 'quantity'")
        try:
             # Ensure product_id is a valid UUID string if passed as string
             p_uuid = UUID(str(item["product_id"]))
             validated_items.append({"product_id": p_uuid, "quantity": float(item["quantity"])})
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid UUID for product_id")

    return await order_services.receive_order(
        db=db,
        tenant_id=current_user.tenant_id,
        order_id=order_id,
        received_items=validated_items
    )


@router.patch("/{order_id}", response_model=OrderSchema)
async def update_order(
    order_id: UUID,
    order_in: OrderUpdate,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para editar órdenes."
        )

    return await order_services.update_order(
        db=db,
        tenant_id=current_user.tenant_id,
        order_id=order_id,
        order_update=order_in
    )


@router.delete("/{order_id}", response_model=bool)
async def delete_order(
    order_id: UUID,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403, detail="No tienes permisos para eliminar órdenes."
        )

    return await order_services.delete_order(
        db=db,
        tenant_id=current_user.tenant_id,
        order_id=order_id
    )
