from fastapi import APIRouter

from app.api.v1.products.routes import router as productos_router
from app.api.v1.cart.routes import router as carrito_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.auth.routes import router as auth_router

# Router principal de la API v1
api_router = APIRouter()

# ============ AUTENTICACIÓN ============
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# ============ PRODUCTOS ============
api_router.include_router(
    productos_router,
    prefix="/products",
    tags=["Products"]
)

# ============ CARRITO DE COMPRAS ============
api_router.include_router(
    carrito_router,
    prefix="/cart",
    tags=["Cart"]
)

# ============ ADMINISTRACIÓN ============
api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Admin"]
)