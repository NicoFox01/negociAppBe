from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from calendar import monthrange
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, extract

from app.models.orders import ClientOrder, SalesChannel, PurchaseOrder
from app.models.orders import ClientOrderItem
from app.models.products import Product
from app.models.requests import PurchaseRequest
from app.models.enums import OrderStatus, PaymentMethod, PurchaseOrderStatus, PurchaseRequestStatus

ARG = ZoneInfo("America/Argentina/Buenos_Aires")

PAYMENT_METHOD_DISPLAY = {
    "EFECTIVO": "Efectivo",
    "MERCADOPAGO": "MercadoPago",
    "APP_COMIDA": "App de Comida",
    "TRANSFERENCIA": "Transferencia",
    "OTRO": "Otro"
}


def get_period_dates(period: str) -> tuple[datetime, datetime]:
    """Retorna (start_date, end_date) según el período."""
    now = datetime.now(ARG)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    if period == "today":
        return today_start, today_end
    elif period == "yesterday":
        yesterday = today_start - timedelta(days=1)
        return yesterday, yesterday.replace(hour=23, minute=59, second=59)
    elif period == "week":
        start = today_start - timedelta(days=today_start.weekday())
        return start, today_end
    elif period == "month":
        start = today_start.replace(day=1)
        return start, today_end
    else:
        return today_start, today_end


async def get_sales_report_dashboard(
    db: AsyncSession,
    tenant_id: UUID,
    channel_id: Optional[UUID] = None
) -> dict:
    """
    Obtiene reporte de ventas para el dashboard.
    Retorna ventas por canal para: hoy, esta semana, este mes.
    """
    now = datetime.now(ARG)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    channels_query = select(SalesChannel).where(
        SalesChannel.tenant_id == tenant_id,
        SalesChannel.is_active == True
    )
    channels_result = await db.execute(channels_query)
    channels = channels_result.scalars().all()
    
    by_channel = []
    
    for channel in channels:
        channel_conditions = [
            ClientOrder.tenant_id == tenant_id,
            ClientOrder.channel_id == channel.id,
            ClientOrder.status == OrderStatus.COMPLETED
        ]
        
        today_query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(*channel_conditions).where(
            ClientOrder.created_at >= today_start,
            ClientOrder.created_at <= now
        )
        today_count_query = select(func.count(ClientOrder.id)).where(*channel_conditions).where(
            ClientOrder.created_at >= today_start,
            ClientOrder.created_at <= now
        )
        
        week_query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(*channel_conditions).where(
            ClientOrder.created_at >= week_start,
            ClientOrder.created_at <= now
        )
        week_count_query = select(func.count(ClientOrder.id)).where(*channel_conditions).where(
            ClientOrder.created_at >= week_start,
            ClientOrder.created_at <= now
        )
        
        month_query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(*channel_conditions).where(
            ClientOrder.created_at >= month_start,
            ClientOrder.created_at <= now
        )
        month_count_query = select(func.count(ClientOrder.id)).where(*channel_conditions).where(
            ClientOrder.created_at >= month_start,
            ClientOrder.created_at <= now
        )
        
        today_total = (await db.execute(today_query)).scalar() or 0
        today_count = (await db.execute(today_count_query)).scalar() or 0
        week_total = (await db.execute(week_query)).scalar() or 0
        week_count = (await db.execute(week_count_query)).scalar() or 0
        month_total = (await db.execute(month_query)).scalar() or 0
        month_count = (await db.execute(month_count_query)).scalar() or 0
        
        by_channel.append({
            "channel_id": str(channel.id),
            "channel_name": channel.name,
            "today": {
                "total": float(today_total),
                "count": int(today_count)
            },
            "week": {
                "total": float(week_total),
                "count": int(week_count)
            },
            "month": {
                "total": float(month_total),
                "count": int(month_count)
            }
        })
    
    today_totals = sum(c["today"]["total"] for c in by_channel)
    today_counts = sum(c["today"]["count"] for c in by_channel)
    week_totals = sum(c["week"]["total"] for c in by_channel)
    week_counts = sum(c["week"]["count"] for c in by_channel)
    month_totals = sum(c["month"]["total"] for c in by_channel)
    month_counts = sum(c["month"]["count"] for c in by_channel)
    
    return {
        "by_channel": by_channel,
        "totals": {
            "today": {"total": today_totals, "count": today_counts},
            "week": {"total": week_totals, "count": week_counts},
            "month": {"total": month_totals, "count": month_counts}
        }
    }


