from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.payments import Payments
from app.models.enums import PaymentStatus, PaymentType
from app.schemas.payments import PaymentCreate
from app.services import tenant_services
from fastapi import HTTPException

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
        await tenant_services.extend_subscription(db, tenant_id, 3)
        return new_payment
    except Exception as e:
        await db.rollback()
        raise e
#my_payments - COMPANY
async def my_payments(
    db: AsyncSession,
    tenant_id: UUID
):
    try:
        payments = await db.execute(select(Payments).where(Payments.tenant_id == tenant_id))
        return payments.scalars().all()
    except Exception as e:
        await db.rollback()
        raise e
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
    except Exception as e:
        await db.rollback()
        raise e
    
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
        if verification_status == PaymentStatus.APPROVED:
            if payment.type == PaymentType.PAGO_MENSUAL:
                await tenant_services.extend_subscription(db, payment.tenant_id, months=1)
            elif payment.type == PaymentType.PAGO_ANUAL:
                await tenant_services.extend_subscription(db, payment.tenant_id, months=12)
        await db.commit()
        await db.refresh(payment)
        return payment
    except Exception as e:
        await db.rollback()
        raise e

# get_payments - ADMIN
async def get_payments(db: AsyncSession):
    try:
        payments = await db.execute(select(Payments))
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
    except Exception as e:
        await db.rollback()
        raise e
