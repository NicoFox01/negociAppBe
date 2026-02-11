from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy import Column, String, Boolean, Date,  Integer, DateTime
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4
from app.models.enums import TransactionType
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.base import Base

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    quantity = Column(Numeric(10,2), nullable=False)
    reference_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))

    # Relationships
    product = relationship("Product")
    tenant = relationship("Tenants")