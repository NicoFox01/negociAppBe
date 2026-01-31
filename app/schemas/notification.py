from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from app.models.enums import NotificationStatus, NotificationType
from datetime import date, datetime
from pydantic.config import ConfigDict

class NotificationBase(BaseModel):
    type: NotificationType
    
class NotificationCreate(NotificationBase):
    user_id: UUID
    tenant_id: UUID

class NotificationUpdate(NotificationBase):
    status: NotificationStatus

class NotificationSchema(NotificationBase):
    id: UUID
    status: NotificationStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RequestResetRequest(NotificationBase):
    username: str
    