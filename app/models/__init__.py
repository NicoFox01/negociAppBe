from app.models.base import Base
from app.models.enums import (
    PlanType, Roles, PaymentStatus, PaymentType, PurchaseRequestStatus, 
    TransactionType, PurchaseOrderStatus, DiscountType, OrderStatus, 
    PaymentMethod, ProductType, NotificationStatus, NotificationType, 
    WasteReason
)
from app.models.tenant import Tenants
from app.models.user import Users
from app.models.payments import Payments
from app.models.notifications import Notification
from app.models.products import Product
from app.models.suppliers import Supplier
from app.models.requests import PurchaseRequest, PurchaseRequestItem
from app.models.orders import PurchaseOrder, PurchaseOrderItem,SalesChannel, ProductChannelPrice, Promotion, ClientOrder, ClientOrderItem
from app.models.inventory import InventoryTransaction, ProductWaste
from app.models.production import ProductionTransform,ProductionTransformInput,ProductionTransformOutput
from app.models.alerts import StockAlert
from app.models.keep_alive import KeepAliveLog

# Ahora Alembic puede ver todos los metadatos al importar 'app.models'
