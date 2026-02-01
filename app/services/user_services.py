from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.user import Users
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.models.enums import Roles

async def get_by_username(db: AsyncSession, username: str):
    try:
        result = await db.execute(select(Users).where(Users.username == username))
        return result.scalars().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_by_id(db: AsyncSession, user_id: UUID):
    try:
        result = await db.execute(select(Users).where(Users.id == user_id))
        return result.scalars().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_user(db: AsyncSession, user_data: UserCreate) -> Users:
    try:
        # 1. Validar si ya existe (Eficiente: SELECT 1)
        existing_user = await get_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

        # 2. Hashear password
        hashed_pw = get_password_hash(user_data.password)

        # 3. Crear usando model_dump
        db_obj = Users(
            **user_data.model_dump(exclude={"password"}), # Excluimos pass plano
            hashed_password=hashed_pw
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except Exception as e:
        await db.rollback()
        raise e

async def update_user(db: AsyncSession, user_id: UUID, user_update: UserUpdate) -> Users:
    try:
        user = await get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        raise e

async def delete_user(db: AsyncSession, user_id: UUID):
    try:
        user = await get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        await db.delete(user)
        await db.commit()
        return {"message": "Usuario eliminado correctamente"}
    except Exception as e:
        await db.rollback()
        raise

async def disable_user(db: AsyncSession, user_id: UUID):
    try:
        user = await get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
        user.is_active = False
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        raise

async def enable_user(db: AsyncSession, user_id: UUID):
    try:
        user = await get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
        user.is_active = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        raise

async def get_all_users(db: AsyncSession):
    try:
        result = await db.execute(select(Users))
        return result.scalars().all()
    except Exception as e:
        await db.rollback()
        raise

async def get_all_users_by_tenant_id(db: AsyncSession, tenant_id: UUID):
    try:
        result = await db.execute(select(Users).where(Users.tenant_id == tenant_id))
        return result.scalars().all()
    except Exception as e:
        await db.rollback()
        raise

async def change_password(db: AsyncSession, user_id: UUID, current_password: str, new_password: str):
    try:
        user = await get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"message": "Contraseña actualizada correctamente"}
    except Exception as e:
        await db.rollback()
        raise e

async def reset_password(db: AsyncSession, current_user: Users, target_user_id: UUID, new_password: str):
    try:
        target_user = await get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario destino no encontrado")
        if current_user.role == Roles.COMPANY:
            if target_user.tenant_id != current_user.tenant_id:
                raise HTTPException(status_code=403, detail="No puedes modificar usuarios de otra empresa")
            if target_user.role != Roles.EMPLOYEE:
                raise HTTPException(status_code=403, detail="Solo puedes resetear contraseñas de empleados")
        elif current_user.role == Roles.ADMIN:
            pass
        else:
            raise HTTPException(status_code=403, detail="No tienes permisos para realizar esta acción")
        target_user.hashed_password = get_password_hash(new_password)
        db.add(target_user)
        await db.commit()
        await db.refresh(target_user)
        return {"message": "Contraseña reseteada correctamente"}
    except Exception as e:
        await db.rollback()
        raise e
