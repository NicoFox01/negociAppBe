from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.models.requests import PurchaseRequest, PurchaseRequestItem
from app.models.products import Product
from app.models.enums import PurchaseRequestStatus, Roles
from app.schemas.requests import RequestCreate, RequestUpdate, RequestSchema
from app.utils.pagination import paginate


async def create_request(
    db: AsyncSession, 
    request_data: RequestCreate, 
    user_id: UUID, 
    tenant_id: UUID
) -> PurchaseRequest:
    try:
        new_request = PurchaseRequest(
            tenant_id=tenant_id,
            user_id=user_id,
            status=PurchaseRequestStatus.PENDING
        )
        db.add(new_request)
        await db.flush()
        for item in request_data.items:
            new_item = PurchaseRequestItem(
                request_id=new_request.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.add(new_item)
        await db.commit()
        await db.refresh(new_request)
        return new_request
        
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_requests(
    db: AsyncSession, 
    tenant_id: UUID,
    skip: int = 0,
    limit: int = 10,
    status: Optional[PurchaseRequestStatus] = None
) -> List[PurchaseRequest]:
    try:
        query = select(PurchaseRequest).where(PurchaseRequest.tenant_id == tenant_id)
        if status:
            query = query.where(PurchaseRequest.status == status)
        
        query = query.options(
            joinedload(PurchaseRequest.items)
            .joinedload(PurchaseRequestItem.product)
            .joinedload(Product.supplier)
        ).order_by(PurchaseRequest.created_at.desc())

        result = await db.execute(paginate(query, skip, limit))
        return result.scalars().unique().all()
    except SQLAlchemyError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_request_by_id(
    db: AsyncSession, 
    request_id: UUID, 
    tenant_id: UUID
) -> Optional[PurchaseRequest]:
    try:
        query = select(PurchaseRequest).where(
            PurchaseRequest.id == request_id, 
            PurchaseRequest.tenant_id == tenant_id
        ).options(
            joinedload(PurchaseRequest.items)
            .joinedload(PurchaseRequestItem.product)
            .joinedload(Product.supplier)
        )
        
        result = await db.execute(query)
        return result.scalars().unique().first()
    except SQLAlchemyError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_request(
    db: AsyncSession, 
    request_id: UUID, 
    tenant_id: UUID
) -> dict:
    try:
        request = await get_request_by_id(db, request_id, tenant_id)
        if not request:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        # Validation: Only PENDING can be deleted
        if request.status != PurchaseRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="No se puede eliminar una solicitud que no esté PENDING")

        await db.delete(request)
        await db.commit()
        return {"message": "Solicitud eliminada correctamente"}
        
    except SQLAlchemyError:
        await db.rollback()
        raise
    except HTTPException as he:
        await db.rollback()
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_request_status(
    db: AsyncSession, 
    request_id: UUID, 
    tenant_id: UUID, 
    new_status: PurchaseRequestStatus,
) -> PurchaseRequest:
    try:
        request = await get_request_by_id(db, request_id, tenant_id)
        if not request:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        if request.status != PurchaseRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Solo se pueden actualizar solicitudes Pendientes")
        
        request.status = new_status
        await db.commit()
        await db.refresh(request)
        return request
        
    except SQLAlchemyError:
        await db.rollback()
        raise
    except HTTPException as he:
        await db.rollback()
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
