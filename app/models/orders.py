from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Enum as SQLEnum, ForeignKey, Numeric, JSON
from sqlalchemy import Column, String, Boolean, Date,  Integer, DateTime
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4
from app.models.enums import PurchaseOrderStatus, DiscountType, OrderStatus, PaymentMethod
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.models.base import Base

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id = Column(PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False, index=True)
    status = Column(SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    notes = Column(String(600), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))

    # Relationships
    tenant = relationship("Tenants")
    supplier = relationship("Supplier")
    items = relationship("PurchaseOrderItem", back_populates="order")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PG_UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Numeric(10,2), nullable=False)
    unit_price=Column(Numeric(10,2), nullable=False, default=0)
    received_quantity = Column(Numeric(10,2), nullable=False, default=0)

    # Relationships
    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")

class SalesChannel(Base):
    __tablename__ = "sales_channels"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))
    name = Column(String(100), nullable=False)
    commission_rate = Column(Numeric(5,4), nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))

    #Relationships
    tenant = relationship("Tenants", back_populates="sales_channels")
    products = relationship("ProductChannelPrice", back_populates="channel")
    promotions = relationship("Promotion", back_populates="channel")
    orders = relationship("ClientOrder", back_populates="channel")

class ProductChannelPrice(Base):
    __tablename__ = "product_channel_prices"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"))
    channel_id = Column(PG_UUID(as_uuid=True), ForeignKey("sales_channels.id"))
    price = Column(Numeric(10, 2), nullable=False)

    #Relationships
    tenant = relationship("Tenants")
    product = relationship("Product")
    channel = relationship("SalesChannel", back_populates="products")

class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))
    channel_id = Column(PG_UUID(as_uuid=True), ForeignKey("sales_channels.id"))
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    discount_type = Column(SQLEnum(DiscountType), nullable=False)
    discount_value = Column(Numeric(10,2), nullable=False, default=0)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))

    #Relationships
    tenant = relationship("Tenants", back_populates="promotions")
    channel = relationship("SalesChannel", back_populates="promotions")
    product = relationship("Product")

class ClientOrder(Base):
    __tablename__ = "client_orders"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))
    channel_id = Column(PG_UUID(as_uuid=True), ForeignKey("sales_channels.id"))
    customer_name = Column(String(100), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    total_amount = Column(Numeric(10,2), nullable=False, default=0)
    total_cost = Column(Numeric(10,2), nullable=False, default=0)
    total_tax = Column(Numeric(10,2), nullable=False, default=0)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))
    last_modified_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    modification_count = Column(Integer, nullable=False, default=0)
    original_value_snapshot = Column(JSON, nullable=True)

    #Relationships
    tenant = relationship("Tenants", back_populates="client_orders")
    channel = relationship("SalesChannel", back_populates="orders")
    user = relationship("Users", back_populates="client_orders")
    items = relationship("ClientOrderItem", back_populates="order")

class ClientOrderItem(Base):
    __tablename__ = "order_items"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PG_UUID(as_uuid=True), ForeignKey("client_orders.id"))
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Numeric(10,2), nullable=False)
    unit_price = Column(Numeric(10,2), nullable=False, default=0)
    unit_cost = Column(Numeric(10,2), nullable=False, default=0)

    #Relationships
    order = relationship("ClientOrder", back_populates="items")
    product = relationship("Product")