from uuid import UUID
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.products import Product
from app.models.alerts import StockAlert
from app.models.notifications import Notification
from app.models.enums import ProductType, NotificationType, NotificationStatus, Roles
from app.schemas.alerts import StockAlertCreate, StockAlertUpdate

ARG = ZoneInfo("America/Argentina/Buenos_Aires")


async def get_products_with_low_stock(
    db: AsyncSession,
    tenant_id: UUID,
    product_type: Optional[ProductType] = None
) -> List[Product]:
    query = select(Product).where(Product.tenant_id == tenant_id)
    
    if product_type:
        query = query.where(Product.product_type == product_type)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    low_stock_products = []
    for product in products:
        if product.enable_alert and product.min_stock_alert is not None:
            if product.stock_quantity <= product.min_stock_alert:
                low_stock_products.append(product)
    
    return low_stock_products


async def get_products_without_stock(
    db: AsyncSession,
    tenant_id: UUID,
    product_type: Optional[ProductType] = None
) -> List[Product]:
    query = select(Product).where(
        Product.tenant_id == tenant_id,
        Product.stock_quantity == 0
    )
    
    if product_type:
        query = query.where(Product.product_type == product_type)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_alerts(
    db: AsyncSession,
    tenant_id: UUID,
    product_type: Optional[ProductType] = None
) -> dict:
    raw_materials = await get_products_with_low_stock(
        db, tenant_id, ProductType.RAW_MATERIAL
    )
    raw_materials_no_stock = await get_products_without_stock(
        db, tenant_id, ProductType.RAW_MATERIAL
    )
    
    elaborated_products = await get_products_with_low_stock(
        db, tenant_id, ProductType.PRODUCT_ELABORATED
    )
    elaborated_no_stock = await get_products_without_stock(
        db, tenant_id, ProductType.PRODUCT_ELABORATED
    )
    
    purchased_products = await get_products_with_low_stock(
        db, tenant_id, ProductType.PRODUCT_PURCHASED
    )
    purchased_no_stock = await get_products_without_stock(
        db, tenant_id, ProductType.PRODUCT_PURCHASED
    )
    
    all_mp = list(set(raw_materials + purchased_products))
    all_mp_no_stock = list(set(raw_materials_no_stock + purchased_no_stock))
    
    return {
        "raw_materials": {
            "low_stock": [p.name for p in all_mp if p.stock_quantity > 0],
            "no_stock": [p.name for p in all_mp_no_stock],
            "all_ok": len(all_mp) == 0 and len(all_mp_no_stock) == 0
        },
        "elaborated_products": {
            "low_stock": [p.name for p in elaborated_products if p.stock_quantity > 0],
            "no_stock": [p.name for p in elaborated_no_stock],
            "all_ok": len(elaborated_products) == 0 and len(elaborated_no_stock) == 0
        }
    }


async def configure_product_alert(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID,
    config: StockAlertUpdate
) -> Product:
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalars().first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if config.min_stock_alert is not None:
        product.min_stock_alert = Decimal(str(config.min_stock_alert))
    
    if config.enable_alert is not None:
        product.enable_alert = config.enable_alert
    
    await db.commit()
    await db.refresh(product)
    
    return product


async def send_production_request(
    db: AsyncSession,
    tenant_id: UUID,
    product_id: UUID,
    quantity: float,
    recipient_ids: List[UUID],
    requester_name: str = "Company"
) -> List[Notification]:
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalars().first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if product.product_type != ProductType.PRODUCT_ELABORATED:
        raise HTTPException(
            status_code=400, 
            detail="Solo se pueden solicitar productos elaborados"
        )
    
    notifications = []
    
    for user_id in recipient_ids:
        notification = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            type=NotificationType.PRODUCTION_REQUEST,
            status=NotificationStatus.PENDING,
            created_at=datetime.now(ARG)
        )
        db.add(notification)
        notifications.append(notification)
    
    await db.commit()
    
    for notif in notifications:
        await db.refresh(notif)
    
    return notifications


async def get_production_requests(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Notification]:
    query = select(Notification).where(
        Notification.tenant_id == tenant_id,
        Notification.user_id == user_id,
        Notification.type == NotificationType.PRODUCTION_REQUEST
    ).order_by(Notification.created_at.desc())
    
    result = await db.execute(
        select(Notification)
        .where(
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
            Notification.type == NotificationType.PRODUCTION_REQUEST
        )
        .offset(skip)
        .limit(limit)
    )
    
    return result.scalars().all()


