from datetime import datetime, timezone
from uuid import UUID

from dns.e164 import query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from fastapi import HTTPException
from typing import List,  Optional
from decimal import Decimal
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from app.models.products import Product

from app.models.orders import SalesChannel, ProductChannelPrice, Promotion, ClientOrder, ClientOrderItem
from app.schemas.orders import SalesChannelSchema, ClientOrderSchema, ClientOrderItemSchema, SalesChannelCreate, \
    ClientOrderCreate, ClientOrderItemCreate, SalesChannelUpdate, ClientOrderUpdate, ClientOrderItemUpdate, \
    PromotionCreate, PromotionUpdate, OrderCreate
from app.models.enums import DiscountType, OrderStatus
from app.utils.pagination import paginate


#Services de SalesChannel:
async def create_sales_channel(db: AsyncSession, tenant_id: UUID, channel_data: SalesChannelCreate) -> SalesChannel:
    try:
        new_sales_channel = SalesChannel(**channel_data.model_dump())
        new_sales_channel.tenant_id = tenant_id
        await db.add(new_sales_channel)
        await db.commit()
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
        list_of_sales_channels = await db.execute(paginate(query, skip, limit))
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
        sales_channel = await db.execute(paginate(query, skip, limit))
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
        await db.add(result)
        await db.commit()
        await db.refresh(result)
        return result
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
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
        await db.add(new_promotion)
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

        result = await db.execute(paginate(query, skip, limit))
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
        await db.add(result)
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
            promotion = promotion_product or promotion_channel
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

            # Aplicar descuento si hay promoción
            if promotion:
                if promotion.discount_type == DiscountType.PERCENTAGE:
                    discount = subtotal * (promotion.discount_value / 100)
                else:
                    discount = promotion.discount_value
                subtotal -= discount

            total_amount += subtotal
            total_cost += float(unit_cost) * item.quantity

            # Crear objeto del item (NO guardar aún)
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost
            })
        # 4. CREAR ORDEN PRINCIPAL
        new_order = ClientOrder(
            tenant_id=tenant_id,
            channel_id=order_data.channel_id,
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            total_amount=total_amount,
            total_cost=total_cost,
            total_tax=0,  # calcular si tenés IVA
            status=OrderStatus.PENDING,
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
        # 5. CREAR ITEMS RELACIONADOS
        for item_data in order_items:
            order_item = ClientOrderItem(
                order_id=new_order.id,
                **item_data
            )
            db.add(order_item)
        # 6. COMMIT TRANSACCIÓN
        await db.commit()
        await db.refresh(new_order)

        # 7. CARGAR RELACIONES PARA RETORNO
        return await get_order_by_id(db, new_order.id, tenant_id)

    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_orders(db:AsyncSession, tenant_id:UUID, channel_id: Optional[UUID], status: Optional[OrderStatus], skip: int=0, limit: int = 0) -> List[ClientOrder]:
    try:
        query = (select(ClientOrder)
                 .where(ClientOrder.tenant_id == tenant_id)
                 .options(
            joinedload(ClientOrder.channel),
            joinedload(ClientOrder.items))
        )
        if channel_id:
            query = query.where(ClientOrder.channel_id == channel_id)
        if status:
            query = query.where(ClientOrder.status == status)

        query = query.order_by(ClientOrder.created_at.desc())

        result = await db.execute(paginate(query, skip, limit))
        return result.scalars().all()

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
                                    joinedload(ClientOrder.items.product)
                                        .joinedload(ClientOrder.channel)
        ))
        if not order:
            raise HTTPException(404, "Orden de venta no encontrada")
        return order
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_order(db: AsyncSession, order_id: UUID, tenant_id: UUID, order_data: ClientOrderUpdate, user_id: UUID) -> ClientOrder:
    try:
        order = await get_order_by_id(db, order_id, tenant_id)
        if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise HTTPException(
                status_code=400,
                detail="No se puede editar la orden en este estado"
            )

        update_data = order_data.model_dump(exclude_unset=True)
        if "items" in update_data and update_data["items"]:
            total_amount = 0
            total_cost = 0
            new_items = []
            for item in update_data["items"]:
                promotion_product = await get_active_promotion(db, order_data.channel_id, tenant_id,
                                                               product_id=item.product_id)
                promotion_channel = await get_active_promotion(db, order_data.channel_id, tenant_id, product_id=None)
                promotion = promotion_product or promotion_channel
                product = await db.get(Product, item.product_id)
                channel_price = await db.execute(
                    select(ProductChannelPrice).where(
                        ProductChannelPrice.product_id == item.product_id,
                        ProductChannelPrice.channel_id == order.channel_id,
                        ProductChannelPrice.tenant_id == tenant_id
                    )
                )
                channel_price_obj = channel_price.scalars().first()

                unit_price = channel_price_obj.price if channel_price_obj else product.base_price
                unit_cost = product.cost_price

                subtotal = float(unit_price) * item.quantity
                if promotion:
                    if promotion.discount_type == DiscountType.PERCENTAGE:
                        discount = subtotal * (float(promotion.discount_value) / 100)
                    else:
                        discount = float(promotion.discount_value)
                    subtotal -= discount
                total_amount += subtotal
                total_cost += float(unit_cost) * item.quantity
                new_items.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "unit_cost": unit_cost
                })
            if order.modification_count == 0:
                order.original_value_snapshot = {
                    "total_amount": float(order.total_amount),
                    "total_cost": float(order.total_cost),
                    "status": order.status.value
                }
            order.total_amount = total_amount
            order.total_cost = total_cost
            order.modification_count += 1

            existing_items = await db.execute(
                select(ClientOrderItem).where(ClientOrderItem.order_id == order_id)
            )
            for item in existing_items.scalars().all():
                await db.delete(item)

            for item_data in new_items:
                new_item = ClientOrderItem(order_id=order_id, **item_data)
                db.add(new_item)
        if "status" in update_data:
            order.status = update_data["status"]
        if "notes" in update_data:
            order.notes = update_data["notes"]
        order.last_modified_by = user_id
        await db.commit()
        await db.refresh(order)
        return await get_order_by_id(db, order_id, tenant_id)
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def cancel_order(db:AsyncSession, order_id:UUID, tenant_id:UUID) -> ClientOrder:
    try:
        order = await get_order_by_id(db, order_id, tenant_id)
        if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise HTTPException(
                status_code=400,
                detail="No se puede cancelar la orden en este estado"
            )
        order.status = OrderStatus.CANCELLED
        await db.commit()
        await db.refresh(order)
        return order
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))