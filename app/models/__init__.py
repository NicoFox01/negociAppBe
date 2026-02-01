from app.models.base import Base
from app.models.enums import PlanType, Roles, PaymentStatus, PaymentType
from app.models.tenant import Tenants
from app.models.user import Users
from app.models.payments import Payments
from app.models.notifications import Notification

# Ahora Alembic puede ver todos los metadatos al importar 'app.models'
