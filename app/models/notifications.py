from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, String, Date, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.base import Base
from app.models.enums import NotificationStatus, NotificationType

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False) 
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    type = Column(SQLEnum(NotificationType), default=NotificationType.RESET_PASSWORD_REQUEST, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default = NotificationStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))
    # Relationship
    tenant = relationship("Tenants", back_populates="notifications")
    user = relationship("Users", back_populates="notifications")
    