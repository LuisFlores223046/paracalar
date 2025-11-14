import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from alembic.config import Config
from alembic import command
import os
from typing import Generator

from app.main import app  # Importa tu app de FastAPI
from app.core.database import Base, get_db # Importa la dependencia de BD
from app.models.user import User
from app.models.enum import UserRole, AuthType, Gender
from app.api.deps import get_current_user, require_admin
from datetime import date

# ---- Configuración de Base de Datos de Prueba ----

# Usamos una base de datos SQLite en memoria para las pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    """Crea las tablas una vez por sesión de prueba."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Crea una nueva sesión de BD para cada prueba y la revierte."""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

# ---- Fixture del Cliente de API ----

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Fixture para el TestClient de FastAPI que usa la sesión de BD de prueba.
    """
    
    # Sobrescribir la dependencia get_db para usar la sesión de prueba
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Limpiar la sobrescritura después de la prueba
    app.dependency_overrides = {}


# ---- Fixtures de Mocks de Autenticación ----

@pytest.fixture
def mock_user() -> User:
    """Retorna un usuario de prueba estándar."""
    return User(
        user_id=1,
        cognito_sub="test-sub-123",
        email="test.user@example.com",
        first_name="Test",
        last_name="User",
        role=UserRole.USER,
        gender=Gender.MALE,
        date_of_birth=date(1990, 1, 1),
        auth_type=AuthType.EMAIL,
        account_status=True
    )

@pytest.fixture
def mock_admin_user() -> User:
    """Retorna un usuario administrador de prueba."""
    return User(
        user_id=99,
        cognito_sub="admin-sub-999",
        email="admin.user@example.com",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        gender=Gender.MALE,
        date_of_birth=date(1980, 1, 1),
        auth_type=AuthType.EMAIL,
        account_status=True
    )

# Funciones helper para sobrescribir dependencias en pruebas funcionales
def override_get_current_user(mock_user: User):
    def _override():
        return mock_user
    return _override

def override_require_admin(mock_admin_user: User):
    def _override():
        return mock_admin_user
    return _override