from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import List, Optional

from app.schemas.products import ProductsSchema
from app.models.enums import PurchaseOrderStatus
from app.schemas.suppliers import SuppliersSchema


class OrderItemBase(BaseModel):
    product_id: UUID
    quantity: float = Field(..., ge=0)
    unit_price: Optional[float] = None

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(BaseModel):
    received_quantity: Optional[float] = Field(..., ge=0)

class OrderItemSchema(OrderItemBase):
    id: UUID
    received_quantity: float
    product: ProductsSchema

    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    supplier_id: UUID
    expected_delivery_date: Optional [date] = None
    notes: Optional [str]
    
class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: PurchaseOrderStatus
    expected_delivery_date: Optional [date] = None
    notes: Optional [str] = None

class OrderSchema(OrderBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    supplier: SuppliersSchema
    items: List[OrderItemSchema]

    model_config = ConfigDict(from_attributes=True)