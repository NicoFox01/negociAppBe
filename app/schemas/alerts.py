from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class StockAlertBase(BaseModel):
    product_id: UUID
    min_stock_alert: float = Field(..., ge=0)
    enable_alert: bool = True


class StockAlertCreate(StockAlertBase):
    pass


class StockAlertUpdate(BaseModel):
    min_stock_alert: Optional[float] = Field(None, ge=0)
    enable_alert: Optional[bool] = None


class StockAlertSchema(StockAlertBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockAlertWithProduct(StockAlertSchema):
    product_name: str
    product_type: str
    current_stock: float


class ProductAlertConfig(BaseModel):
    min_stock_alert: Optional[float] = Field(None, ge=0)
    enable_alert: Optional[bool] = None
