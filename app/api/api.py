from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import users, tenants, payments, notifications # Descomentar a medida que los crees

api_router = APIRouter()

# Conectamos el router de Auth
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# Conectamos el router de Users
api_router.include_router(users.router, prefix="/users", tags=["users"])
# Conectamos el router de Tenants
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
# Conectamos el router de Payments
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
