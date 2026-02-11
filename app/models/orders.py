from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy import Column, String, Boolean, Date,  Integer, DateTime
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4
from app.models.enums import PurchaseOrderStatus
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
    notes = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))

    # Relationships
    tenant = relationship("Tenants")
    supplier = relationship("Suppliers")
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