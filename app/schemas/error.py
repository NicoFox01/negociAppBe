from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Optional

class ErrorSchema(BaseModel):
    code: str
    message: str
    details: dict | None = None
    model_config = ConfigDict(from_attributes=True)