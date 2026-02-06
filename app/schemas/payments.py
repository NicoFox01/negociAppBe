from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from app.models.enums import PaymentStatus, PaymentType
from datetime import date, datetime
from pydantic.config import ConfigDict


class PaymentBase(BaseModel):
    amount: float
    type: PaymentType
    payment_period: date

class PaymentCreate(PaymentBase):
    proof_url:str

class PaymentUpdate(PaymentBase):
    status: Optional[PaymentStatus]

class PaymentSchema(PaymentBase):
    id: UUID
    tenant_id: UUID
    payment_date: datetime
    status: PaymentStatus
    proof_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)