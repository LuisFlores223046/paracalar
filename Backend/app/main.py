from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router

# Crear la aplicación FastAPI con metadatos mejorados
app = FastAPI(
    title="BeFit API",
    description="""
    ## API REST para plataforma de e-commerce de productos fitness

    Esta API proporciona endpoints para:
    
    * **Productos**: Gestión completa de productos (CRUD, búsqueda, filtros)
    * **Categorías**: Organización de productos por categorías
    * **Carrito de compras**: Gestión del carrito de usuarios
    * **Reseñas**: Sistema de calificaciones y comentarios
    * **Administración**: Panel administrativo con estadísticas y reportes
    
    ### Autenticación
    La mayoría de los endpoints requieren autenticación mediante Bearer Token.
    
    ### Base URL
    Todos los endpoints están bajo el prefijo `/api/v1`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "BeFit Team",
        "email": "soporte@befit.com"
    },
    license_info={
        "name": "MIT"
    }
)

# Configurar CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir el router principal de la API v1
# Todos los endpoints estarán disponibles bajo /api/v1
app.include_router(api_router, prefix="/api/v1")

# ============ ENDPOINTS RAÍZ ============

@app.get("/", tags=["root"])
def root():
    """
    Endpoint raíz de la API
    
    Retorna información básica sobre la API y enlaces útiles.
    """
    return {
        "message": "¡Bienvenido a la API de BeFit!",
        "version": "1.0.0",
        "documentation": "/docs",
        "alternative_docs": "/redoc",
        "endpoints": {
            "products": "/api/v1/products",
            "cart": "/api/v1/cart",
            "admin": "/api/v1/admin"
        }
    }


@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint
    
    Útil para verificar que la API está funcionando correctamente.
    Puede ser usado por servicios de monitoreo o load balancers.
    """
    return {
        "status": "healthy",
        "service": "BeFit API",
        "version": "1.0.0"
    }


@app.get("/api/v1", tags=["root"])
def api_v1_root():
    """
    Endpoint raíz de la versión 1 de la API
    
    Muestra todos los módulos disponibles en la API v1.
    """
    return {
        "version": "1.0",
        "modules": {
            "products": {
                "path": "/api/v1/products",
                "description": "Gestión de productos y categorías"
            },
            "cart": {
                "path": "/api/v1/cart",
                "description": "Carrito de compras"
            },
            "admin": {
                "path": "/api/v1/admin",
                "description": "Panel de administración"
            }
        }
    }


# ============ STARTUP / SHUTDOWN EVENTS ============

@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación
    """
    print("🚀 BeFit API iniciando...")
    print("📚 Documentación disponible en: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento que se ejecuta al cerrar la aplicación
    """
    print("👋 BeFit API cerrándose...")