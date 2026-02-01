from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.models.enums import Roles

class UserBase(BaseModel):
    username: str # Nickname
    full_name: str
    role: Roles = Roles.EMPLOYEE

class UserCreate(UserBase):
    password: str
    tenant_id: UUID

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserSchema(UserBase):
    id: UUID
    tenant_id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
class PasswordReset(BaseModel):
    new_password: str
