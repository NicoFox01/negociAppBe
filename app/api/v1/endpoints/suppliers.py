from uuid import UUID
from app.api.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, TYPE_CHECKING

from app.schemas.suppliers import SuppliersCreate, SuppliersSchema, SuppliersUpdate
from app.services import supplier_services, product_services

if TYPE_CHECKING:
    from app.models.user import Users
from app.models.enums import Roles

router = APIRouter()

@router.get("/", response_model=SuppliersSchema)
async def return_all_suppliers(
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await supplier_services.get_suppliers(db, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )
@router.get("/{supplier_id}", response_model=SuppliersSchema)
async def return_supplier_by_id(
    current_user: Annotated["Users", Depends(get_current_user)],
    supplier_id:UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await supplier_services.get_supplier_by_id(db,supplier_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.post("/", response_model=SuppliersCreate)
async def new_supplier(
    current_user: Annotated["Users", Depends(get_current_user)],
    supplier_data:SuppliersCreate,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await supplier_services.create_supplier(db,supplier_data, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )
@router.patch("/{supplier_id}", response_model=SuppliersUpdate)
async def modify_supplier(
    current_user: Annotated["Users", Depends(get_current_user)],
    supplier_id: UUID,
    supplier_data:SuppliersCreate,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await supplier_services.update_supplier(db, supplier_data,supplier_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )
@router.delete("/{supplier_id}", response_model=None)
async def remove_supplier(
    current_user: Annotated["Users", Depends(get_current_user)],
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db) 
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        products = await product_services.get_products_by_supplier(db, tenant_id, supplier_id)
        if products:
             raise HTTPException(
                status_code=400,
                detail="No se puede eliminar el proveedor porque tiene productos asociados. Elimine o reasigne los productos primero."
            )
        return await supplier_services.delete_supplier(db, supplier_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )