from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from app.api.deps import get_current_user, get_db
from app.core.security import verify_password
from app.models.enums import Roles, PaymentStatus, PaymentType
from app.schemas.payments import PaymentCreate, PaymentSchema
from app.services import payments_services, storage_services, user_services
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.enums import Roles
from typing import Annotated, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import Users

router = APIRouter()

@router.post("/", response_model=PaymentSchema)
async def new_payment(
    current_user: Annotated["Users", Depends(get_current_user)],
    file: UploadFile = File(...),
    amount: float = Form(...),
    payment_period: date = Form(...),
    type: PaymentType = Form(...),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != Roles.COMPANY:
        raise HTTPException(status_code=403, detail="Solo los responsables de la empresa pueden crear pagos")
    tenant_id = current_user.tenant_id
    
    url_payment = await storage_services.upload_payment_proof(file, tenant_id)
    payment_data = PaymentCreate(
        amount=amount,
        type=type,
        payment_period=payment_period,
        proof_url=url_payment,
        tenant_id=tenant_id
    )
    return await payments_services.create_payment(db, payment_data, tenant_id)


@router.post("/notify", response_model=PaymentSchema)
async def notify_payment(
        username: str = Form(...),
        password: str = Form(...),
        file: UploadFile = File(...),
        amount: float = Form(...),
        payment_period: date = Form(...),
        type: PaymentType = Form(...),
        db: AsyncSession = Depends(get_db)
):
    # 1. Validar credenciales (como en login)
    user = await user_services.get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # 2. Verificar rol
    if user.role != Roles.COMPANY:
        raise HTTPException(status_code=403, detail="Solo el responsable puede")
    tenant_id = user.tenant_id

    url_payment = await storage_services.upload_payment_proof(file, tenant_id)
    payment_data = PaymentCreate(
        amount=amount,
        type=type,
        payment_period=payment_period,
        proof_url=url_payment,
        tenant_id=tenant_id
    )
    return await payments_services.create_payment(db, payment_data, tenant_id)

@router.get("/mis-pagos", response_model=List[PaymentSchema])
async def list_of_my_payments(
        current_user: Annotated["Users", Depends(get_current_user)],
        skip: int = 0,
        limit: int = 10,
        db: AsyncSession = Depends(get_db)
):
    if current_user.role != Roles.COMPANY:
        raise HTTPException(status_code=403, detail="Solo los responsables de la empresa pueden ver sus pagos")
    return await payments_services.my_payments(db, current_user.tenant_id, skip, limit)

@router.get("/pagos", response_model=list[PaymentSchema])
async def list_of_payments(
    current_user: Annotated["Users", Depends(get_current_user)],
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != Roles.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permiso para acceder a esta ruta")
    return await payments_services.get_payments(db, skip, limit)

@router.patch("/{payment_id}", response_model=PaymentSchema)
async def verify_payment(
    payment_id: UUID,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    status: PaymentStatus = Form(...)
):
    if current_user.role != Roles.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permiso para acceder a esta ruta")
    return await payments_services.verify_payment(db, payment_id, status)

@router.patch("/cancelar/{payment_id}", response_model=PaymentSchema)
async def cancel_payment(
    payment_id: UUID,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != Roles.COMPANY:
        raise HTTPException(status_code=403, detail="Solo los responsables de la empresa pueden cancelar sus pagos")
    return await payments_services.cancel_payment(db, payment_id, current_user.tenant_id)