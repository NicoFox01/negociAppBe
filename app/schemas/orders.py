from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import List, Optional

from sqlalchemy import JSON

from app.schemas.products import ProductsSchema
from app.models.enums import PurchaseOrderStatus, DiscountType, OrderStatus
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

class SalesChannelBase(BaseModel):
    name: str
    commission_rate: float = Field(..., ge=0, le=1)
    is_active: bool

class SalesChannelCreate(SalesChannelBase):
    pass

class SalesChannelUpdate(SalesChannelBase):
    name: Optional[str] = None
    commission_rate: Optional[float] = None
    is_active: Optional[bool] = None

class SalesChannelSchema(SalesChannelBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductChannelPriceBase(BaseModel):
    product_id: UUID
    channel_id: UUID
    price: float

class ProductChannelPriceCreate(ProductChannelPriceBase):
    pass

class ProductChannelPriceUpdate(ProductChannelPriceBase):
    price: Optional[float] = None

class ProductChannelPriceSchema(ProductChannelPriceBase):
    id: UUID
    tenant_id: UUID

    model_config = ConfigDict(from_attributes=True)

class PromotionBase(BaseModel):
    channel_id: UUID
    product_id: Optional[UUID] = None
    name: str
    discount_type: DiscountType
    discount_value: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(PromotionBase):
    name: Optional[str] = None
    product_id: Optional[UUID] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class PromotionSchema(PromotionBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ClientOrderItemBase(BaseModel):
    product_id: UUID
    quantity: float = Field(...,gt=0)

class ClientOrderItemCreate(ClientOrderItemBase):
    pass

class ClientOrderItemUpdate(ClientOrderItemBase):
    quantity: Optional[float] = None

class ClientOrderItemSchema(ClientOrderItemBase):
    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: float
    unit_price: float
    unit_cost: float

    model_config = ConfigDict(from_attributes=True)

class ClientOrderBase(BaseModel):
    channel_id: UUID
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[ClientOrderItemBase]
    notes: Optional[str] = None

class ClientOrderCreate(ClientOrderBase):
    pass

class ClientOrderUpdate(ClientOrderBase):
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None

class ClientOrderSchema(ClientOrderBase):
    id: UUID
    tenant_id: UUID
    total_amount: float
    total_cost: float
    total_tax: float
    status: OrderStatus
    created_at: datetime
    last_modified_by: Optional[UUID]=None
    modification_count: int = Field(..., ge=0)
    original_value_snapshot: Optional[JSON] = None
    items: List[ClientOrderItemSchema]
    model_config = ConfigDict(from_attributes=True)