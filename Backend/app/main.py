from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar el router principal de v1
from app.api.v1.router import api_router

# Crear la aplicación FastAPI
app = FastAPI(
    title="BeFit E-Commerce API",
    description="API para el e-commerce de suplementos deportivos BeFit",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir el router de la API v1
app.include_router(api_router, prefix="/api/v1")

# Endpoint raíz para verificar que el servidor está corriendo
@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Bienvenido a BeFit API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

# Endpoint de health check
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}