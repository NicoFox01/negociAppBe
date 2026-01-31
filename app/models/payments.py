from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, String, Date, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.base import Base
from app.models.enums import PaymentStatus, PaymentType

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

class Payments(Base):
    __tablename__ = "payments" # Fixed typo
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    amount = Column(Float, default=0.0)
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))
    payment_period = Column(Date, nullable=False)
    proof_url = Column(String(255), nullable=True)
    type = Column(SQLEnum(PaymentType), default=PaymentType.PAGO_MENSUAL, nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    # Relationship
    tenant = relationship("Tenants", back_populates="payments")