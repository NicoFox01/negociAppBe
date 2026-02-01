from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

from app.models.enums import PlanType

class TenantBase(BaseModel):
    name: str
    contact_email: EmailStr
    contact_name: str
    phone_number: Optional[str] = None

class TenantCreate(TenantBase):
    plan_type: PlanType = PlanType.FREE_TRIAL_1_MONTH

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    plan_type: Optional[PlanType] = None

class TenantSchema(TenantBase):
    id: UUID
    plan_type: PlanType
    is_active: bool
    subscription_end: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)
