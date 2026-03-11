from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from app.models.production import ProductionTransform, ProductionTransformInput, ProductionTransformOutput
from app.models.products import Product
from app.models.inventory import InventoryTransaction
from app.models.enums import TransactionType
from app.schemas.production import ProductionTransformCreate, ProductionTransformSchema
from app.utils.pagination import paginate

async def create_transform(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    transform_data: ProductionTransformCreate
) -> ProductionTransformSchema:
    try:
        new_transform = ProductionTransform(
            tenant_id=tenant_id,
            user_id=user_id
        )
        db.add(new_transform)
        await db.flush()
        # Procesamiento de inputs
        for item in transform_data.inputs:
            # Se bloquea el producto durante la transacción
            query = select(Product).with_for_update().where(
                Product.id == item.product_id,
                Product.tenant_id == tenant_id
            )
            result = await db.execute(query)
            product = result.scalars().first()

            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Producto input no encontrado"
                )
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para {product.name}. "
                           f"Disponible: {product.stock_quantity}, necesario: {item.quantity}"
                )
            product.stock_quantity -= item.quantity

            # Se crea una transacción de tipo salida
            transaction = InventoryTransaction(
                tenant_id=tenant_id,
                product_id=item.product_id,
                transaction_type=TransactionType.OUT,
                quantity=item.quantity,
                reference_id=new_transform.id
            )
            db.add(transaction)

            # Guardamos el input
            transform_input = ProductionTransformInput(
                transform_id=new_transform.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.add(transform_input)
        # Procesamiento de outputs
        for item in transform_data.outputs:
            # Se bloquea el producto durante la transacción
            query = select(Product).with_for_update().where(
                Product.id == item.product_id,
                Product.tenant_id == tenant_id
            )
            result = await db.execute(query)
            product = result.scalars().first()

            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Producto output no encontrado"
                )
            product.stock_quantity += item.quantity

            # Se crea una transacción de tipo entrada
            transaction = InventoryTransaction(
                tenant_id=tenant_id,
                product_id=item.product_id,
                transaction_type=TransactionType.IN,
                quantity=item.quantity,
                reference_id=new_transform.id
            )
            db.add(transaction)
            # Guardar output
            transform_output = ProductionTransformOutput(
                transform_id=new_transform.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.add(transform_output)

        await db.commit()
        await db.refresh(new_transform)
        # Se crean relaciones para guardar completo
        query = select(ProductionTransform).where(
            ProductionTransform.id == new_transform.id
        ).options(
            joinedload(ProductionTransform.inputs).joinedload(ProductionTransformInput.product),
            joinedload(ProductionTransform.outputs).joinedload(ProductionTransformOutput.product)
        )
        result = await db.execute(query)
        return result.scalars().unique().first()
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_transforms(
        db: AsyncSession,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 10
) -> List[ProductionTransformSchema]:
    try:
        query = (select(ProductionTransform)
                 .where(ProductionTransform.tenant_id == tenant_id)
        .options(
            joinedload(ProductionTransform.inputs).joinedload(ProductionTransformInput.product),
            joinedload(ProductionTransform.outputs).joinedload(ProductionTransformOutput.product)
        ))
        result = await db.execute(paginate(query, skip, limit))
        return result.scalars().unique().all()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_transform_by_id(
        db: AsyncSession,
        transform_id: UUID,
        tenant_id: UUID
) -> Optional[ProductionTransformSchema]:
    try:
        query = (select(ProductionTransform)
                 .where(ProductionTransform.tenant_id == tenant_id,
                        ProductionTransform.id == transform_id)
        .options(
            joinedload(ProductionTransform.inputs).joinedload(ProductionTransformInput.product),
            joinedload(ProductionTransform.outputs).joinedload(ProductionTransformOutput.product)
        ))
        result = await db.execute(query)
        return result.scalars().unique().first()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))