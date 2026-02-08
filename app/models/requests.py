from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Enum as SQLEnum, ForeignKey
from sqlalchemy import Column, String, Boolean, Date,  Integer, DateTime
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4
from app.models.enums import PurchaseRequestStatus
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.base import Base

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLEnum(PurchaseRequestStatus), default=PurchaseRequestStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))

    # Relationships
    tenant = relationship("Tenants", back_populates="requests")
    user = relationship("Users", back_populates="requests")
    items = relationship("PurchaseRequestItem", back_populates="request", cascade="all, delete-orphan")

class PurchaseRequestItem(Base):
    __tablename__ = "purchase_request_items"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(PG_UUID(as_uuid=True), ForeignKey("purchase_requests.id"), nullable=False, index=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)

    # Relationships
    request = relationship("PurchaseRequest", back_populates="items")
    product = relationship("Product")