from uuid import UUID
from app.api.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, TYPE_CHECKING, List, Optional

from app.schemas.requests import RequestItemCreate, RequestItemSchema, RequestCreate, RequestSchema, RequestUpdate
from app.services import request_service

if TYPE_CHECKING:
    from app.models.user import Users
from app.models.enums import Roles, PurchaseRequestStatus

router = APIRouter()

@router.get("/", response_model=List[RequestSchema])
async def return_all_request(
    current_user: Annotated["Users", Depends(get_current_user)],
    status: Optional[PurchaseRequestStatus],
    db: AsyncSession = Depends(get_db)
):
    allowed_roles = {
        Roles.EMPLOYEE,
        Roles.COMPANY
    }
    if current_user.role in allowed_roles:
        tenant_id = current_user.tenant_id
        return await request_service.get_requests(db, tenant_id, status)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.get("/{request_id}", response_model=RequestSchema)
async def return_request_by_id(
    current_user: Annotated["Users", Depends(get_current_user)],
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    allowed_roles = {
        Roles.EMPLOYEE,
        Roles.COMPANY
    }
    if current_user.role in allowed_roles:
        tenant_id = current_user.tenant_id
        return await request_service.get_request_by_id(db, request_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )
@router.post("/", response_model=RequestSchema)
async def new_request(
    current_user: Annotated["Users", Depends(get_current_user)],
    request_data: RequestCreate,
    db: AsyncSession = Depends(get_db)
):
    allowed_roles = {
        Roles.EMPLOYEE,
        Roles.COMPANY
    }
    if current_user.role in allowed_roles:
        return await request_service.create_request(
            db, 
            request_data, 
            current_user.id, 
            current_user.tenant_id
        )
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.patch("/{request_id}/{status}", response_model=RequestUpdate)
async def modify_request(
    current_user: Annotated["Users", Depends(get_current_user)],
    request_id:UUID,
    status: PurchaseRequestStatus,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        request = await request_service.get_request_by_id(db, request_id, tenant_id)
        finally_status = {
            PurchaseRequestStatus.APPROVED,
            PurchaseRequestStatus.CANCELED,
            PurchaseRequestStatus.REJECTED
        }
        if request.status in finally_status:
            raise HTTPException(status_code=404, detail="No se puede modificar el estado presente")
        if status == PurchaseRequestStatus.PENDING:
            raise HTTPException(status_code=404, detail="Se debe elegir un status diferente a pendiente")
        return await request_service.update_request_status(db, request_id, tenant_id, status)
    if current_user.role == Roles.EMPLOYEE:
        tenant_id = current_user.tenant_id
        request = await request_service.get_request_by_id(db, request_id, tenant_id)
        if request.status == PurchaseRequestStatus.PENDING:
            return await request_service.update_request_status(db, request_id, tenant_id, status)
        else:
            raise HTTPException(status_code=404, detail="No se puede cambiar el stado de una request ya evaluada")
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.delete("/{request_id}", response_model=None)
async def remove_request(
    current_user: Annotated["Users", Depends(get_current_user)],
    request_id:UUID,
    db: AsyncSession = Depends(get_db)
):
    allowed_roles = {
        Roles.EMPLOYEE,
        Roles.COMPANY
    }
    if current_user.role in allowed_roles:
        tenant_id = current_user.tenant_id
        request = await request_service.get_request_by_id(db, request_id, tenant_id)
        if request.status != PurchaseRequestStatus.PENDING:
            raise HTTPException(status_code=404, detail="no se pueden eliminar request tramitadas")
        return await request_service.delete_request(db, request_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )