from fastapi import APIRouter, Depends, HTTPException
from app.models import PlanType
from datetime import timedelta
from typing import Annotated, TYPE_CHECKING, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

if TYPE_CHECKING:
    from app.models.user import Users
from app.core.config import settings
from uuid import UUID

from app.core.security import create_access_token, verify_password
from app.api.deps import get_current_user, get_db
from app.schemas.token import Token
from app.schemas.tenant import TenantCreate, TenantSchema
from app.schemas.user import UserCreate
from app.services import tenant_services, user_services

router = APIRouter()

@router.post("/register", response_model=TenantSchema)
async def register(
    tenant: TenantCreate,
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
    ) -> Any:
    tenant.plan_type = PlanType.FREE_TRIAL_1_MONTH
    return await tenant_services.create_tenant_with_admin(db, tenant, user)

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
    ) -> Token:
    user = await user_services.get_by_username(db, form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code = 400, detail="Contraseña incorrecta")
    if not user.is_active:
        raise HTTPException(status_code = 400, detail="Usuario inactivo")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer"
    )
    



from app.schemas.user import PasswordChange, PasswordReset

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[Any, Depends(get_current_user)] = None # Annotated type Any to avoid circular import issues if Users is not imported, though get_current_user returns Users.
):
    # current_user is already verified by get_current_user
    return await user_services.change_password(db, current_user.id, password_data.current_password, password_data.new_password)

@router.patch("/reset-password/{target_user_id}")
async def reset_password(
    target_user_id: UUID, 
    password_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[Any, Depends(get_current_user)] = None
):
    # Lógica de permisos manejada en el servicio
    return await user_services.reset_password(db, current_user, target_user_id, password_data.new_password)
