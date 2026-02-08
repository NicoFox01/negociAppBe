import enum

class PlanType(str, enum.Enum):
    FREE_FOREVER = "FREE_FOREVER"
    FREE_TRIAL_1_MONTH = "FREE_TRIAL_1_MONTH"
    PAID_MONTHLY = "PAID_MONTHLY"
    PAID_YEARLY = "PAID_YEARLY"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"

class PaymentType(str, enum.Enum):
    PAGO_MENSUAL = "PAGO_MENSUAL"
    PAGO_ANUAL = "PAGO_ANUAL"
    SOLICITUD_GRACIA = "SOLICITUD_GRACIA"
    

class Roles(str, enum.Enum):
    ADMIN = "ADMIN"
    COMPANY = "COMPANY"
    EMPLOYEE = "EMPLOYEE"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class NotificationType (str, enum.Enum):
    RESET_PASSWORD_REQUEST= "RESET_PASSWORD_REQUEST"
    
class PurchaseRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"