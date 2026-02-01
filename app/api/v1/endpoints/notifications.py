from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy import select
from app.api.deps import get_current_user, get_db
from app.models.enums import NotificationType, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationSchema, NotificationUpdate
from app.services import payments_services, storage_services
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.enums import Roles

from app.models.notifications import Notification
from typing import Annotated, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import Users

router = APIRouter()

@router.get("/", response_model=List[NotificationSchema])
async def get_my_notifications(
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    status: Optional[NotificationStatus] = Query(None)
):
    if current_user.role == Roles.COMPANY:
        return await notification_services.get_notifications(
            db, 
            tenant_id=current_user.tenant_id,
            status=status, 
            creator_role=Roles.EMPLOYEE
        )
    elif current_user.role == Roles.ADMIN:
        return await notification_services.get_notifications(
            db, 
            tenant_id=None,
            status=status, 
            creator_role=Roles.COMPANY
        )
    else:
        raise HTTPException(
            status_code=403,
            detail="No cuentas con los permisos requeridos para ver notificaciones."
        )

@router.post("/{username_request}", response_model=NotificationCreate)
async def create_reset_request(username_request: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Users).where(Users.username == username_request))
    user_db = result.scalars().first()
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
        )

    query_exist = await db.execute(
        select(Notification).where(
            Notification.user_id == user_db.id,
            Notification.status == NotificationStatus.PENDING,
            Notification.type == NotificationType.RESET_PASSWORD_REQUEST
        )
    )
    if query_exist.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una solicitud de recuperación pendiente para este usuario."
        )

    new_notification = Notification(
        user_id=user_db.id,
        tenant_id=user_db.tenant_id,
        type=NotificationType.RESET_PASSWORD_REQUEST,
        status=NotificationStatus.PENDING
    )

    db.add(new_notification)
    await db.commit()
    await db.refresh(new_notification)
    return new_notification

@router.patch("/{notification_id}", response_model=NotificationUpdate)
async def resolve_notification_request(
    notification_id: UUID,
    new_Status: NotificationStatus,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    notification_to_update = await db.execute(select(Notification).where(Notification.id == notification_id))
    if not notification_to_update:
        raise HTTPException (
            status_code=404,
            detail="Notificación no encontrada"
            )
    allowed_statuses = {
        NotificationStatus.RESOLVED,
        NotificationStatus.IGNORED,
    }

    if new_Status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Status invalido. Solo se Permite IGNORED o RESOLVED."
        )
    user_in_request = await user_services.get_by_id(notification_to_update.user_id)
    if current_user.role == Roles.ADMIN:
        if user_in_request.role == Roles.EMPLOYEE:
            raise HTTPException(status_code=404, detail= "No puedes actualizar las contraseñas de empleados")
        return notification_services.resolve_notification(db, notification_id, new_Status)
    elif current_user.role == Roles.COMPANY:
        if notification_to_update.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="No puedes actualizar la contraseña de alguien fuera de tu compañía.")
        not_allowed_roles = {
            Roles.COMPANY,
            Roles.ADMIN
        }
        if user_in_request.role == not_allowed_roles:
            raise HTTPException(status_code=404, detail= "Unicamente tenes permisos para actualizar la contraseña de los empleados de tu compañía ")
         
        return notification_services.get_notifications(db,current_user.tenant_id, new_Status, role=Roles.EMPLOYEE)
    else:
        raise HTTPException(
            status_code=403,
            detail="No cuentas con los permisos requeridos para la petición"
        )
    