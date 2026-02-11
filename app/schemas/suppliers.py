from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

from app.models.enums import PlanType

class SuppliersBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class SuppliersCreate(SuppliersBase):
    cbu: Optional[str] = None
    
class SuppliersUpdate(SuppliersBase):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    cbu: Optional[str] = None
class SuppliersSchema(SuppliersBase):
    id: UUID
    tenant_id: UUID
    
    model_config = ConfigDict(from_attributes=True)