from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import PurchaseRequestStatus
from app.schemas.products import ProductWithSuppliersSchema 


class RequestItemBase(BaseModel):
    product_id: UUID
    quantity: int
    
class RequestItemCreate(RequestItemBase):
    pass

class RequestItemSchema(RequestItemBase):
    id: UUID
    product: Optional[ProductWithSuppliersSchema ] = None
    model_config = ConfigDict(from_attributes=True)


class RequestBase(BaseModel):
    status: PurchaseRequestStatus = PurchaseRequestStatus.PENDING
    
class RequestCreate(RequestBase):
    items: List[RequestItemCreate]
    
class RequestUpdate(BaseModel):
    status: Optional[PurchaseRequestStatus] = None
    
class RequestSchema(RequestBase):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    created_at: datetime
    items: List[RequestItemSchema]
    model_config = ConfigDict(from_attributes=True)