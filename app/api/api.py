from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import users, tenants, payments, notifications, products, suppliers, request, orders, inventory

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(request.router, prefix="/request", tags=["request"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
