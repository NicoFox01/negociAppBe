from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.products import Product
from app.schemas.products import ProductsCreate,  ProductsUpdate
from app.services.supplier_services import get_supplier_by_id

async def create_product(db:AsyncSession, product_data:ProductsCreate, tenant_id:UUID)->Product:
    try:
        new_product = Product(**product_data.model_dump())
        new_product.tenant_id = tenant_id
        await db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return new_product
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_products(db:AsyncSession, tenant_id: UUID) ->List[Product]:
    try:
        result = await db.execute(select(Product).where(Product.tenant_id == tenant_id))
        return result.scalars().all()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_products_by_supplier(db:AsyncSession, tenant_id: UUID, supplier_id:UUID) ->List[Product]:
    try:
        result = await db.execute(select(Product).where(
            Product.tenant_id == tenant_id,
            Product.supplier_id == supplier_id
            ))
        return result.scalars().all()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_product_by_id(db:AsyncSession, product_id: UUID, tenant_id:UUID)->Product:
    try:
        result = await db.execute(select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
            ))
        return result.scalars().first()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_product(db:AsyncSession, product_data:ProductsUpdate, product_id:UUID, tenant_id: UUID) -> Optional[Product]:
    try:
        product_to_update = await get_product_by_id(db, product_id, tenant_id)
        if not product_to_update:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product_to_update, field, value)

        await db.add(product_to_update)
        await db.commit()
        await db.refresh(product_to_update)
        return product_to_update
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def delete_product(db:AsyncSession, product_id:UUID, tenant_id:UUID)-> None:
    try:
        product_to_delete = await get_product_by_id(db, product_id, tenant_id)
        if not product_to_delete:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        await db.delete(product_to_delete)
        await db.commit()
        return {"message": "Producto eliminado correctamente"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def delete_all_products_by_supplier(db:AsyncSession, tenant_id:UUID, supplier_id:UUID) -> None:
    try:
        supplier = await get_supplier_by_id(db, supplier_id, tenant_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        list_of_products_to_delete = await get_products_by_supplier(db, tenant_id, supplier_id)
        if not list_of_products_to_delete:
            raise HTTPException(status_code=404, detail="No hay productos asociados al proveedor")
        for product in list_of_products_to_delete:
            await db.delete(product)
        await db.commit()
        return {"message": "productos eliminados correctamente"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))