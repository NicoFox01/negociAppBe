import pytest_asyncio
from types import SimpleNamespace

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.base import Base
from app.models.tenant import Tenants
from app.models.user import Users
from app.models.suppliers import Supplier
from app.models.products import Product
from app.models.orders import SalesChannel
from app.models.enums import PlanType, Roles, ProductType


@pytest_asyncio.fixture
async def db():
    """Sesión async sobre SQLite en memoria con todas las tablas creadas."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def seed_data(db):
    """Tenant + usuario COMPANY + canal de venta + 2 productos vendibles (stock 10, precio 100)."""
    tenant = Tenants(name="Empresa Test", plan_type=PlanType.FREE_TRIAL_1_MONTH, contact_name="Owner")
    db.add(tenant)
    await db.flush()

    user = Users(
        tenant_id=tenant.id,
        username="owner",
        hashed_password="no-importa",
        full_name="Owner",
        role=Roles.COMPANY,
    )
    supplier = Supplier(tenant_id=tenant.id, name="Proveedor Test")
    db.add_all([user, supplier])
    await db.flush()

    channel = SalesChannel(tenant_id=tenant.id, name="Local", commission_rate=0, is_active=True)
    db.add(channel)

    p1 = Product(
        tenant_id=tenant.id,
        supplier_id=supplier.id,
        sku="P-001",
        name="Producto Uno",
        product_type=ProductType.PRODUCT_ELABORATED,
        stock_quantity=10,
        base_price=100,
        cost_price=50,
    )
    p2 = Product(
        tenant_id=tenant.id,
        supplier_id=supplier.id,
        sku="P-002",
        name="Producto Dos",
        product_type=ProductType.PRODUCT_PURCHASED,
        stock_quantity=10,
        base_price=100,
        cost_price=50,
    )
    db.add_all([p1, p2])
    await db.commit()
    await db.refresh(channel)
    await db.refresh(p1)
    await db.refresh(p2)

    return SimpleNamespace(
        tenant=tenant, user=user, supplier=supplier, channel=channel, p1=p1, p2=p2
    )
