from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID


class ChannelSalesData(BaseModel):
    channel_id: str
    channel_name: str
    today: dict
    week: dict
    month: dict


class TotalsData(BaseModel):
    today: dict
    week: dict
    month: dict


class SalesDashboardResponse(BaseModel):
    by_channel: List[ChannelSalesData]
    totals: TotalsData


class ChannelMonthlyData(BaseModel):
    channel_name: str
    total: float


class MonthlySalesData(BaseModel):
    month: str
    month_name: str
    totals_by_channel: List[ChannelMonthlyData]
    grand_total: float


class SalesHistoricalResponse(BaseModel):
    months: List[MonthlySalesData]


class PaymentMethodData(BaseModel):
    method: str
    method_display: str
    today: dict
    week: dict
    month: dict


class RevenueDashboardResponse(BaseModel):
    by_method: List[PaymentMethodData]
    totals: dict


class MonthlyRevenueByMethod(BaseModel):
    method: str
    method_display: str
    total: float
    percentage: float


class MonthlyRevenueData(BaseModel):
    month: str
    month_name: str
    grand_total: float
    by_method: List[MonthlyRevenueByMethod]


class RevenueHistoricalResponse(BaseModel):
    months: List[MonthlyRevenueData]


class MonthDetailData(BaseModel):
    month: str
    month_name: str
    grand_total: float
    totals_by_channel: List[ChannelMonthlyData]
    revenue_by_method: List[MonthlyRevenueByMethod]


class MonthDetailResponse(BaseModel):
    months: List[MonthDetailData]


class CountsResponse(BaseModel):
    purchase_orders_count: int
    insumo_requests_count: int


class TopProductEntry(BaseModel):
    product_id: UUID
    product_name: str
    quantity_sold: float
    revenue: float
    rank: int


class TopProductsResponse(BaseModel):
    period: str
    channel_id: Optional[UUID] = None
    total_products_sold: int
    products: List[TopProductEntry]
