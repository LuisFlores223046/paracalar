# Autor: Luis & Gabriel
# Fecha: 16/11/2025
# Descripción: Configuración de base de datos usando SQLAlchemy 2.0
# Soporta SQLite (desarrollo) y PostgreSQL/MySQL (producción)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Obtener URL desde configuración
DATABASE_URL = settings.DATABASE_URL

# Validar que existe
if not DATABASE_URL:
    raise ValueError("❌ No se encontró DATABASE_URL en el archivo .env")

# Configurar parámetros específicos según el tipo de base de datos
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
    logger.info("🗄️  Usando SQLite como base de datos")
else:
    logger.info("🗄️  Usando base de datos remota (PostgreSQL/MySQL)")

# Crear engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,  # Mostrar SQL queries solo en DEBUG
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
)

# Crear sesión
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base moderna para SQLAlchemy 2.0
class Base(DeclarativeBase):
    """
    Clase base para todos los modelos de la base de datos.
    Usa DeclarativeBase de SQLAlchemy 2.0 para mejor typing y features.
    """
    pass


def get_db() -> Generator:
    """
    Dependencia de FastAPI que proporciona una sesión de base de datos.
    
    La sesión se cierra automáticamente después de cada request.
    
    Yields:
        Session: Sesión de SQLAlchemy para operaciones de base de datos
        
    Example:
```python
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Log de inicialización
if settings.DEBUG:
    logger.info(f"✅ Base de datos configurada correctamente")
    logger.info(f"   Tipo: {'SQLite' if 'sqlite' in DATABASE_URL else 'Remota'}")