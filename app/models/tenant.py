from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, String, Boolean, Date
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4

from app.models.base import Base
from app.models.enums import PlanType

class Tenants(Base):
    __tablename__ = "tenants"
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    plan_type = Column(SQLEnum(PlanType), default=PlanType.FREE_TRIAL_1_MONTH, nullable=False)
    is_active = Column(Boolean, default=True)
    subscription_end = Column(Date, nullable=True)
    contact_name = Column(String(100), nullable=False)
    phone_number = Column(String(30), nullable=True)
    contact_email = Column(String(50), nullable=True)

    # Relationships
    users = relationship("Users", back_populates="tenant", cascade="all, delete-orphan")
    payments = relationship("Payments", back_populates="tenant", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="tenant", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="tenant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    requests = relationship("PurchaseRequest", back_populates="tenant", cascade="all, delete-orphan")
 