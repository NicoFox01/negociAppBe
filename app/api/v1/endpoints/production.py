from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.enums import Roles
from app.models.user import Users
from app.schemas.production import ProductionTransformCreate, ProductionTransformSchema
from app.services import production_service

router = APIRouter()


@router.post("/transform", response_model=ProductionTransformSchema)
async def create_transform(
    transform_data: ProductionTransformCreate,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="No tienes permisos")

    return await production_service.create_transform(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        transform_data=transform_data
    )


@router.get("/transforms", response_model=List[ProductionTransformSchema])
async def get_transforms(
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="No tienes permisos")

    return await production_service.get_transforms(
        db=db,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )


@router.get("/transforms/{transform_id}", response_model=ProductionTransformSchema)
async def get_transform_by_id(
    transform_id: UUID,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="No tienes permisos")

    transform = await production_service.get_transform_by_id(
        db=db,
        transform_id=transform_id,
        tenant_id=current_user.tenant_id
    )

    if not transform:
        raise HTTPException(status_code=404, detail="Transformación no encontrada")

    return transform
