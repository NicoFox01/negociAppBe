from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.enums import Roles, ProductType
from app.services import alerts_service
from app.schemas.alerts import StockAlertUpdate
from app.models.user import Users

router = APIRouter()


class ProductionRequestCreate(BaseModel):
    product_id: UUID
    quantity: float
    recipient_ids: List[UUID] = []


class ProductionResponseCreate(BaseModel):
    status: str
    cancel_reason: Optional[str] = None


class DashboardAlertsResponse(BaseModel):
    raw_materials: dict
    elaborated_products: dict


@router.get("/dashboard-alerts", response_model=DashboardAlertsResponse)
async def get_dashboard_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene las alertas para el widget del dashboard.
    """
    return await alerts_service.get_all_alerts(
        db=db,
        tenant_id=current_user.tenant_id
    )


@router.get("/alert-count")
async def get_alert_count(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene la cantidad de alertas para el badge.
    """
    count = await alerts_service.get_alert_count(
        db=db,
        tenant_id=current_user.tenant_id
    )
    return {"count": count}


@router.patch("/products/{product_id}/alert-config")
async def configure_product_alert(
    product_id: UUID,
    config: StockAlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Configura los parámetros de alerta para un producto.
    """
    if current_user.role not in [Roles.COMPANY]:
        raise HTTPException(status_code=403, detail="Solo COMPANY puede configurar alertas")
    
    return await alerts_service.configure_product_alert(
        db=db,
        product_id=product_id,
        tenant_id=current_user.tenant_id,
        config=config
    )


@router.post("/production-request")
async def send_production_request(
    data: ProductionRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Envía una solicitud de producción a employees.
    """
    if current_user.role not in [Roles.COMPANY]:
        raise HTTPException(status_code=403, detail="Solo COMPANY puede enviar solicitudes de producción")
    
    return await alerts_service.send_production_request(
        db=db,
        tenant_id=current_user.tenant_id,
        product_id=data.product_id,
        quantity=data.quantity,
        recipient_ids=data.recipient_ids,
        requester_name=current_user.name or "Company"
    )


@router.get("/production-requests")
async def get_production_requests(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene las solicitudes de producción para el usuario actual.
    """
    return await alerts_service.get_production_requests(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.patch("/production-requests/{notification_id}/respond")
async def respond_production_request(
    notification_id: UUID,
    data: ProductionResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Responde una solicitud de producción (completada o cancelada).
    """
    if current_user.role not in [Roles.EMPLOYEE]:
        raise HTTPException(status_code=403, detail="Solo EMPLOYEE puede responder solicitudes")
    
    if data.status not in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Status debe ser COMPLETED o CANCELLED")
    
    return await alerts_service.respond_production_request(
        db=db,
        notification_id=notification_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        status=data.status,
        cancel_reason=data.cancel_reason,
        user_name=current_user.name or "Employee"
    )
