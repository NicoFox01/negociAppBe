from uuid import UUID
from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.enums import Roles
from app.models.user import Users
from app.services.report_service import (
    get_sales_report_dashboard,
    get_sales_report_historical,
    get_revenue_by_payment_method,
    get_revenue_historical,
    get_top_products,
    get_counts,
    get_period_dates
)
from app.schemas.report import (
    SalesDashboardResponse,
    SalesHistoricalResponse,
    RevenueDashboardResponse,
    RevenueHistoricalResponse,
    TopProductsResponse,
    CountsResponse
)

router = APIRouter()


@router.get("/dashboard", response_model=SalesDashboardResponse)
async def get_sales_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene reporte de ventas para el dashboard.
    Retorna ventas por canal para: hoy, esta semana, este mes.
    """
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        return {"by_channel": [], "totals": {"today": {"total": 0, "count": 0}, "week": {"total": 0, "count": 0}, "month": {"total": 0, "count": 0}}}
    
    return await get_sales_report_dashboard(
        db=db,
        tenant_id=current_user.tenant_id
    )


@router.get("/historical", response_model=SalesHistoricalResponse)
async def get_sales_historical(
    months: int = Query(default=12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene reporte histórico de ventas por mes.
    Retorna los últimos N meses con totales por canal.
    """
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        return {"months": []}
    
    return await get_sales_report_historical(
        db=db,
        tenant_id=current_user.tenant_id,
        months=months
    )


@router.get("/revenue-by-payment-method", response_model=RevenueDashboardResponse)
async def get_revenue_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene reporte de recaudación por método de pago para el dashboard.
    Retorna totales por método para: hoy, esta semana, este mes.
    """
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        return {"by_method": [], "totals": {"today": {"total": 0, "count": 0}, "week": {"total": 0, "count": 0}, "month": {"total": 0, "count": 0}}}
    
    return await get_revenue_by_payment_method(
        db=db,
        tenant_id=current_user.tenant_id
    )


@router.get("/revenue-historical", response_model=RevenueHistoricalResponse)
async def get_revenue_historical(
    months: int = Query(default=12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene reporte histórico de recaudación por mes y método de pago.
    Incluye ventas por canal para modal unificado.
    Retorna los últimos N meses.
    """
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        return {"months": []}
    
    return await get_revenue_historical(
        db=db,
        tenant_id=current_user.tenant_id,
        months=months
    )


@router.get("/top-products", response_model=TopProductsResponse)
async def get_top_products_report(
    period: str = Query(default="month", pattern="^(today|yesterday|week|month)$"),
    channel_id: Optional[UUID] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Ranking de productos más vendidos en el período (por cantidad vendida).
    Filtros: period=today|yesterday|week|month, channel_id opcional, limit.
    """
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        return {"period": period, "channel_id": channel_id, "total_products_sold": 0, "products": []}

    return await get_top_products(
        db=db,
        tenant_id=current_user.tenant_id,
        period=period,
        channel_id=channel_id,
        limit=limit
    )


@router.get("/counts", response_model=CountsResponse)
async def get_pending_counts(
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Obtiene contadores de ordenes de compra y pedidos de insumo pendientes.
    """
    if current_user.role not in [Roles.COMPANY, Roles.EMPLOYEE]:
        return {"purchase_orders_count": 0, "insumo_requests_count": 0}
    
    return await get_counts(db=db, tenant_id=current_user.tenant_id)
