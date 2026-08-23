from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy import select
from app.api.deps import get_current_user, get_db
from app.models.enums import NotificationType, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationSchema, NotificationUpdate
from app.services import notification_services, payments_services, storage_services, user_services
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
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    status: Optional[NotificationStatus] = Query(None)
):
    if current_user.role == Roles.COMPANY:
        return await notification_services.get_notifications(
            db, 
            tenant_id=current_user.tenant_id,
            status=status, 
            creator_role=Roles.EMPLOYEE,
            skip=skip,
            limit=limit
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
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification_to_update = result.scalar_one_or_none()
    
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
    user_in_request = await user_services.get_by_id(db, notification_to_update.user_id)
    if current_user.role == Roles.ADMIN:
        if user_in_request.role == Roles.EMPLOYEE:
            raise HTTPException(status_code=404, detail= "No puedes actualizar las contraseñas de empleados")
        return await notification_services.resolve_notification(db, notification_id, new_Status)
    elif current_user.role == Roles.COMPANY:
        if notification_to_update.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="No puedes actualizar la contraseña de alguien fuera de tu compañía.")
        not_allowed_roles = {
            Roles.COMPANY,
            Roles.ADMIN
        }
        if user_in_request.role in not_allowed_roles:
            raise HTTPException(status_code=404, detail= "Unicamente tenes permisos para actualizar la contraseña de los empleados de tu compañía ")
         
        return await notification_services.resolve_notification(db, notification_id, new_Status)
    else:
        raise HTTPException(
            status_code=403,
            detail="No cuentas con los permisos requeridos para la petición"
        )

@router.get("/production-requests", response_model=List[NotificationSchema])
async def get_production_requests(
    current_user: Annotated["Users", Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        raise HTTPException(
            status_code=403,
            detail="No cuentas con los permisos requeridos"
        )
    
    query = select(Notification).where(
        Notification.tenant_id == current_user.tenant_id,
        Notification.type.in_([
            NotificationType.PRODUCTION_REQUEST,
            NotificationType.PRODUCTION_COMPLETED,
            NotificationType.PRODUCTION_CANCELLED
        ])
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    if current_user.role == Roles.EMPLOYEE:
        notifications = [n for n in notifications if n.user_id == current_user.id or n.type in [NotificationType.PRODUCTION_COMPLETED, NotificationType.PRODUCTION_CANCELLED]]
    
    return notifications

@router.patch("/production-requests/{notification_id}/respond")
async def respond_production_request(
    notification_id: UUID,
    status_action: str,
    current_user: Annotated["Users", Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    cancel_reason: Optional[str] = None
):
    if current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403,
            detail="Solo empleados pueden responder solicitudes de producción"
        )
    
    if status_action not in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail="Status debe ser COMPLETED o CANCELLED"
        )
    
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.tenant_id == current_user.tenant_id,
            Notification.type == NotificationType.PRODUCTION_REQUEST
        )
    )
    notification = result.scalars().first()
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Solicitud no encontrada"
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Esta solicitud no te pertenece"
        )
    
    notification.status = NotificationStatus.RESOLVED
    
    result_company = await db.execute(
        select(Notification).where(
            Notification.tenant_id == current_user.tenant_id
        ).where(
            Notification.user.has(role=Roles.COMPANY)
        )
    )
    company_notifications = result_company.scalars().all()
    company_user_id = company_notifications[0].user_id if company_notifications else None
    
    new_type = NotificationType.PRODUCTION_COMPLETED if status_action == "COMPLETED" else NotificationType.PRODUCTION_CANCELLED
    
    response_notification = Notification(
        tenant_id=current_user.tenant_id,
        user_id=company_user_id,
        type=new_type,
        status=NotificationStatus.PENDING,
        notes=f"Solicitud {status_action} por {current_user.name or current_user.username}" + (f": {cancel_reason}" if cancel_reason and status_action == "CANCELLED" else "")
    )
    db.add(response_notification)
    
    await db.commit()
    await db.refresh(response_notification)
    
    return {"message": f"Solicitud marcada como {status_action}", "notification_id": str(response_notification.id)}
    