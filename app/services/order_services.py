from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
from uuid import UUID
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.models.enums import (
    PurchaseOrderStatus, PurchaseRequestStatus, TransactionType,
    NotificationType, NotificationStatus, Roles
)
from app.models.orders import PurchaseOrder, PurchaseOrderItem
from app.models.requests import PurchaseRequest, PurchaseRequestItem
from app.models.products import Product
from app.models.notifications import Notification
from app.services.inventory_services import register_transaction
from app.schemas.orders import OrderUpdate
from app.utils.pagination import paginate

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

PURCHASE_ORDER_STATUS_DISPLAY = {
    "DRAFT": "En Proceso",
    "SENT": "Enviada",
    "RECEIVED": "Recibida",
    "PARTIALLY_RECEIVED": "Parcialmente Recibida",
    "CANCELLED": "Cancelada"
}


async def create_orders_from_requests(
    db: AsyncSession, 
    tenant_id: UUID, 
    request_ids: List[UUID]
) -> List[PurchaseOrder]:
    # 1. Traer todas las requests validas de una sola vez (Usamos joinedload para traer items y productos para evitar N+1)
    result = await db.execute(
        select(PurchaseRequest)
        .options(
            joinedload(PurchaseRequest.items)
            .joinedload(PurchaseRequestItem.product)
        )
        .where(
            PurchaseRequest.id.in_(request_ids),
            PurchaseRequest.tenant_id == tenant_id
        )
    )
    requests = result.scalars().unique().all()
    # 2. Validaciones
    if len(requests) != len(request_ids):
        found_ids = {r.id for r in requests}
        missing_ids = set(request_ids) - found_ids
        raise HTTPException(status_code=404, detail=f"No se encontraron las solicitudes: {missing_ids}")
    for req in requests:
        if req.status != PurchaseRequestStatus.APPROVED:
            raise HTTPException(status_code=400, detail=f"La solicitud {req.id} no está aprobada (Estado: {req.status})")
    
    # 3. Agrupación por Proveedor (Estructura: { supplier_id: { product_id: { 'quantity': total_qty } } })
    items_by_supplier: Dict[UUID, Dict[UUID, float]] = {}
    for req in requests:
        for item in req.items:
            product = item.product
            if not product.supplier_id:
                raise HTTPException(status_code=400, detail=f"El producto {product.name} no tiene proveedor asignado")
            
            supplier_id = product.supplier_id
            
            if supplier_id not in items_by_supplier:
                items_by_supplier[supplier_id] = {}
            
            if product.id not in items_by_supplier[supplier_id]:
                items_by_supplier[supplier_id][product.id] = 0
            
            items_by_supplier[supplier_id][product.id] += float(item.quantity)
    
    # 4. Creación de Órdenes
    created_orders = []
    try:
        for supplier_id, products_dict in items_by_supplier.items():
            new_order = PurchaseOrder(
                tenant_id=tenant_id,
                supplier_id=supplier_id,
                status=PurchaseOrderStatus.DRAFT,
                notes=f"Generada automáticamente desde {len(request_ids)} solicitudes" 
            )
            db.add(new_order)
            await db.flush() # Para tener el ID de la orden

            # Crear Items de Orden
            for product_id, quantity in products_dict.items():
                # Buscamos el producto en la sesión para sacar el precio de costo actual
                product = await db.get(Product, product_id) 
                
                order_item = PurchaseOrderItem(
                    order_id=new_order.id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=product.cost_price, # Usamos el costo actual como precio de compra inicial
                    received_quantity=0
                )
                db.add(order_item)
            
            created_orders.append(new_order)

        # 5. Commit de toda la operación
        await db.commit()

        # 6. Recargar órdenes con relaciones para serialización
        order_ids = [o.id for o in created_orders]
        result = await db.execute(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product)
            )
            .where(PurchaseOrder.id.in_(order_ids))
        )
        return result.scalars().unique().all()

    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

