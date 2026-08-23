from datetime import datetime, timezone, time, date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from fastapi import HTTPException
from typing import List,  Optional
from decimal import Decimal
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
from app.models.products import Product

from app.models.orders import SalesChannel, ProductChannelPrice, Promotion, ClientOrder, ClientOrderItem
from app.schemas.orders import SalesChannelSchema, ClientOrderSchema, ClientOrderItemSchema, SalesChannelCreate, \
    ClientOrderCreate, ClientOrderItemCreate, SalesChannelUpdate, ClientOrderUpdate, ClientOrderItemUpdate, \
    PromotionCreate, PromotionUpdate, OrderCreate
from app.models.enums import DiscountType, OrderStatus, TransactionType
from app.services.product_services import get_product_by_id
from app.services.inventory_services import register_transaction
from app.utils.logger import log_debug, log_error
from app.utils.pagination import paginate


#Services de SalesChannel:
async def create_sales_channel(db: AsyncSession, tenant_id: UUID, channel_data: SalesChannelCreate) -> SalesChannel:
    try:
        new_sales_channel = SalesChannel(
            name=channel_data.name,
            commission_rate=channel_data.commission_rate,
            is_active=channel_data.is_active
        )
        new_sales_channel.tenant_id = tenant_id
        
        db.add(new_sales_channel)
        await db.commit()
        await db.refresh(new_sales_channel)
        return new_sales_channel
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_sales_channels(db: AsyncSession, tenant_id: UUID, skip: int=0, limit: int = 0) -> List[SalesChannel]:
    try:
        query = select(SalesChannel).where(SalesChannel.tenant_id == tenant_id)
        if limit > 0:
            query = query.offset(skip).limit(limit)
        else:
            query = query.offset(skip)
        list_of_sales_channels = await db.execute(query)
        return list_of_sales_channels.scalars().all()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
