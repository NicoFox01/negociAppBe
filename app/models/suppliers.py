from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Enum as SQLEnum, ForeignKey
from sqlalchemy import Column, String, Boolean, Date
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4

from app.models.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(40), nullable=True)
    cbu = Column(String(22), nullable=True)

    # Relationships
    tenant = relationship("Tenants", back_populates="suppliers", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="supplier", cascade="all, delete-orphan")
