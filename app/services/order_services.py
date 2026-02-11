from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.models.enums import PurchaseOrderStatus, PurchaseRequestStatus, TransactionType
from app.models.orders import PurchaseOrder, PurchaseOrderItem
from app.models.requests import PurchaseRequest, PurchaseRequestItem, Product
from app.services.inventory_services import register_transaction
from app.schemas.orders import OrderUpdate

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
        for order in created_orders:
            await db.refresh(order)
        return created_orders

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando órdenes: {str(e)}")

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
            quantity = float(received.get('quantity', 0))
            
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
                reference_id=order.id
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
        return order

    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error recibiendo orden: {str(e)}")

async def get_orders(
    db: AsyncSession, 
    tenant_id: UUID, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[PurchaseOrderStatus] = None
) -> List[PurchaseOrder]:
    query = select(PurchaseOrder).where(PurchaseOrder.tenant_id == tenant_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
    
    query = query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
    query = query.options(joinedload(PurchaseOrder.supplier))
    result = await db.execute(query)
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
    return order

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