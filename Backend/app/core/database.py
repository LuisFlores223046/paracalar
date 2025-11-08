from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator

# Usar SQLite
DATABASE_URL = "sqlite:///./befit.db"

# Crear engine con configuraciones para SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Cambia a True si quieres ver las queries SQL
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base moderna para los modelos
class Base(DeclarativeBase):
    pass

# Dependency para obtener la sesión de base de datos
def get_db() -> Generator:
    """
    Dependencia que proporciona una sesión de base de datos.
    Se cierra automáticamente después de cada request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()