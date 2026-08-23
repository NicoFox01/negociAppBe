from fastapi import APIRouter, Body, Depends, HTTPException
from app.models.enums import Roles, OrderStatus
from uuid import UUID
from datetime import date
from typing import Annotated, TYPE_CHECKING, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.schemas.orders import (SalesChannelSchema, SalesChannelCreate, SalesChannelUpdate,
                                ProductChannelPriceSchema, ProductChannelPriceCreate,
                                PromotionSchema, PromotionCreate, PromotionUpdate,
                                ClientOrderSchema, ClientOrderCreate, ClientOrderUpdate)
from app.services.sales_service import *
from app.services.alerts_service import check_and_notify_low_stock
from pydantic import BaseModel

from typing import Annotated, TYPE_CHECKING, List

if TYPE_CHECKING:
    from app.models.user import Users
from app.models.enums import Roles
router = APIRouter()

class PaginatedOrdersResponse(BaseModel):
    items: List[ClientOrderSchema]
    total: int
    skip: int
    limit: int

#endpoints Sales Channel (Solo COMPANY)
@router.post("/channels", response_model=SalesChannelSchema)
async def new_channel(
    current_user: Annotated["Users", Depends(get_current_user)],
    channel_data: SalesChannelCreate,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await create_sales_channel(db, tenant_id, channel_data)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/channels", response_model=List[SalesChannelSchema])
async def return_channels(
        current_user: Annotated["Users", Depends(get_current_user)],
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 10
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        return await get_sales_channels(db, tenant_id, skip, limit)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.get("/channels/{channel_id}", response_model=SalesChannelSchema)
async def return_channel(
        channel_id: UUID,
        current_user: Annotated["Users", Depends(get_current_user)],
        db: AsyncSession = Depends(get_db)
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        return await get_sales_channel_by_id(db, channel_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.patch("/channels/{channel_id}", response_model=SalesChannelSchema)
async def modify_channel(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: UUID,
        channel_data: SalesChannelUpdate,
        db: AsyncSession = Depends(get_db)
):
    print(f"DEBUG PATCH: channel_id={channel_id}, data={channel_data}")
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        result = await update_sales_channel(db, channel_id, tenant_id, channel_data)
        print(f"DEBUG PATCH: result={result}")
        return result
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.delete("/channels/{channel_id}", response_model=None)
async def remove_channel(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await delete_sales_channel(db, channel_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

#endpoints Sales Channel Price (Solo COMPANY)
@router.post("/channels/{channel_id}/prices/{product_id}", response_model=ProductChannelPriceSchema)
async def new_product_sales_channel_price(
        current_user: Annotated["Users", Depends(get_current_user)],
        product_id: UUID,
        channel_id: UUID,
        price: float = Body(..., embed=True),
        db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await set_product_price(db, tenant_id, product_id, channel_id, price)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/channels/{channel_id}/prices", response_model=List[ProductChannelPriceSchema])
async def return_product_sales_channel_prices(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: UUID,
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 10
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        return await get_all_product_prices(db, channel_id, tenant_id, skip, limit)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/channels/{channel_id}/prices/{product_id}", response_model=ProductChannelPriceSchema)
async def return_product_sales_channel_price(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: UUID,
        product_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        return await get_product_price_by_id(db, product_id, channel_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.delete("/channels/{channel_id}/prices/{product_id}", response_model=None)
async def remove_product_sales_channel_price(
        current_user: Annotated["Users", Depends(get_current_user)],
        product_id: UUID,
        channel_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await delete_product_price(db, product_id, channel_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

#endpoints promotion (Solo COMPANY)
@router.post("/channels/{channel_id}/promotions", response_model=PromotionSchema)
async def new_promotion(
    current_user: Annotated["Users", Depends(get_current_user)],
    tenant_id: UUID, 
    promotion_data: PromotionCreate,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await create_promotion(db, tenant_id, promotion_data)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/channels/{channel_id}/promotions", response_model=List[PromotionSchema])
async def return_promotions(
    current_user: Annotated["Users", Depends(get_current_user)],
    channel_id: UUID,
    product_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    if current_user.role == Roles.COMPANY:
        return await get_active_promotion(db, channel_id, tenant_id, product_id, skip, limit)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/channels/{channel_id}/promotions/active",response_model=list[PromotionSchema])
async def return_active_promotions(
    current_user: Annotated["Users", Depends(get_current_user)],
    channel_id: UUID,
    product_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await get_active_promotion(db, channel_id, tenant_id, product_id, skip, limit)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )
@router.get("/channels/{channel_id}/promotions/{promotion_id}", response_model=PromotionSchema)
async def return_promotion_by_id(
    current_user: Annotated["Users", Depends(get_current_user)],
    channel_id: UUID,
    promotion_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        promotion = await get_promotion_by_id(
            db=db,
            promotion_id=promotion_id,
            channel_id=channel_id,
            tenant_id=current_user.tenant_id
        )

        if not promotion:
            raise HTTPException(
                status_code=404,
                detail="Promoción no encontrada"
            )

        return promotion
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.patch("/channels/{channel_id}/promotions/{promotion_id}", response_model=PromotionSchema)
async def modify_promotion(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: UUID,
        promotion_data: PromotionUpdate,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await update_promotion(db, promotion_id, tenant_id, promotion_data)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.delete("/channels/{channel_id}/promotions/{promotion_id}", response_model=None)
async def remove_promotion(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: UUID,
        promotion_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await delete_promotion(db, promotion_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

#endpoints ClientOrder (COMPANY & EMPLOYEE)
@router.post("/clientOrder", response_model=ClientOrderSchema)
async def new_client_order(
        current_user: Annotated["Users", Depends(get_current_user)],
        order_data:ClientOrderCreate,
        user_id: UUID | None = None,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        final_user_id = user_id if user_id else current_user.id
        order = await create_order(db, tenant_id, order_data, final_user_id)
        for item in order_data.items:
            await check_and_notify_low_stock(db, tenant_id, item.product_id)
        return order
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/clientOrder", response_model=PaginatedOrdersResponse)
async def return_client_orders(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: Optional[UUID] = None,
        status: Optional[OrderStatus] = None,
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        items, total = await get_orders(db, tenant_id, channel_id, status, skip, limit, start_date=start_date, end_date=end_date)
        return PaginatedOrdersResponse(items=items, total=total, skip=skip, limit=limit)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/clientOrder/cancelled", response_model=PaginatedOrdersResponse)
async def return_cancelled_orders(
        current_user: Annotated["Users", Depends(get_current_user)],
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        items, total = await get_cancelled_orders(db, tenant_id, skip, limit)
        return PaginatedOrdersResponse(items=items, total=total, skip=skip, limit=limit)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/clientOrder/{order_id}", response_model=ClientOrderSchema)
async def return_client_order_by_id(
        current_user: Annotated["Users", Depends(get_current_user)],
        order_id:UUID,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        return await get_order_by_id(db, order_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.get("/clientOrder/filter", response_model=PaginatedOrdersResponse)
async def return_client_order_by_channel_status(
        current_user: Annotated["Users", Depends(get_current_user)],
        channel_id: UUID,
        status: Optional[OrderStatus] = None,
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        items, total = await get_orders(db, tenant_id, channel_id, status, skip, limit, start_date=start_date, end_date=end_date)
        return PaginatedOrdersResponse(items=items, total=total, skip=skip, limit=limit)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

#Employee solo va a poder cancelar.
@router.patch("/clientOrder/{order_id}", response_model=ClientOrderSchema)
async def modify_client_order(
        current_user: Annotated["Users", Depends(get_current_user)],
        order_id:UUID,
        order_data: ClientOrderUpdate,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        user_id = current_user.id
        return await update_order(db, order_id, tenant_id, order_data, user_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

@router.delete("/clientOrder/{order_id}", response_model=None)
async def cancel_client_order(
        current_user: Annotated["Users", Depends(get_current_user)],
        order_id:UUID,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role in [Roles.COMPANY, Roles.EMPLOYEE]:
        tenant_id = current_user.tenant_id
        user_id = current_user.id
        return await cancel_order(db, order_id, tenant_id, user_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )