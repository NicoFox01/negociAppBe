from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.products import Product
from app.schemas.products import ProductsCreate,  ProductsUpdate
from app.services.supplier_services import get_supplier_by_id

import re

from app.utils.pagination import paginate


async def generate_sku(db: AsyncSession, tenant_id: UUID, name: str) -> str:
    # 1. Generate Prefix
    cleaned_name = re.sub(r'[^a-zA-Z]', '', name)
    prefix = (cleaned_name[:3] if len(cleaned_name) >= 3 else cleaned_name).upper()
    if len(prefix) < 3:
        prefix = (prefix + "XXX")[:3]
    
    # 2. Find similar SKUs
    # Look for SKUs starting with PREFIX-
    query = select(Product.sku).where(
        Product.tenant_id == tenant_id,
        Product.sku.like(f"{prefix}-%")
    )
    result = await db.execute(query)
    existing_skus = result.scalars().all()
    
    # 3. Determine Max Number
    max_num = 0
    for sku in existing_skus:
        # Expected format: AAA-001
        parts = sku.split('-')
        if len(parts) == 2 and parts[0] == prefix and parts[1].isdigit():
            num = int(parts[1])
            if num > max_num:
                max_num = num
    
    # 4. Return new SKU
    next_num = max_num + 1
    return f"{prefix}-{next_num:03d}"

async def create_product(db:AsyncSession, product_data:ProductsCreate, tenant_id:UUID)->Product:
    try:
        # Auto-generate SKU if missing
        sku_value = product_data.sku
        if not sku_value:
            try:
                sku_value = await generate_sku(db, tenant_id, product_data.name)
            except Exception as sku_error:
                print(f"Error generating SKU: {sku_error}")
                sku_value = f"PROD-{product_data.name[:3].upper()}-{tenant_id.hex[:6]}"

        # Create product dict with proper types
        product_dict = product_data.model_dump()
        product_dict['sku'] = sku_value
        product_dict['tenant_id'] = tenant_id
        
        new_product = Product(**product_dict)
        db.add(new_product)
        await db.flush()
        await db.commit()
        
        # Refresh only the columns, not relationships
        await db.refresh(new_product, attribute_names=['id', 'sku', 'name', 'unit', 'base_price', 'cost_price', 'stock_quantity', 'is_raw_material', 'expiration_date', 'supplier_id', 'tenant_id'])
        
        return new_product
    except SQLAlchemyError as db_err:
        await db.rollback()
        print(f"Database error: {db_err}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(db_err)}")
    except Exception as e:
        await db.rollback()
        print(f"Create product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_products(db:AsyncSession, tenant_id: UUID, skip: int=0, limit: int = 10) ->List[Product]:
    try:
        query = select(Product).where(Product.tenant_id == tenant_id)
        result = await db.execute(paginate(query, skip, limit))
        return result.scalars().all()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_products_by_supplier(db:AsyncSession, tenant_id: UUID, supplier_id:UUID, skip: int=0, limit: int = 10) ->List[Product]:
    try:
        query = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.supplier_id == supplier_id
            )
        result = await db.execute(paginate(query, skip, limit))
        return result.scalars().all()
    except SQLAlchemyError:
        await db.rollback()
        raise
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
    except SQLAlchemyError:
        await db.rollback()
        raise
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

        await db.commit()
        await db.refresh(product_to_update)
        return product_to_update
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

async def delete_product(db:AsyncSession, product_id:UUID, tenant_id:UUID)-> None:
    try:
        product_to_delete = await get_product_by_id(db, product_id, tenant_id)
        if not product_to_delete:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        await db.delete(product_to_delete)
        await db.commit()
        return {"message": "Producto eliminado correctamente"}
    except SQLAlchemyError:
        await db.rollback()
        raise
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