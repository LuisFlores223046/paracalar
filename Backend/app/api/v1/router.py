from fastapi import APIRouter

from app.api.v1.products.routes import router as productos_router
from app.api.v1.cart.routes import router as carrito_router
from app.api.v1.admin.routes import router as admin_router

# Router principal de la API v1
api_router = APIRouter()

# Incluir todos los routers de módulos
api_router.include_router(
    productos_router,
    prefix="/products",
    tags=["products"]
)

api_router.include_router(
    carrito_router,
    prefix="/cart",
    tags=["cart"]
)

api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"]
)