async def get_sales_channel_by_id(db:AsyncSession, channel_id:UUID, tenant_id:UUID, skip: int=0, limit: int = 0) -> SalesChannel:
    try:
        query = select(SalesChannel).where(SalesChannel.id == channel_id, SalesChannel.tenant_id == tenant_id)
        sales_channel = await db.execute(query)
        result = sales_channel.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Sales channel no encontrado")
        return result
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_sales_channel(db:AsyncSession, channel_id:UUID, tenant_id:UUID, channel_data: SalesChannelUpdate) -> SalesChannel:
    try:
        sales_channel_to_update = await db.execute(select(SalesChannel).where(SalesChannel.id == channel_id, SalesChannel.tenant_id == tenant_id))
        result = sales_channel_to_update.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Sales channel no encontrado")
        update_data = channel_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(result, field, value)
        db.add(result)
        await db.commit()
        await db.refresh(result)
        return result
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        log_error(f"Error actualizando canal de ventas {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def delete_sales_channel(db:AsyncSession, channel_id:UUID, tenant_id:UUID) -> None:
    try:
        sales_channel_to_delete = await get_sales_channel_by_id(db, channel_id, tenant_id)
        if not sales_channel_to_delete:
            raise HTTPException(status_code=404, detail="No existe el canal de ventas buscado")
        await db.delete(sales_channel_to_delete)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

#Services de ProductChannelPrice:
async def set_product_price(db:AsyncSession, tenant_id:UUID, product_id:UUID, channel_id:UUID, price:float) -> ProductChannelPrice:
    try:
        price_decimal = Decimal(str(price))
        product_price_to_set = await db.execute(select(ProductChannelPrice).where(
            ProductChannelPrice.product_id == product_id,
            ProductChannelPrice.channel_id == channel_id,
            ProductChannelPrice.tenant_id == tenant_id
        ))
        product_price = product_price_to_set.scalar_one_or_none()
        if product_price:
            product_price.price = price_decimal
        else:
            product_price = ProductChannelPrice(
                tenant_id=tenant_id,
                product_id=product_id,
                channel_id=channel_id,
                price=price_decimal,
            )
            db.add(product_price)
        await db.commit()
        await db.refresh(product_price)
        return product_price

    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_product_price_by_id(db:AsyncSession, product_id:UUID, channel_id:UUID, tenant_id:UUID) -> ProductChannelPrice:
    try:
        product_price = await db.execute(select(ProductChannelPrice).where(
            ProductChannelPrice.product_id == product_id,
            ProductChannelPrice.channel_id == channel_id,
            ProductChannelPrice.tenant_id == tenant_id
        ))
        result = product_price.scalars().first()
        if not result:
            return None
        return result
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_all_product_prices (db:AsyncSession, channel_id:UUID, tenant_id:UUID, skip: int=0, limit: int = 0) -> List[ProductChannelPrice]:
    try:
        query = select(ProductChannelPrice).where(
            ProductChannelPrice.tenant_id == tenant_id,
            ProductChannelPrice.channel_id == channel_id
        )
        list_of_channel_prices = await db.execute(paginate(query, skip, limit))
        return list_of_channel_prices.scalars().all()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def delete_product_price(db:AsyncSession, product_id:UUID, channel_id:UUID, tenant_id:UUID):
    try:
        channel_price_to_delete = await get_product_price_by_id(db, product_id, channel_id, tenant_id)
        if not channel_price_to_delete:
            raise HTTPException(status_code=404, detail="Precio de producto en canal no encontrado")
        await db.delete(channel_price_to_delete)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

#Services de Promotion:
async def create_promotion(db:AsyncSession, tenant_id:UUID, promotion_data:PromotionCreate) -> Promotion:
    try:
        new_promotion = Promotion(**promotion_data.model_dump())
        new_promotion.tenant_id = tenant_id
        db.add(new_promotion)
        await db.commit()
        await db.refresh(new_promotion)
        return new_promotion
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_promotions_by_channel(db:AsyncSession, channel_id:UUID, tenant_id:UUID, skip: int=0, limit: int = 0) -> List[Promotion]:
    try:
        query = select(Promotion).where(
            Promotion.tenant_id == tenant_id,
            Promotion.channel_id == channel_id
        )
        list_of_promotion_channel = await db.execute(paginate(query, skip, limit))
        return list_of_promotion_channel.scalars().all()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
async def get_promotion_by_id(db: AsyncSession, promotion_id: UUID, channel_id: UUID, tenant_id: UUID) -> Promotion | None:
    try:
        result = await db.execute(
            select(Promotion).where(
                Promotion.id == promotion_id,
                Promotion.channel_id == channel_id,
                Promotion.tenant_id == tenant_id
            )
        )
        return result.scalars().first()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_active_promotion(db: AsyncSession, channel_id: UUID, tenant_id: UUID, product_id: UUID | None = None, skip: int=0, limit: int = 0) -> list[Promotion]:
    try:
        now = datetime.now(timezone.utc)

        query = select(Promotion).where(
            Promotion.tenant_id == tenant_id,
            Promotion.channel_id == channel_id,
            Promotion.is_active.is_(True),
            Promotion.start_date <= now,
            or_(
                Promotion.end_date >= now,
                Promotion.end_date.is_(None)
            )
        )

        if product_id:
            query = query.where(Promotion.product_id == product_id)
        else:
            query = query.where(Promotion.product_id.is_(None))

        # limit<=0 significa "sin límite" (LIMIT 0 devolvería siempre vacío)
        result = await db.execute(paginate(query, skip, limit) if limit > 0 else query.offset(skip))
        promotions = result.scalars().all()
        return promotions
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_promotion(db:AsyncSession, promotion_id:UUID, tenant_id:UUID, promotion_data:PromotionUpdate) -> Promotion:
    try:
        promotion_to_update = await db.execute(select(Promotion).where(
            Promotion.tenant_id == tenant_id,
            Promotion.id == promotion_id
        ))
        result = promotion_to_update.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Promocion no encontrada")
        update_data = promotion_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(result, field, value)
        db.add(result)
        await db.commit()
        await db.refresh(result)
        return result
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def delete_promotion(db:AsyncSession, promotion_id:UUID, tenant_id:UUID) -> None:
    try:
        promotion_to_delete = await db.execute(select(Promotion).where(
            Promotion.tenant_id == tenant_id,
            Promotion.id == promotion_id
        ))
        result = promotion_to_delete.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Promocion no encontrada")
        await db.delete(result)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

#Services de ClientOrder:
async def _restore_stock_for_order(db: AsyncSession, order: ClientOrder, tenant_id: UUID, user_id: UUID) -> None:
    """Devuelve al inventario el stock de los items de una orden cancelada/rechazada."""
    for item in order.items:
        await register_transaction(
            db=db,
            product_id=item.product_id,
            quantity=item.quantity,
            transaction_type=TransactionType.IN,
            tenant_id=tenant_id,
            reference_id=order.id,
            user_id=user_id,
            auto_commit=False
        )

async def create_order(db:AsyncSession, tenant_id:UUID, order_data:ClientOrderCreate, user_id:UUID) -> ClientOrder:
    try:
        # 1. VALIDAR CANAL DE VENTAS
        channel = await db.execute(
            select(SalesChannel).where(
                SalesChannel.id == order_data.channel_id,
                SalesChannel.tenant_id == tenant_id
            )
        )
        result = channel.scalars().first()
        if not result:
            raise HTTPException(404, detail = "Canal de ventas no encontrado")

        # 3. PROCESAR ITEMS
        total_amount = 0
        total_cost = 0
        order_items = []

        for item in order_data.items:
            product = await get_product_by_id(db, item.product_id, tenant_id)
            if not product:
                raise HTTPException(status_code=404, detail=f"producto no encontrado: {item.product_id}")
            if product.stock_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"falta stock para la transacción de: {item.product_id} tiene {product.stock_quantity} y necesitas como minimo {item.quantity}")
            promotion_product = await get_active_promotion(db, order_data.channel_id, tenant_id, product_id=item.product_id)
            promotion_channel = await get_active_promotion(db, order_data.channel_id, tenant_id, product_id=None)
            # get_active_promotion devuelve una lista; priorizar promo de producto sobre la de canal
            promotions = promotion_product or promotion_channel
            promotion = promotions[0] if promotions else None
            # Traer producto con precio de canal o base
            product_price = await get_product_price_by_id(
                db, item.product_id, order_data.channel_id, tenant_id
            )

            if product_price:
                unit_price = product_price.price
            else:
                unit_price = product.base_price

            # Obtener costo del producto
            unit_cost = product.cost_price

            # Calcular subtotal
            subtotal = float(unit_price) * item.quantity

            # Aplicar descuento si hay promoción (la de producto prioriza sobre la de canal)
            if promotion:
                discount_value = float(promotion.discount_value)
                if promotion.discount_type == DiscountType.PERCENTAGE:
                    subtotal -= subtotal * (discount_value / 100)
                elif promotion.product_id is not None:
                    # Descuento fijo por producto: aplica a este item
                    subtotal -= min(discount_value, subtotal)
                # Descuento fijo de canal: NO se aplica acá; se descuenta una vez sobre el total

            total_amount += subtotal
            total_cost += float(unit_cost) * item.quantity

            # Crear objeto del item (NO guardar aún)
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost
            })

        # Aplicar descuento fijo de canal UNA sola vez sobre el total
        if promotion and promotion.product_id is None and promotion.discount_type == DiscountType.FIXED_AMOUNT:
            total_amount = max(total_amount - float(promotion.discount_value), 0)

        # 4. CREAR ORDEN PRINCIPAL
        order_status = order_data.status if order_data.status else OrderStatus.PENDING
        new_order = ClientOrder(
            tenant_id=tenant_id,
            channel_id=order_data.channel_id,
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            payment_method=order_data.payment_method,
            total_amount=total_amount,
            total_cost=total_cost,
            total_tax=0,  # calcular si tenés IVA
            status=order_status,
            notes=order_data.notes,
            last_modified_by=user_id,
            modification_count=0,
            original_value_snapshot={
                "total_amount": total_amount,
                "total_cost": total_cost
            }
        )
        db.add(new_order)
        await db.flush()  # Para obtener el ID
        # 5. CREAR ITEMS RELACIONADOS Y DESCONTAR STOCK
        for item_data in order_items:
            order_item = ClientOrderItem(
                order_id=new_order.id,
                **item_data
            )
            db.add(order_item)
            # Descuento de stock con registro de inventario (mismo commit)
            await register_transaction(
                db=db,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                transaction_type=TransactionType.OUT,
                tenant_id=tenant_id,
                reference_id=new_order.id,
                user_id=user_id,
                auto_commit=False
            )
        # 6. COMMIT TRANSACCIÓN
        await db.commit()
        await db.refresh(new_order)

        # 7. CARGAR RELACIONES PARA RETORNO
        return await get_order_by_id(db, new_order.id, tenant_id)

    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_orders(db:AsyncSession, tenant_id:UUID, channel_id: Optional[UUID], status: Optional[OrderStatus], skip: int=0, limit: int = 0, start_date: Optional[date] = None, end_date: Optional[date] = None) -> tuple[List[ClientOrder], int]:
    try:
        # Rango: si no se especifica start_date, se listan las de hoy (comportamiento default)
        if start_date:
            range_start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        else:
            range_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        base_where = [ClientOrder.tenant_id == tenant_id, ClientOrder.created_at >= range_start]
        if end_date:
            base_where.append(ClientOrder.created_at <= datetime.combine(end_date, time.max, tzinfo=timezone.utc))
        if channel_id:
            base_where.append(ClientOrder.channel_id == channel_id)
        if status:
            base_where.append(ClientOrder.status == status)

        count_query = select(func.count()).select_from(ClientOrder).where(*base_where)
        total = (await db.execute(count_query)).scalar() or 0

        query = (select(ClientOrder)
                 .where(*base_where)
                 .options(joinedload(ClientOrder.channel), joinedload(ClientOrder.items))
                 .order_by(ClientOrder.created_at.desc())
        )

        result = await db.execute(paginate(query, skip, limit))
        return result.scalars().unique().all(), total

    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_order_by_id(db:AsyncSession, order_id:UUID, tenant_id:UUID) -> ClientOrder:
    try:
        order = await db.execute(select(ClientOrder)
                                 .where(ClientOrder.id == order_id,
                                        ClientOrder.tenant_id == tenant_id)
                                 .options(
                                     joinedload(ClientOrder.channel),
                                     joinedload(ClientOrder.items)
        ))
        if not order:
            raise HTTPException(404, "Orden de venta no encontrada")
        return order.scalars().first()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_order(db: AsyncSession, order_id: UUID, tenant_id: UUID, order_data: ClientOrderUpdate, user_id: UUID) -> ClientOrder:
    try:
        from app.models.user import Users
        
        order = await get_order_by_id(db, order_id, tenant_id)
        
        update_data = order_data.model_dump(exclude_unset=True)
        
        old_status = order.status
        
        # Solo actualizar status y notes
        if "status" in update_data and update_data["status"]:
            new_status = update_data["status"]
            
            # Si es string, convertir a enum
            if isinstance(new_status, str):
                try:
                    new_status = OrderStatus(new_status)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Estado inválido: {new_status}")
            
            # Validar transiciones
            if order.status == OrderStatus.PENDING:
                if new_status not in [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED]:
                    raise HTTPException(status_code=400, detail="De Pendiente solo puede pasar a En Proceso o Cancelado")
            elif order.status == OrderStatus.IN_PROGRESS:
                if new_status not in [OrderStatus.COMPLETED, OrderStatus.REJECTED]:
                    raise HTTPException(status_code=400, detail="De En Proceso solo puede pasar a Entregado o Rechazado")
            
            order.status = new_status
            
            # Devolver stock y notificar si se canceló o rechazó
            if new_status in [OrderStatus.CANCELLED, OrderStatus.REJECTED] and old_status != new_status:
                await _restore_stock_for_order(db, order, tenant_id, user_id)

                from app.services.alerts_service import notify_sale_cancelled, notify_sale_rejected
                
                user_result = await db.execute(select(Users).where(Users.id == user_id))
                user = user_result.scalars().first()
                user_name = user.full_name if user else str(user_id)[:8]
                
                order_data_dict = {
                    "customer_name": order.customer_name,
                    "total_amount": float(order.total_amount),
                    "channel_name": order.channel.name if order.channel else "N/A"
                }
                
                if new_status == OrderStatus.CANCELLED:
                    await notify_sale_cancelled(db, tenant_id, order_id, order_data_dict, user_id, user_name)
                else:
                    await notify_sale_rejected(db, tenant_id, order_id, order_data_dict, user_id, user_name)
        
        if "notes" in update_data:
            order.notes = update_data["notes"]
        
        # Auditoría: preservar snapshot original de creación y acumular historial de modificaciones
        prev_snapshot = dict(order.original_value_snapshot) if order.original_value_snapshot else {}
        modifications = list(prev_snapshot.get("modifications", []))
        modifications.append({
            "modified_at": datetime.now(timezone.utc).isoformat(),
            "modified_by": str(user_id),
            "fields": {
                k: (v if isinstance(v, (str, int, float, bool)) else str(v))
                for k, v in update_data.items()
            },
        })
        order.original_value_snapshot = {**prev_snapshot, "modifications": modifications}
        order.modification_count += 1
        order.last_modified_by = user_id
        await db.commit()
        await db.refresh(order)
        return await get_order_by_id(db, order_id, tenant_id)
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def cancel_order(db:AsyncSession, order_id:UUID, tenant_id:UUID, user_id: UUID) -> ClientOrder:
    try:
        from app.models.user import Users
        from app.services.alerts_service import notify_sale_cancelled
        
        order = await get_order_by_id(db, order_id, tenant_id)
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Solo se puede cancelar una orden en estado Pendiente"
            )
        order.status = OrderStatus.CANCELLED

        # Devolver stock de los items (mismo commit)
        await _restore_stock_for_order(db, order, tenant_id, user_id)
        
        user_result = await db.execute(select(Users).where(Users.id == user_id))
        user = user_result.scalars().first()
        user_name = user.full_name if user else str(user_id)[:8]
        
        order_data_dict = {
            "customer_name": order.customer_name,
            "total_amount": float(order.total_amount),
            "channel_name": order.channel.name if order.channel else "N/A"
        }
        
        await notify_sale_cancelled(db, tenant_id, order_id, order_data_dict, user_id, user_name)
        
        await db.commit()
        await db.refresh(order)
        return order
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def get_cancelled_orders(
    db: AsyncSession,
    tenant_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[ClientOrder], int]:
    """
    Obtiene todas las órdenes canceladas o rechazadas (histórico paginado).
    """
    try:
        base_where = [
            ClientOrder.tenant_id == tenant_id,
            ClientOrder.status.in_([OrderStatus.CANCELLED, OrderStatus.REJECTED])
        ]

        count_query = select(func.count()).select_from(ClientOrder).where(*base_where)
        total = (await db.execute(count_query)).scalar() or 0

        query = (
            select(ClientOrder)
            .where(*base_where)
            .options(joinedload(ClientOrder.channel), joinedload(ClientOrder.items))
            .order_by(ClientOrder.created_at.desc())
        )
        
        result = await db.execute(paginate(query, skip, limit))
        return result.scalars().unique().all(), total
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))