async def get_sales_report_historical(
    db: AsyncSession,
    tenant_id: UUID,
    months: int = 12
) -> dict:
    """
    Obtiene reporte histórico de ventas por mes.
    Retorna los últimos N meses con totales por canal.
    """
    now = datetime.now(ARG)
    
    months_data = []
    
    for i in range(months):
        target_month = now.month - i
        target_year = now.year
        
        if target_month <= 0:
            target_month += 12
            target_year -= 1
        
        month_start = datetime(target_year, target_month, 1, tzinfo=ARG)
        _, last_day = monthrange(target_year, target_month)
        month_end = datetime(target_year, target_month, last_day, 23, 59, 59, tzinfo=ARG)
        
        month_name = month_start.strftime("%B %Y")
        
        channels_query = select(SalesChannel).where(
            SalesChannel.tenant_id == tenant_id,
            SalesChannel.is_active == True
        )
        channels_result = await db.execute(channels_query)
        channels = channels_result.scalars().all()
        
        totals_by_channel = []
        grand_total = 0
        
        for channel in channels:
            query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(
                ClientOrder.tenant_id == tenant_id,
                ClientOrder.channel_id == channel.id,
                ClientOrder.status == OrderStatus.COMPLETED,
                ClientOrder.created_at >= month_start,
                ClientOrder.created_at <= month_end
            )
            
            total = (await db.execute(query)).scalar() or 0
            total_float = float(total)
            grand_total += total_float
            
            if total_float > 0:
                totals_by_channel.append({
                    "channel_name": channel.name,
                    "total": total_float
                })
        
        if grand_total > 0:
            months_data.append({
                "month": f"{target_year}-{target_month:02d}",
                "month_name": month_name,
                "totals_by_channel": totals_by_channel,
                "grand_total": grand_total
            })
    
    return {"months": months_data}


async def get_revenue_by_payment_method(
    db: AsyncSession,
    tenant_id: UUID
) -> dict:
    """
    Obtiene reporte de recaudación por método de pago para el dashboard.
    Retorna totales por método para: hoy, esta semana, este mes.
    """
    now = datetime.now(ARG)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    payment_methods = [pm.value for pm in PaymentMethod]
    by_method = []
    
    for method in payment_methods:
        method_conditions = [
            ClientOrder.tenant_id == tenant_id,
            ClientOrder.payment_method == method,
            ClientOrder.status == OrderStatus.COMPLETED
        ]
        
        today_query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(*method_conditions).where(
            ClientOrder.created_at >= today_start,
            ClientOrder.created_at <= now
        )
        today_count_query = select(func.count(ClientOrder.id)).where(*method_conditions).where(
            ClientOrder.created_at >= today_start,
            ClientOrder.created_at <= now
        )
        
        week_query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(*method_conditions).where(
            ClientOrder.created_at >= week_start,
            ClientOrder.created_at <= now
        )
        week_count_query = select(func.count(ClientOrder.id)).where(*method_conditions).where(
            ClientOrder.created_at >= week_start,
            ClientOrder.created_at <= now
        )
        
        month_query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(*method_conditions).where(
            ClientOrder.created_at >= month_start,
            ClientOrder.created_at <= now
        )
        month_count_query = select(func.count(ClientOrder.id)).where(*method_conditions).where(
            ClientOrder.created_at >= month_start,
            ClientOrder.created_at <= now
        )
        
        today_total = (await db.execute(today_query)).scalar() or 0
        today_count = (await db.execute(today_count_query)).scalar() or 0
        week_total = (await db.execute(week_query)).scalar() or 0
        week_count = (await db.execute(week_count_query)).scalar() or 0
        month_total = (await db.execute(month_query)).scalar() or 0
        month_count = (await db.execute(month_count_query)).scalar() or 0
        
        by_method.append({
            "method": method,
            "method_display": PAYMENT_METHOD_DISPLAY.get(method, method),
            "today": {"total": float(today_total), "count": int(today_count)},
            "week": {"total": float(week_total), "count": int(week_count)},
            "month": {"total": float(month_total), "count": int(month_count)}
        })
    
    today_totals = sum(m["today"]["total"] for m in by_method)
    today_counts = sum(m["today"]["count"] for m in by_method)
    week_totals = sum(m["week"]["total"] for m in by_method)
    week_counts = sum(m["week"]["count"] for m in by_method)
    month_totals = sum(m["month"]["total"] for m in by_method)
    month_counts = sum(m["month"]["count"] for m in by_method)
    
    return {
        "by_method": by_method,
        "totals": {
            "today": {"total": today_totals, "count": today_counts},
            "week": {"total": week_totals, "count": week_counts},
            "month": {"total": month_totals, "count": month_counts}
        }
    }


