from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.suppliers import Supplier
from app.schemas.suppliers import SuppliersCreate, SuppliersUpdate

async def create_supplier(db:AsyncSession, supplier_data:SuppliersCreate, tenant_id:UUID)->Supplier:
    try:
        new_supplier = Supplier(**supplier_data.model_dump())
        new_supplier.tenant_id = tenant_id
        await db.add(new_supplier)
        await db.commit()
        await db.refresh(new_supplier)
        return new_supplier
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_suppliers(db:AsyncSession, tenant_id:UUID) ->List[Supplier]:
    try:
        result = await db.execute(select(Supplier).where(Supplier.tenant_id == tenant_id))
        return result.scalars().all()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_supplier_by_id(db:AsyncSession, supplier_id: UUID, tenant_id:UUID) -> Optional[Supplier]:
    try:
        result = await db.execute(select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.tenant_id == tenant_id
            ))
        return result.scalars().first()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_supplier(db:AsyncSession, supplier_data:SuppliersUpdate, supplier_id: UUID, tenant_id:UUID) -> Supplier:
    try:
        supplier_to_update = await get_supplier_by_id(db, supplier_id,tenant_id)
        if not supplier_to_update:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        update_data = supplier_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier_to_update, field, value)

        await db.add(supplier_to_update)
        await db.commit()
        await db.refresh(supplier_to_update)
        return supplier_to_update
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def delete_supplier(db:AsyncSession, supplier_id: UUID, tenant_id:UUID) ->dict:
    try:
        supplier_to_delete = await get_supplier_by_id(db, supplier_id,tenant_id)
        if not supplier_to_delete:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        await db.delete(supplier_to_delete)
        await db.commit()
        return {"message": "Proveedor eliminado correctamente"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

