from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.notifications import Notification
from app.models.enums import NotificationStatus, NotificationType, Roles
from app.schemas.notification import NotificationCreate
from app.services import user_services
from fastapi import HTTPException
from typing import Optional

async def create_reset_request(
    db: AsyncSession,
    username: str,
):
    try:
        user_exist = await user_services.get_by_username(db, username)
        if not user_exist:
            # We return None or raise 404. For security, maybe just return None?
            # But the caller might want to know.
            return None 

        existing = await db.execute(
            select(Notification).where(
                Notification.user_id == user_exist.id,
                Notification.status == NotificationStatus.PENDING,
                Notification.type == NotificationType.RESET_PASSWORD_REQUEST
            )
        )
        if existing.scalars().first():
            # Already exists, just return it or ignore
            return existing.scalars().first()

        new_notification = Notification(
            user_id=user_exist.id,
            tenant_id=user_exist.tenant_id,
            type=NotificationType.RESET_PASSWORD_REQUEST,
            status=NotificationStatus.PENDING
        )
        db.add(new_notification)
        await db.commit()
        await db.refresh(new_notification)
        return new_notification
    except Exception as e:
        await db.rollback()
        raise e

async def get_notifications(
    db: AsyncSession,
    tenant_id: Optional[UUID],
    status: Optional[NotificationStatus],
    creator_role: Optional[Roles] = None
):
    try:
        query = select(Notification)
        if tenant_id:
            query = query.where(Notification.tenant_id == tenant_id)
        if status:
            query = query.where(Notification.status == status)
        if creator_role:
             # Use explicit join for reliability with AsyncSession
             from app.models.user import Users
             query = query.join(Notification.user).where(Users.role == creator_role)
             
        
        notifications = await db.execute(query)
        results = notifications.scalars().all()

        return results
    except Exception as e:
        await db.rollback()
        raise e

async def resolve_notification(
    db: AsyncSession,
    id: UUID,
    status: NotificationStatus
):
    try:
        result = await db.execute(select(Notification).where(Notification.id == id))
        change_password_request = result.scalar_one_or_none()

        if not change_password_request:
            raise HTTPException (status_code=404, detail="Solicitud inexistente")
        if change_password_request.status != NotificationStatus.PENDING:
            raise HTTPException (status_code=400, detail="Solo se pueden cambiar de estado las solicitudes pendientes")
        change_password_request.status = status
        db.add(change_password_request)
        await db.commit()
        await db.refresh(change_password_request)
        return change_password_request
    except Exception as e:
        await db.rollback()
        raise e

    