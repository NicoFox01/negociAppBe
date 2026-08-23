from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import List, Optional
from app.models.enums import TransactionType, WasteReason

class InventoryTransactionBase(BaseModel):
    transaction_type: TransactionType
    quantity: float = Field(..., gt=0)

class InventoryTransactionCreate(InventoryTransactionBase):
    product_id: UUID
    reference_id: Optional[UUID]

class InventoryTransactionAdjustment(BaseModel):
    transaction_type: TransactionType
    product_id: UUID
    quantity: float
    reason: Optional[str] = None

class InventoryTransactionSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    user_full_name: Optional[str] = None
    transaction_type: TransactionType
    quantity: float
    reason: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductWasteCreate(BaseModel):
    product_id: UUID
    quantity: float = Field(..., gt=0)
    reason: WasteReason
    notes: Optional[str] = Field(None, max_length=500)


class ProductWasteSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    product_name: Optional[str] = None
    quantity: float
    reason: WasteReason
    reason_display: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: UUID
    recorded_by_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedProductWasteResponse(BaseModel):
    items: List[ProductWasteSchema]
    total: int
    skip: int
    limit: int