async def get_revenue_historical(
    db: AsyncSession,
    tenant_id: UUID,
    months: int = 12
) -> dict:
    """
    Obtiene reporte histórico de recaudación por mes y método de pago.
    También incluye ventas por canal para el modal unificado.
    Retorna los últimos N meses.
    """
    now = datetime.now(ARG)
    
    months_data = []
    
    for i in range(months):
        target_month = now.month - i
        target_year = now.year
        
        if target_month <= 0:
            target_month += 12
            target_year -= 1
        
        month_start = datetime(target_year, target_month, 1, tzinfo=ARG)
        _, last_day = monthrange(target_year, target_month)
        month_end = datetime(target_year, target_month, last_day, 23, 59, 59, tzinfo=ARG)
        
        month_name = month_start.strftime("%B %Y")
        
        payment_methods = [pm.value for pm in PaymentMethod]
        revenue_by_method = []
        grand_total_revenue = 0
        
        for method in payment_methods:
            method_query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(
                ClientOrder.tenant_id == tenant_id,
                ClientOrder.payment_method == method,
                ClientOrder.status == OrderStatus.COMPLETED,
                ClientOrder.created_at >= month_start,
                ClientOrder.created_at <= month_end
            )
            
            method_total = (await db.execute(method_query)).scalar() or 0
            method_total_float = float(method_total)
            grand_total_revenue += method_total_float
            
            if method_total_float > 0:
                revenue_by_method.append({
                    "method": method,
                    "method_display": PAYMENT_METHOD_DISPLAY.get(method, method),
                    "total": method_total_float,
                    "percentage": 0.0
                })
        
        if grand_total_revenue > 0:
            for item in revenue_by_method:
                item["percentage"] = round((item["total"] / grand_total_revenue) * 100, 1)
        
        channels_query = select(SalesChannel).where(
            SalesChannel.tenant_id == tenant_id,
            SalesChannel.is_active == True
        )
        channels_result = await db.execute(channels_query)
        channels = channels_result.scalars().all()
        
        totals_by_channel = []
        grand_total_channel = 0
        
        for channel in channels:
            query = select(func.coalesce(func.sum(ClientOrder.total_amount), 0)).where(
                ClientOrder.tenant_id == tenant_id,
                ClientOrder.channel_id == channel.id,
                ClientOrder.status == OrderStatus.COMPLETED,
                ClientOrder.created_at >= month_start,
                ClientOrder.created_at <= month_end
            )
            
            total = (await db.execute(query)).scalar() or 0
            total_float = float(total)
            grand_total_channel += total_float
            
            if total_float > 0:
                totals_by_channel.append({
                    "channel_name": channel.name,
                    "total": total_float
                })
        
        grand_total = grand_total_revenue
        
        if grand_total > 0:
            months_data.append({
                "month": f"{target_year}-{target_month:02d}",
                "month_name": month_name,
                "grand_total": grand_total,
                "totals_by_channel": totals_by_channel,
                "revenue_by_method": revenue_by_method
            })
    
    return {"months": months_data}


async def get_top_products(
    db: AsyncSession,
    tenant_id: UUID,
    period: str = "month",
    channel_id: Optional[UUID] = None,
    limit: int = 10
) -> dict:
    """
    Ranking de productos más vendidos (por cantidad) en el período.
    Solo cuenta órdenes COMPLETED. Filtro opcional por canal.
    """
    start, end = get_period_dates(period)

    conditions = [
        ClientOrder.tenant_id == tenant_id,
        ClientOrder.status == OrderStatus.COMPLETED,
        ClientOrder.created_at >= start,
        ClientOrder.created_at <= end
    ]
    if channel_id:
        conditions.append(ClientOrder.channel_id == channel_id)

    count_query = select(
        func.count(func.distinct(ClientOrderItem.product_id))
    ).join(
        ClientOrder, ClientOrderItem.order_id == ClientOrder.id
    ).where(*conditions)
    total_products = (await db.execute(count_query)).scalar() or 0

    ranking_query = (
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(ClientOrderItem.quantity).label("quantity_sold"),
            func.sum(ClientOrderItem.quantity * ClientOrderItem.unit_price).label("revenue")
        )
        .select_from(ClientOrderItem)
        .join(Product, ClientOrderItem.product_id == Product.id)
        .join(ClientOrder, ClientOrderItem.order_id == ClientOrder.id)
        .where(*conditions)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(ClientOrderItem.quantity).desc())
        .limit(limit)
    )
    rows = (await db.execute(ranking_query)).all()

    products = [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "quantity_sold": float(row.quantity_sold or 0),
            "revenue": float(row.revenue or 0),
            "rank": idx + 1
        }
        for idx, row in enumerate(rows)
    ]

    return {
        "period": period,
        "channel_id": channel_id,
        "total_products_sold": int(total_products),
        "products": products
    }


async def get_counts(db: AsyncSession, tenant_id: UUID) -> dict:
    po_result = await db.execute(
        select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.status.in_([
                PurchaseOrderStatus.DRAFT,
                PurchaseOrderStatus.SENT,
                PurchaseOrderStatus.PARTIALLY_RECEIVED
            ])
        )
    )
    purchase_orders_count = po_result.scalar() or 0

    ir_result = await db.execute(
        select(func.count(PurchaseRequest.id)).where(
            PurchaseRequest.tenant_id == tenant_id,
            PurchaseRequest.status == PurchaseRequestStatus.PENDING
        )
    )
    insumo_requests_count = ir_result.scalar() or 0

    return {
        "purchase_orders_count": int(purchase_orders_count),
        "insumo_requests_count": int(insumo_requests_count)
    }
