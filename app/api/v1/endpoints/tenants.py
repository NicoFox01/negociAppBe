from app.models import PlanType
from datetime import timedelta
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import Users

from app.api.deps import get_current_user, get_db
from app.schemas.tenant import TenantCreate, TenantSchema, TenantUpdate
from app.schemas.user import UserCreate
from app.services import tenant_services
from app.models.tenant import Tenants
from app.models.enums import Roles

router = APIRouter()

#Lista de Tenant - solo Admin
@router.get("/", response_model=List[TenantSchema])
async def return_all_tenants(
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.ADMIN:
        return tenant_services.get_all_tenants(db)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

# Obtener detalles de mi tenant - para COMPANY
@router.get("/mi-empresa", response_model=TenantSchema)
async def return_my_tenant(
    current_user: Annotated["Users",Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        return tenant_services.get_tenant_by_id(db, current_user.tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
    )

# Crear tenant - solo Admin
@router.post("/", response_model=TenantSchema)
async def new_tenant(
    current_user: Annotated["Users",Depends(get_current_user)],
    tenant_data: TenantCreate,
    company_role_data: UserCreate,
    db: AsyncSession = Depends(get_db),

):
    if current_user.role != Roles.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a esta ruta"
        )
    return tenant_services.create_tenant_with_admin(db, tenant_data, company_role_data)

# Actualizar tenant - solo Admin
@router.put("/{tenant_id}", response_model=TenantSchema)
async def modify_tenant(
    current_user: Annotated["Users",Depends(get_current_user)],
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != Roles.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a esta ruta"
        )
    ## si la tenant_id no existe
    tenant_to_update = tenant_services.get_tenant_by_id(db, tenant_id)
    if tenant_to_update is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant no encontrado"
        )
    return tenant_services.update_tenant(db, tenant_id, tenant_data)

# Eliminar tenant - solo Admin
@router.delete("/{tenant_id}", response_model=None)
async def remove_tenant(
    current_user: Annotated["Users",Depends(get_current_user)],
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != Roles.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a esta ruta"
        )
    tenant_services.delete_tenant(db, tenant_id)
    return None
# Activar tenant - solo Admin
@router.patch("/activar/{tenant_id}", response_model=TenantSchema)
async def activate_tenant(
    current_user: Annotated["Users",Depends(get_current_user)],
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != Roles.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a esta ruta"
        )
    tenant_services.activate_tenant(db, tenant_id)
    return tenant_services.get_tenant_by_id(db, tenant_id)
# Desactivar tenant - solo Admin
@router.patch("/desactivar/{tenant_id}", response_model=TenantSchema)
async def deactivate_tenant(
    current_user: Annotated["Users",Depends(get_current_user)],
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != Roles.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a esta ruta"
        )
    tenant_services.deactivate_tenant(db, tenant_id)
    return tenant_services.get_tenant_by_id(db, tenant_id)