async def respond_production_request(
    db: AsyncSession,
    notification_id: UUID,
    tenant_id: UUID,
    user_id: UUID,
    status: str,
    cancel_reason: Optional[str] = None,
    user_name: str = "Employee"
) -> Notification:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.tenant_id == tenant_id,
            Notification.type == NotificationType.PRODUCTION_REQUEST
        )
    )
    notification = result.scalars().first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    notification.status = NotificationStatus.RESOLVED
    
    user_result = await db.execute(
        select(Users).where(Users.id == user_id)
    )
    user = user_result.scalars().first()
    user_name = user.name or user.username if user else "Employee"
    
    from app.models.user import Users
    company_result = await db.execute(
        select(Users).where(
            Users.tenant_id == tenant_id,
            Users.role == Roles.COMPANY
        )
    )
    company_user = company_result.scalars().first()
    
    new_type = NotificationType.PRODUCTION_COMPLETED if status == "COMPLETED" else NotificationType.PRODUCTION_CANCELLED
    
    response_notification = Notification(
        tenant_id=tenant_id,
        user_id=company_user.id if company_user else None,
        type=new_type,
        status=NotificationStatus.PENDING,
        notes=f"Solicitud {status} por {user_name}" + (f": {cancel_reason}" if cancel_reason and status == "CANCELLED" else "")
    )
    db.add(response_notification)
    await db.commit()
    await db.refresh(response_notification)
    
    return response_notification


async def check_and_notify_low_stock(
    db: AsyncSession,
    tenant_id: UUID,
    product_id: UUID
) -> Optional[Notification]:
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalars().first()
    
    if not product:
        return None
    
    if product.enable_alert and product.min_stock_alert is not None:
        if product.stock_quantity <= product.min_stock_alert:
            from app.models.user import Users
            company_result = await db.execute(
                select(Users).where(
                    Users.tenant_id == tenant_id,
                    Users.role == Roles.COMPANY
                )
            )
            company_user = company_result.scalars().first()
            
            if company_user:
                notification = Notification(
                    tenant_id=tenant_id,
                    user_id=company_user.id,
                    type=NotificationType.STOCK_LOW_ALERT,
                    status=NotificationStatus.PENDING,
                    created_at=datetime.now(ARG)
                )
                db.add(notification)
                await db.commit()
                await db.refresh(notification)
                return notification
    
    return None


async def get_alert_count(
    db: AsyncSession,
    tenant_id: UUID
) -> int:
    result = await db.execute(
        select(Product).where(Product.tenant_id == tenant_id)
    )
    products = result.scalars().all()
    
    count = 0
    for product in products:
        if product.enable_alert and product.min_stock_alert is not None:
            if product.stock_quantity <= product.min_stock_alert:
                count += 1
    
    return count


async def notify_sale_cancelled(
    db: AsyncSession,
    tenant_id: UUID,
    order_id: UUID,
    order_data: dict,
    cancelled_by_user_id: UUID,
    cancelled_by_name: str
) -> Optional[Notification]:
    from app.models.user import Users
    
    company_result = await db.execute(
        select(Users).where(
            Users.tenant_id == tenant_id,
            Users.role == Roles.COMPANY
        )
    )
    company_user = company_result.scalars().first()
    
    if not company_user:
        return None
    
    notes = (
        f"Venta #{str(order_id)[:8]} "
        f"cliente: {order_data.get('customer_name', 'N/A')}, "
        f"total: ${order_data.get('total_amount', 0):.2f}, "
        f"canal: {order_data.get('channel_name', 'N/A')}, "
        f"cancelado por: {cancelled_by_name}"
    )
    
    notification = Notification(
        tenant_id=tenant_id,
        user_id=company_user.id,
        type=NotificationType.SALE_CANCELLED,
        status=NotificationStatus.PENDING,
        notes=notes,
        created_at=datetime.now(ARG)
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def notify_sale_rejected(
    db: AsyncSession,
    tenant_id: UUID,
    order_id: UUID,
    order_data: dict,
    rejected_by_user_id: UUID,
    rejected_by_name: str
) -> Optional[Notification]:
    from app.models.user import Users
    
    company_result = await db.execute(
        select(Users).where(
            Users.tenant_id == tenant_id,
            Users.role == Roles.COMPANY
        )
    )
    company_user = company_result.scalars().first()
    
    if not company_user:
        return None
    
    notes = (
        f"Venta #{str(order_id)[:8]} "
        f"cliente: {order_data.get('customer_name', 'N/A')}, "
        f"total: ${order_data.get('total_amount', 0):.2f}, "
        f"canal: {order_data.get('channel_name', 'N/A')}, "
        f"rechazado por: {rejected_by_name}"
    )
    
    notification = Notification(
        tenant_id=tenant_id,
        user_id=company_user.id,
        type=NotificationType.SALE_REJECTED,
        status=NotificationStatus.PENDING,
        notes=notes,
        created_at=datetime.now(ARG)
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification