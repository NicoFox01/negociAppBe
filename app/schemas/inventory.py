from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from app.models.enums import TransactionType

class InventoryTransactionBase(BaseModel):
    transaction_type: TransactionType
    quantity: int = Field(..., gt=0)

class InventoryTransactionCreate(InventoryTransactionBase):
    product_id: UUID
    reference_id: Optional[UUID]

class InventoryTransactionSchema(InventoryTransactionBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)