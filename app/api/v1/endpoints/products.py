from uuid import UUID
from app.api.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, TYPE_CHECKING

from app.schemas.products import ProductsCreate, ProductsSchema, ProductsUpdate
from app.services import product_services

if TYPE_CHECKING:
    from app.models.user import Users
from app.models.enums import Roles

router = APIRouter()

@router.get("/", response_model=ProductsSchema)
async def return_all_products(
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    Allowed_roles = {
        Roles.COMPANY,
        Roles.EMPLOYEE
    }
    if current_user.role in Allowed_roles:
        tenant_id = current_user.tenant_id
        return await product_services.get_products(db, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.get("/{product_id}", response_model=ProductsSchema)
async def return_product_by_id(
    current_user: Annotated["Users", Depends(get_current_user)],
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    Allowed_roles = {
        Roles.COMPANY,
        Roles.EMPLOYEE
    }
    if current_user.role in Allowed_roles:
        tenant_id = current_user.tenant_id
        return await product_services.get_product_by_id(db, product_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.get("/{supplier_id}", response_model=ProductsSchema)
async def return_products_by_suppliers(
    current_user: Annotated["Users", Depends(get_current_user)],
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await product_services.get_products_by_supplier(db, tenant_id, supplier_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.post("/", response_model=ProductsCreate)
async def new_product(
    current_user: Annotated["Users", Depends(get_current_user)],
    product_data:ProductsCreate,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await product_services.create_product(db,product_data, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.patch("/{product_id}", response_model=ProductsUpdate)
async def modify_product(
    current_user: Annotated["Users", Depends(get_current_user)],
    product_id: UUID,
    product_data:ProductsUpdate,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await product_services.update_product(db, product_data,product_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )
@router.delete("/{product_id}", response_model=None)
async def remove_product(
    current_user: Annotated["Users", Depends(get_current_user)],
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await product_services.delete_product(db, product_id, tenant_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )

@router.delete("/{supplier_id}", response_model=None)
async def remove_all_product_for_supplier(
    current_user: Annotated["Users", Depends(get_current_user)],
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == Roles.COMPANY:
        tenant_id = current_user.tenant_id
        return await product_services.delete_all_products_by_supplier(db, tenant_id, supplier_id)
    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta ruta"
        )