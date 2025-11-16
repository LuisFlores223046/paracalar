from fastapi import APIRouter

from app.api.v1.products.routes import router as productos_router
from app.api.v1.cart.routes import router as carrito_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.search.routes import router as search_router
from app.api.v1.analytics.routes import router as analytics_router
from app.api.v1.address.routes import router as address_router
from app.api.v1.loyalty.routes import router as loyalty_router
from app.api.v1.orders.routes import router as orders_router
from app.api.v1.payment_method.routes import router as payment_method_router
from app.api.v1.payments.routes import router as payments_router
from app.api.v1.user_profile.routes import router as user_profile_router
from app.api.v1.shipping.routes import router as shipping_router 
from app.api.v1.placement_test.routes import router as placement_test_router  
from app.api.v1.subscriptions.routes import router as subscriptions_router


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

# ============ PERFIL DE USUARIO ============
api_router.include_router(
    user_profile_router,
    prefix="/profile",
    tags=["User Profile"]
)

# ============ DIRECCIONES DE ENVIO ============
api_router.include_router(
    address_router,
    prefix="/addresses",
    tags=["Addresses"]
)

# ============ MÉTODOS DE PAGO ============
api_router.include_router(
    payment_method_router,
    prefix="/payment-methods", 
    tags=["Payment Methods"]
)

# ============ PROGRAMA DE LEALTAD/PUNTOS ============
api_router.include_router(
    loyalty_router, 
    prefix="/loyalty", 
    tags=["Loyalty Program"]
)

# ============ ORDENES ============
api_router.include_router(
    orders_router, 
    prefix="/orders", 
    tags=["Orders"]
)

# ============ PROCESO DE PAGO ============
api_router.include_router(
    payments_router, 
    prefix="/checkout", 
    tags=["Payment Process"]
)

# ============ ENVÍOS Y RASTREO ============
api_router.include_router(
    shipping_router,
    prefix="/shipping",
    tags=["Shipping"]
)

# ============ TEST DE POSICIONAMIENTO ============
api_router.include_router(
    placement_test_router,
    prefix="/placement-test",
    tags=["Placement Test"]
)


api_router.include_router(
    subscriptions_router,
    prefix="/subscriptions",
    tags=["Subscriptions"]
)