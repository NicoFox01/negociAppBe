from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

from app.models.enums import PlanType

class ProductsBase(BaseModel):
    name: str

class ProductsCreate(ProductsBase):
    sku: str
    unit: str
    base_price: float = Field(..., ge=0)
    cost_price: float = Field(..., ge=0)
    is_raw_material: bool = False
    supplier_id: UUID

class ProductsUpdate(ProductsBase):
    name: Optional[str] = None
    sku: Optional[str] = None
    unit: Optional[str] = None
    base_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    is_raw_material: Optional[bool] = None
    supplier_id: Optional[UUID] = None

class ProductsSchema(ProductsBase):
    id: UUID
    tenant_id: UUID
    sku: str
    unit: str
    base_price: float
    cost_price: float
    is_raw_material: bool
    stock_quantity: int
    supplier_id: UUID

    model_config = ConfigDict(from_attributes=True)