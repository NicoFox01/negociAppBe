from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import ForeignKey
from sqlalchemy import Column, Numeric, DateTime
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4
from datetime import datetime
from zoneinfo import ZoneInfo
from app.models.base import Base

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

class ProductionTransform(Base):
    __tablename__ = "transforms"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ARG))

    # Relationships
    tenant = relationship("Tenants", back_populates="transformations")
    user = relationship("Users", back_populates="transformations")

    inputs = relationship(
        "ProductionTransformInput",
        back_populates="transform",
        cascade="all, delete-orphan"
    )

    outputs = relationship(
        "ProductionTransformOutput",
        back_populates="transform",
        cascade="all, delete-orphan"
    )


class ProductionTransformInput(Base):
    __tablename__ = "transforms_input"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    transform_id = Column(PG_UUID(as_uuid=True), ForeignKey("transforms.id"), index=True, nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"), index=True, nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)

    #Relationship
    transform = relationship("ProductionTransform", back_populates="inputs")
    product = relationship("Product", back_populates="transform_inputs")

class ProductionTransformOutput(Base):
    __tablename__ = "transforms_output"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    transform_id = Column(PG_UUID(as_uuid=True), ForeignKey("transforms.id"), index=True, nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id"), index=True, nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)

    #Relationship
    transform = relationship("ProductionTransform", back_populates="outputs")
    product = relationship("Product", back_populates="transform_outputs")