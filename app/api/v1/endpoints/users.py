from uuid import UUID
from app.api.deps import get_current_user, get_db
from app.models import PlanType
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, TYPE_CHECKING

from app.schemas.user import UserCreate, UserSchema, UserUpdate
from app.services import user_services

if TYPE_CHECKING:
    from app.models.user import Users
from app.models.enums import Roles

router = APIRouter()

#Devuelve mi usuario
@router.get("/mi-usuario", response_model=UserSchema)
async def return_my_user(
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    return current_user

#Devuelve todos los usuarios
@router.get("/", response_model=list[UserSchema])
async def return_all_users(
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.ADMIN:
        return user_services.get_all_users(db)
    if current_user.role == Roles.COMPANY:
        return user_services.get_all_users_by_tenant_id(db, current_user.tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

#Devueve un usuario por id
@router.get("/{user_id}", response_model=UserSchema)
async def return_user_by_id(
    user_id: UUID,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):        
    if current_user.role == Roles.COMPANY:
        user_to_return = user_services.get_user_by_id(db, user_id)
        if user_to_return.tenant_id == current_user.tenant_id:
            return user_to_return
        else:
            raise HTTPException(
                status_code =403,
                detail= "Solo puedes ver usuarios de tu tenant"
            )
    if current_user.role == Roles.ADMIN:
        return user_services.get_user_by_id(db, user_id)
    raise HTTPException(
            status_code =403,
            detail= "No cuentas con los permisos para acceder a esta ruta"
        )

#Crea un usuario
@router.post("/", response_model=UserSchema)
async def new_user(
    user_data: UserCreate,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.ADMIN:
        return user_services.create_user(db, user_data)
    if current_user.role == Roles.COMPANY:
        candidate_to_create = user_services.create_user(db, user_data)
        if candidate_to_create.tenant_id == current_user.tenant_id:
            return candidate_to_create
        else:
            raise HTTPException(
                status_code =403,
                detail= "Solo puedes crear usuarios de tu tenant"
            )
    raise HTTPException(
        status_code =403,
        detail= "No cuentas con los permisos para acceder a esta ruta"
    )

#Actualiza un usuario
@router.put("/{user_id}", response_model=UserSchema)
async def modify_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == Roles.ADMIN:
        return user_services.update_user(db, user_id, user_data)
    if current_user.role == Roles.COMPANY:
        user_to_update = user_services.get_user_by_id(db, user_id)
        if user_to_update.tenant_id == current_user.tenant_id:
            return user_services.update_user(db, user_id, user_data)
        else:
            raise HTTPException(
                status_code =403,
                detail= "Solo puede actualizar usuarios de tu tenant"
            )
    raise HTTPException(
        status_code =403,
        detail= "No cuentas con los permisos para acceder a esta ruta"
    )

#Borra un usuario
@router.delete("/{user_id}", response_model=None)
async def remove_user(
    user_id: UUID,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.ADMIN:
        return user_services.delete_user(db, user_id)
    if current_user.role == Roles.COMPANY:
        user_to_delete = user_services.get_user_by_id(db, user_id)
        if user_to_delete.tenant_id == current_user.tenant_id:
            return user_services.delete_user(db, user_id)
        else:
            raise HTTPException(
                status_code =403,
                detail= "Solo puedes eliminar usuarios de tu tenant"
            )
    raise HTTPException(
        status_code =403,
        detail= "No cuentas con los permisos para acceder a esta ruta"
    )

#Desactiva un usuario
@router.patch("/desactivar/{user_id}", response_model=UserSchema)
async def disable_user(
    user_id: UUID,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.ADMIN:
        return user_services.disable_user(db, user_id)
    if current_user.role == Roles.COMPANY:
        user_to_disable = user_services.get_user_by_id(db, user_id)
        if user_to_disable.tenant_id == current_user.tenant_id:
            return user_services.disable_user(db, user_id)
        else:
            raise HTTPException(
                status_code =403,
                detail= "Solo puedes desactivar usuarios de tu tenant"
            )
    raise HTTPException(
        status_code =403,
        detail= "No cuentas con los permisos para acceder a esta ruta"
    )
#Activa un usuario
@router.patch("/activar/{user_id}", response_model=UserSchema)
async def enable_user(
    user_id: UUID,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.ADMIN:
        return user_services.enable_user(db, user_id)
    if current_user.role == Roles.COMPANY:
        user_to_enable = user_services.get_user_by_id(db, user_id)
        if user_to_enable.tenant_id == current_user.tenant_id:
            return user_services.enable_user(db, user_id)
        else:
            raise HTTPException(
                status_code =403,
                detail= "Solo puedes activar usuarios de tu tenant"
            )
    raise HTTPException(
        status_code =403,
        detail= "No cuentas con los permisos para acceder a esta ruta"
    )




