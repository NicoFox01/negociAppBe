from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    warning_payment: bool = False
    subscription_overdue: bool = False


class TokenPayload(BaseModel):
    sub: Optional[str] = None
