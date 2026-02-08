from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, String, Boolean, Integer, Numeric
from sqlalchemy.orm import relationship
from uuid import UUID, uuid4

from app.models.base import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    sku = Column(String(64), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    unit = Column(String(10), nullable=False, default="u")
    base_price = Column(Numeric(10,2), nullable=False, default=0)
    cost_price = Column(Numeric(10,2), nullable=False, default=0)
    stock_quantity = Column(Integer(20), nullable=False, default=0)
    is_raw_material = Boolean(default=False)
    supplier_id = Column(PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    __table_args__ = UniqueConstraint("sku", "tenant_id", name="uq_product_sku_tenant")
    # Relationships
    tenant = relationship("Tenants", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")