from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from app.models.payments import Payments
from app.models.enums import PaymentStatus, PaymentType
from app.schemas.payments import PaymentCreate
from app.services import tenant_services
from fastapi import HTTPException
from app.utils.pagination import paginate

# create_payment - COMPANY
async def create_payment(
    db: AsyncSession,
    payment_in: PaymentCreate,
    tenant_id: UUID
):
    try:
        new_payment = Payments(**payment_in.model_dump(), tenant_id=tenant_id)
        new_payment.status = PaymentStatus.PENDING
        db.add(new_payment)
        await db.commit()
        await db.refresh(new_payment)
        tenant = await tenant_services.get_tenant(db, tenant_id)
        if not tenant.grace_period_used:
            await tenant_services.extend_subscription(db, tenant_id, days = 3)
            tenant.grace_period_used = True
            await db.commit()
        return new_payment
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
#my_payments - COMPANY
async def my_payments(
    db: AsyncSession,
    tenant_id: UUID,
    skip: int = 0,
    limit: int = 10
):
    try:
        query = select(Payments).where(Payments.tenant_id == tenant_id)
        payments = await db.execute(paginate(query, skip, limit))
        return payments.scalars().all()
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
#cancel_payment - COMPANY
async def cancel_payment(
    db: AsyncSession,
    payment_id: UUID,
    tenant_id: UUID
):
    try:
        payment = await get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        if payment.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Solo puedes cancelar tus propios pagos")
        if payment.status != PaymentStatus.PENDING:
            raise HTTPException(status_code=400, detail="Solo puedes cancelar pagos pendientes")
        payment.status = PaymentStatus.CANCELED
        await db.commit()
        await db.refresh(payment)
        return payment
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
#verify_payment - ADMIN
async def verify_payment(
    db: AsyncSession,
    payment_id: UUID,
    verification_status: PaymentStatus
):
    try:
        if verification_status != PaymentStatus.APPROVED and verification_status != PaymentStatus.REJECTED:
            raise HTTPException(status_code=400, detail="Estado de verificación no válido")
        payment = await get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        payment.status = verification_status
        tenant = await tenant_services.get_tenant(db, payment.tenant_id)
        if verification_status == PaymentStatus.APPROVED:
            if payment.type == PaymentType.PAGO_MENSUAL:
                await tenant_services.extend_subscription(db, payment.tenant_id, months=1)
                await tenant_services.extend_subscription(db, payment.tenant_id, days=-3)
                
            elif payment.type == PaymentType.PAGO_ANUAL:
                await tenant_services.extend_subscription(db, payment.tenant_id, months=12)
                await tenant_services.extend_subscription(db, payment.tenant_id, days=-3)
            tenant.grace_period_used = False
            await db.commit()
            await db.refresh(payment)
        return payment
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# get_payments - ADMIN
async def get_payments(db: AsyncSession, skip: int = 0, limit: int = 10):
    try:
        query = select(Payments)
        payments = await db.execute(paginate(query, skip, limit))
        return payments.scalars().all()
    except Exception as e:
        await db.rollback()
        raise e   

# get_payment_by_id - ADMIN
async def get_payment_by_id(db: AsyncSession, payment_id: UUID):
    try:
        payment = await db.get(Payments, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        return payment
    except SQLAlchemyError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

