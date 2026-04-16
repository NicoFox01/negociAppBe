from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from app.schemas.products import ProductWithSuppliersSchema

class TransformInputItemBase(BaseModel):
    product_id: UUID
    quantity: float = Field(..., gt=0.0)

class TransformInputItemCreate(TransformInputItemBase):
    pass

class TransformInputItemSchema(TransformInputItemBase):
    id: UUID
    product: Optional[ProductWithSuppliersSchema] = None
    model_config = ConfigDict(from_attributes=True)

class TransformOutputItemBase(BaseModel):
    product_id: UUID
    quantity: float = Field(..., gt=0.0)

class TransformOutputItemCreate(TransformOutputItemBase):
    pass

class TransformOutputItemSchema(TransformOutputItemBase):
    id: UUID
    product: Optional[ProductWithSuppliersSchema] = None
    model_config = ConfigDict(from_attributes=True)

class ProductionTransformBase(BaseModel):
    pass

class ProductionTransformCreate(ProductionTransformBase):
    inputs: List[TransformInputItemCreate]
    outputs: List[TransformOutputItemCreate]

class ProductionTransformSchema(ProductionTransformBase):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    user_full_name: Optional[str] = None
    created_at: datetime
    inputs: List[TransformInputItemSchema]
    outputs: List[TransformOutputItemSchema]
    model_config = ConfigDict(from_attributes=True)