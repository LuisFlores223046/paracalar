from fastapi import APIRouter

from app.api.v1.products.routes import router as productos_router
from app.api.v1.cart.routes import router as carrito_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.search.routes import router as search_router
from app.api.v1.analytics.routes import router as analytics_router

# Router principal de la API v1
api_router = APIRouter()

# ============ AUTENTICACIÓN ============
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# ============ BÚSQUEDA Y FILTROS ============
api_router.include_router(
    search_router,
    prefix="/search",
    tags=["Search & Filters"]
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

# ============ ANALYTICS Y REPORTES ============
api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics & Reports"]
)