from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.models.base import Base
from app.models.enums import Roles

class Users(Base):
    __tablename__ = "users"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(SQLEnum(Roles), default=Roles.EMPLOYEE, nullable=False)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationship
    tenant = relationship("Tenants", back_populates="users")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
