from uuid import UUID
from datetime import timedelta, date
import calendar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.tenant import Tenants
from app.models.user import Users
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.schemas.user import UserCreate
from app.models.enums import Roles
from app.core.security import get_password_hash

async def get_all_tenants(db: AsyncSession):
    try:
        result = await db.execute(select(Tenants))
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_tenant(db: AsyncSession, tenant_id: UUID):
    try:
        result = await db.execute(select(Tenants).where(Tenants.id == tenant_id))
        return result.scalars().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_tenant_with_admin(db: AsyncSession, tenant_data: TenantCreate, admin_user_data: UserCreate) -> Tenants:
    # Inicio de Transacción Atómica implícita en AsyncSession
    try:
        # 1. Crear Empresa
        new_tenant = Tenants(**tenant_data.model_dump())
        db.add(new_tenant)
        await db.flush() # Para obtener el ID del tenant antes del commit

        # 2. Preparar Usuario Admin (Vinculado al Tenant)
        # Verificamos duplicado de usuario aquí también por seguridad
        q = await db.execute(select(Users).where(Users.username == admin_user_data.username))
        if q.scalars().first():
            raise HTTPException(status_code=400, detail="El usuario ya existe")

        hashed_pw = get_password_hash(admin_user_data.password)
        
        new_admin = Users(
            tenant_id=new_tenant.id,
            username=admin_user_data.username,
            full_name=admin_user_data.full_name,
            role=Roles.COMPANY, # <--- FIXED: COMPANY role for Tenant Owner
            hashed_password=hashed_pw
        )
        db.add(new_admin)

        await db.commit()
        await db.refresh(new_tenant)
        return new_tenant

    except Exception as e:
        await db.rollback()
        raise e

async def update_tenant(db: AsyncSession, tenant_id: UUID, tenant_update: TenantUpdate):
    try:
        tenant = await get_tenant(db, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")

        update_data = tenant_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant
    except Exception as e:
        await db.rollback()
        raise e

async def delete_tenant(db: AsyncSession, tenant_id: UUID):
    try:
        tenant = await get_tenant(db, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        await db.delete(tenant)
        await db.commit()
        return {"message": "Empresa eliminada correctamente"}
    except Exception as e:
        await db.rollback()
        raise e

async def deactivate_tenant(db: AsyncSession, tenant_id: UUID):
    try:
        tenant = await get_tenant(db, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
        tenant.is_active = False # Baja Lógica
        db.add(tenant)
        await db.commit()
        return tenant
    except Exception as e:
        await db.rollback()
        raise e

async def activate_tenant(db: AsyncSession, tenant_id: UUID):
    try:
        tenant = await get_tenant(db, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
        tenant.is_active = True
        db.add(tenant)
        await db.commit()
        return tenant
    except Exception as e:
        await db.rollback()
        raise e

def add_months(source_date: date, months: int) -> date:
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

async def extend_subscription(db: AsyncSession, tenant_id: UUID, days: int = 0, months: int = 0):
    try: 
        tenant = await get_tenant(db, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        current_end = tenant.subscription_end
        base_date = current_end if current_end and current_end >= date.today() else date.today()
        
        if months > 0:
            new_end_date = add_months(base_date, months)
        else:
            new_end_date = base_date + timedelta(days=days)

        tenant.subscription_end = new_end_date
        
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant
    except Exception as e:
        await db.rollback()
        raise e