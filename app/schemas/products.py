from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

from app.schemas.suppliers import SuppliersSchema
from app.models.enums import ProductType

class ProductsBase(BaseModel):
    name: str

class ProductsCreate(ProductsBase):
    sku: Optional[str] = None
    unit: str
    base_price: float = Field(..., ge=0)
    cost_price: float = Field(..., ge=0)
    stock_quantity: float = Field(..., ge=0)
    is_raw_material: bool = False
    expiration_date: Optional[date] = None
    supplier_id: UUID
    product_type: ProductType = ProductType.RAW_MATERIAL
    min_stock_alert: Optional[float] = Field(None, ge=0)
    enable_alert: bool = False

    model_config = ConfigDict(from_attributes=True)

class ProductsUpdate(ProductsBase):
    name: Optional[str] = None
    sku: Optional[str] = None
    unit: Optional[str] = None
    base_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    stock_quantity: Optional[float] = Field(None, ge=0)
    is_raw_material: Optional[bool] = None
    expiration_date: Optional[date] = None
    supplier_id: Optional[UUID] = None
    product_type: Optional[ProductType] = None
    min_stock_alert: Optional[float] = Field(None, ge=0)
    enable_alert: Optional[bool] = None

class ProductsSchema(ProductsBase):
    id: UUID
    tenant_id: UUID
    sku: str
    unit: str
    base_price: float
    cost_price: float
    is_raw_material: bool
    stock_quantity: float
    expiration_date: Optional[date]
    supplier_id: UUID
    product_type: ProductType
    min_stock_alert: Optional[float]
    enable_alert: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
    
class ProductWithSuppliersSchema (ProductsSchema):
    supplier: Optional[SuppliersSchema] = None