async def create_order_direct(
    db: AsyncSession,
    tenant_id: UUID,
    supplier_id: UUID,
    items: List[Dict],
    expected_delivery_date: Optional[date] = None,
    notes: Optional[str] = None
) -> PurchaseOrder:
    from app.models.suppliers import Supplier
    
    supplier = await db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if supplier.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este proveedor")

    try:
        new_order = PurchaseOrder(
            tenant_id=tenant_id,
            supplier_id=supplier_id,
            status=PurchaseOrderStatus.SENT,
            expected_delivery_date=expected_delivery_date,
            notes=notes
        )
        db.add(new_order)
        await db.flush()

        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")
            
            if not product_id or not quantity:
                raise HTTPException(status_code=400, detail="Cada item debe tener product_id y quantity")

            product = await db.get(Product, product_id)
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto {product_id} no encontrado")
            if product.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail=f"No tienes acceso al producto {product_id}")

            order_item = PurchaseOrderItem(
                order_id=new_order.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product.cost_price,
                received_quantity=0
            )
            db.add(order_item)

        await db.commit()
        await db.refresh(new_order)
        
        # Load relationships for response
        from sqlalchemy.orm import joinedload
        result = await db.execute(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product)
            )
            .where(PurchaseOrder.id == new_order.id)
        )
        return result.scalars().unique().first()

    except SQLAlchemyError:
        await db.rollback()
        raise
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def receive_order(
    db: AsyncSession,
    tenant_id: UUID,
    order_id: UUID,
    received_items: List[Dict[str, any]]
) -> PurchaseOrder:
    # 1. Obtener orden con items
    result = await db.execute(
        select(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == tenant_id
        )
    )
    order = result.scalars().unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    if order.status == PurchaseOrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="No se puede recibir una orden cancelada")

    # 2. Procesar items recibidos
    # Mapa rápido para buscar items por producto
    order_items_map = {item.product_id: item for item in order.items}
    try:
        for received in received_items:
            product_id = received.get('product_id')
            quantity = Decimal(str(received.get('quantity', 0)))
            
            if quantity <= 0:
                continue

            if product_id not in order_items_map:
                raise HTTPException(status_code=400, detail=f"El producto {product_id} no pertenece a esta orden")
            
            item = order_items_map[product_id]
            # Actualizar cantidad recibida en la orden
            item.received_quantity += quantity
            
            # 3. IMPACTO EN INVENTARIO (CRÍTICO)
            await register_transaction(
                db=db,
                product_id=product_id,
                quantity=quantity,
                transaction_type=TransactionType.IN,
                tenant_id=tenant_id,
                reference_id=order.id,
                auto_commit=False
            )

        # 4. Actualizar Estado de la Orden
        all_received = True
        any_received = False
        
        for item in order.items:
            if item.received_quantity > 0:
                any_received = True
            if item.received_quantity < item.quantity:
                all_received = False
        
        if all_received:
            order.status = PurchaseOrderStatus.RECEIVED
        elif any_received:
            order.status = PurchaseOrderStatus.PARTIALLY_RECEIVED
        
        # Guardar cambios
        await db.commit()
        await db.refresh(order)
        
        # Load relationships for response
        result = await db.execute(
            select(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product)
            )
            .where(PurchaseOrder.id == order.id)
        )
        return result.scalars().unique().first()

    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

async def get_orders(
    db: AsyncSession, 
    tenant_id: UUID, 
    skip: int = 0, 
    limit: int = 10,
    status: Optional[PurchaseOrderStatus] = None
) -> List[PurchaseOrder]:
    query = select(PurchaseOrder).where(PurchaseOrder.tenant_id == tenant_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
    
    query = query.order_by(PurchaseOrder.created_at.desc())
    query = query.options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product)
    )
    result = await db.execute(paginate(query, skip, limit))
    return result.scalars().unique().all()


async def get_orders_by_id(
    db: AsyncSession, 
    order_id: UUID, 
    tenant_id: UUID
) -> Optional[PurchaseOrder]:
    query = select(PurchaseOrder).where(
        PurchaseOrder.id == order_id,
        PurchaseOrder.tenant_id == tenant_id
    ).options(
        joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
        joinedload(PurchaseOrder.supplier)
    )
    result = await db.execute(query)
    return result.scalars().unique().first()


async def update_order(
    db: AsyncSession,
    tenant_id: UUID,
    order_id: UUID,
    order_update: OrderUpdate
) -> PurchaseOrder:
    order = await get_orders_by_id(db, order_id, tenant_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    update_data = order_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(order, key, value)

    await db.commit()
    await db.refresh(order)
    
    # Load relationships for response
    from sqlalchemy.orm import joinedload
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product)
        )
        .where(PurchaseOrder.id == order.id)
    )
    return result.scalars().unique().first()

