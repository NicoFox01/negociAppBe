import pytest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, func

from app.services import sales_service
from app.schemas.orders import ClientOrderCreate, ClientOrderItemCreate, ClientOrderUpdate
from app.models.enums import OrderStatus, DiscountType
from app.models.products import Product
from app.models.orders import Promotion, ClientOrder


async def reload_product(db, product_id):
    """Re-lee el producto desde la DB forzando la actualización de atributos."""
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def orders_count(db):
    result = await db.execute(select(func.count(ClientOrder.id)))
    return result.scalar() or 0


def make_order_data(channel_id, items, customer_name="Cliente"):
    return ClientOrderCreate(channel_id=channel_id, customer_name=customer_name, items=items)


@pytest.mark.asyncio
async def test_create_order_discounts_stock(db, seed_data):
    s = seed_data
    data = make_order_data(s.channel.id, [ClientOrderItemCreate(product_id=s.p1.id, quantity=3)])

    order = await sales_service.create_order(db, s.tenant.id, data, s.user.id)

    assert float(order.total_amount) == 300.0
    assert float(order.total_cost) == 150.0
    assert order.status == OrderStatus.PENDING

    product = await reload_product(db, s.p1.id)
    assert float(product.stock_quantity) == 7.0


@pytest.mark.asyncio
async def test_create_order_insufficient_stock_rolls_back(db, seed_data):
    s = seed_data
    # Capturar ids antes del fallo: el rollback expira atributos de los objetos en sesión
    tenant_id, channel_id, user_id = s.tenant.id, s.channel.id, s.user.id
    p1_id, p2_id = s.p1.id, s.p2.id

    data = make_order_data(
        channel_id,
        [
            ClientOrderItemCreate(product_id=p1_id, quantity=2),
            ClientOrderItemCreate(product_id=p2_id, quantity=99),
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await sales_service.create_order(db, tenant_id, data, user_id)

    assert exc.value.status_code == 400
    assert await orders_count(db) == 0

    p1 = await reload_product(db, p1_id)
    p2 = await reload_product(db, p2_id)
    assert float(p1.stock_quantity) == 10.0
    assert float(p2.stock_quantity) == 10.0


@pytest.mark.asyncio
async def test_channel_fixed_promotion_applied_once_on_total(db, seed_data):
    s = seed_data
    now = datetime.now(timezone.utc)
    promo = Promotion(
        tenant_id=s.tenant.id,
        channel_id=s.channel.id,
        product_id=None,
        name="$50 off",
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=50,
        start_date=now - timedelta(days=1),
        end_date=None,
        is_active=True,
    )
    db.add(promo)
    await db.commit()

    data = make_order_data(
        s.channel.id,
        [
            ClientOrderItemCreate(product_id=s.p1.id, quantity=1),
            ClientOrderItemCreate(product_id=s.p2.id, quantity=1),
        ],
    )
    order = await sales_service.create_order(db, s.tenant.id, data, s.user.id)

    # 100 + 100 - 50 (una sola vez, no por item)
    assert float(order.total_amount) == 150.0


@pytest.mark.asyncio
async def test_percentage_promotion_applies_per_item(db, seed_data):
    s = seed_data
    now = datetime.now(timezone.utc)
    promo = Promotion(
        tenant_id=s.tenant.id,
        channel_id=s.channel.id,
        product_id=None,
        name="10% off",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10,
        start_date=now - timedelta(days=1),
        end_date=None,
        is_active=True,
    )
    db.add(promo)
    await db.commit()

    data = make_order_data(s.channel.id, [ClientOrderItemCreate(product_id=s.p1.id, quantity=2)])
    order = await sales_service.create_order(db, s.tenant.id, data, s.user.id)

    # 200 - 10% = 180
    assert float(order.total_amount) == 180.0


@pytest.mark.asyncio
async def test_update_order_audits_modifications_and_validates_transitions(db, seed_data):
    s = seed_data
    data = make_order_data(s.channel.id, [ClientOrderItemCreate(product_id=s.p1.id, quantity=1)])
    order = await sales_service.create_order(db, s.tenant.id, data, s.user.id)

    updated = await sales_service.update_order(
        db, order.id, s.tenant.id,
        ClientOrderUpdate(status=OrderStatus.IN_PROGRESS, notes="en cocina"),
        s.user.id,
    )

    assert updated.modification_count == 1
    assert updated.last_modified_by == s.user.id
    mods = updated.original_value_snapshot.get("modifications", [])
    assert len(mods) == 1
    assert "status" in mods[0]["fields"]
    assert updated.status == OrderStatus.IN_PROGRESS

    # Transición inválida: PENDING -> COMPLETED no permitida
    other_data = make_order_data(s.channel.id, [ClientOrderItemCreate(product_id=s.p1.id, quantity=1)])
    other = await sales_service.create_order(db, s.tenant.id, other_data, s.user.id)
    with pytest.raises(HTTPException) as exc:
        await sales_service.update_order(
            db, other.id, s.tenant.id,
            ClientOrderUpdate(status=OrderStatus.COMPLETED),
            s.user.id,
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_cancel_order_restores_stock(db, seed_data):
    s = seed_data
    data = make_order_data(s.channel.id, [ClientOrderItemCreate(product_id=s.p1.id, quantity=4)])
    order = await sales_service.create_order(db, s.tenant.id, data, s.user.id)

    p_after_sale = await reload_product(db, s.p1.id)
    assert float(p_after_sale.stock_quantity) == 6.0

    cancelled = await sales_service.cancel_order(db, order.id, s.tenant.id, s.user.id)

    assert cancelled.status == OrderStatus.CANCELLED
    p_restored = await reload_product(db, s.p1.id)
    assert float(p_restored.stock_quantity) == 10.0


@pytest.mark.asyncio
async def test_tenant_isolation(db, seed_data):
    from app.models.tenant import Tenants
    from app.models.enums import PlanType

    s = seed_data
    other_tenant = Tenants(name="Otra Empresa", plan_type=PlanType.FREE_TRIAL_1_MONTH, contact_name="Otro")
    db.add(other_tenant)
    await db.commit()

    data = make_order_data(s.channel.id, [ClientOrderItemCreate(product_id=s.p1.id, quantity=1)])
    order = await sales_service.create_order(db, s.tenant.id, data, s.user.id)

    assert await sales_service.get_order_by_id(db, order.id, other_tenant.id) is None
    assert await sales_service.get_order_by_id(db, order.id, s.tenant.id) is not None

    # Canal de otro tenant -> 404 al crear venta
    with pytest.raises(HTTPException) as exc:
        await sales_service.create_order(db, other_tenant.id, data, s.user.id)
    assert exc.value.status_code == 404
