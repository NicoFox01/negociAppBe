from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import users, tenants, payments, notifications, products, suppliers # Descomentar a medida que los crees

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(notifications.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(notifications.router, prefix="/products", tags=["products"])