async def delete_order(
    db: AsyncSession,
    tenant_id: UUID,
    order_id: UUID
) -> bool:
     order = await get_orders_by_id(db, order_id, tenant_id)
     if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
     
     if order.status not in [PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SENT]:
         raise HTTPException(status_code=400, detail="Solo se pueden eliminar órdenes en borrador o enviadas")
     
     await db.delete(order)
     await db.commit()
     return True


async def _notify_orders_due_today(db: AsyncSession, tenant_id: UUID, orders: List[PurchaseOrder]) -> int:
    """
    Notifica a COMPANY y EMPLOYEEs las órdenes cuya fecha de entrega es HOY.
    Idempotente por día: usa el marcador [ORDER:{id}] en notes para no duplicar.
    Patrón 'lazy cron': se dispara cuando alguien consulta /orders/tracking.
    """
    now = datetime.now(ARG)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today = now.date()

    users_result = await db.execute(
        select(Users.id).where(
            Users.tenant_id == tenant_id,
            Users.role.in_([Roles.COMPANY, Roles.EMPLOYEE]),
            Users.is_active == True
        )
    )
    user_ids = users_result.scalars().all()
    if not user_ids:
        return 0

    sent_count = 0
    for order in orders:
        if order.expected_delivery_date != today:
            continue

        marker = f"[ORDER:{order.id}]"
        existing = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.tenant_id == tenant_id,
                Notification.type == NotificationType.ORDER_DELIVERY_TODAY,
                Notification.created_at >= today_start,
                Notification.notes.contains(marker)
            )
        )
        if (existing.scalar() or 0) > 0:
            continue

        supplier_name = order.supplier.name if order.supplier else "Proveedor"
        products_summary = ", ".join(
            f"{item.product.name} x{item.quantity}" if item.product else f"Producto {item.product_id} x{item.quantity}"
            for item in order.items
        )
        notes = (
            f"[ORDER:{order.id}] Entrega prevista HOY de orden de compra "
            f"a {supplier_name}: {products_summary}"
        )

        for user_id in user_ids:
            db.add(Notification(
                tenant_id=tenant_id,
                user_id=user_id,
                type=NotificationType.ORDER_DELIVERY_TODAY,
                status=NotificationStatus.PENDING,
                notes=notes,
                created_at=datetime.now(ARG)
            ))
        sent_count += 1

    if sent_count:
        await db.commit()
    return sent_count


async def get_tracking_orders(db: AsyncSession, tenant_id: UUID) -> List[dict]:
    """
    Órdenes de compra en seguimiento (DRAFT/SENT/PARTIALLY_RECEIVED con fecha de entrega).
    Ordenadas por expected_delivery_date ascendente (más próximas primero).
    Dispara notificaciones del día para las que entregan hoy.
    """
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product)
        )
        .where(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.status.in_([
                PurchaseOrderStatus.DRAFT,
                PurchaseOrderStatus.SENT,
                PurchaseOrderStatus.PARTIALLY_RECEIVED
            ]),
            PurchaseOrder.expected_delivery_date.isnot(None)
        )
        .order_by(PurchaseOrder.expected_delivery_date.asc())
    )
    orders = result.scalars().unique().all()

    try:
        await _notify_orders_due_today(db, tenant_id, orders)
    except SQLAlchemyError:
        # La notificación no debe romper la consulta de tracking
        await db.rollback()

    today = datetime.now(ARG).date()

    tracking = []
    for order in orders:
        days_until = (order.expected_delivery_date - today).days
        total_items = len(order.items)
        received_items = sum(1 for i in order.items if i.received_quantity >= i.quantity and i.quantity > 0)

        tracking.append({
            "id": order.id,
            "supplier_name": order.supplier.name if order.supplier else "Proveedor",
            "status": order.status.value,
            "status_display": PURCHASE_ORDER_STATUS_DISPLAY.get(order.status.value, order.status.value),
            "expected_delivery_date": order.expected_delivery_date,
            "days_until_delivery": days_until,
            "is_due_today": days_until == 0,
            "overdue_days": max(-days_until, 0),
            "total_items": total_items,
            "received_items": received_items,
            "fully_received": total_items > 0 and received_items == total_items,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else None,
                    "quantity": float(item.quantity),
                    "received_quantity": float(item.received_quantity),
                    "unit_price": float(item.unit_price)
                }
                for item in order.items
            ],
            "created_at": order.created_at
        })
    return tracking