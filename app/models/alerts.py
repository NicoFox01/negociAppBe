from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import ForeignKey, Column, String, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.base import Base

ARG = ZoneInfo("America/Argentina/Buenos_Aires")


class StockAlert(Base):
    __tablename__ = "stock_alerts"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    min_stock_alert = Column(Numeric(10,2), nullable=False)
    enable_alert = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG), onupdate=lambda: datetime.now(ARG))
    
    tenant = relationship("Tenants", back_populates="stock_alerts")
    product = relationship("Product", back_populates="stock_alerts")
