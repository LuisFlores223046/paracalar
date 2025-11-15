# Autor: Luis Flores
# Fecha: 14/11/2025
# Descripción: Archivo de configuración de pytest con fixtures compartidos para todos los tests.
#             Incluye configuración de base de datos de prueba, cliente HTTP y datos de prueba.

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date
from decimal import Decimal

from app.main import app
from app.core.database import Base, get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.enum import UserRole, AuthType, Gender
from app.core.security import hash_password

# Configurar variable de entorno para modo de prueba
os.environ["COGNITO_REGION"] = "test"

# Configuración de base de datos en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Autor: Luis Flores
    Descripción: Fixture que proporciona una sesión de base de datos de prueba.
                 Se crea una nueva base de datos en memoria para cada test y se limpia al finalizar.
    Retorna:
        Session: Sesión de base de datos SQLAlchemy para testing.
    """
    # Crear las tablas
    Base.metadata.create_all(bind=engine)
    
    # Crear sesión
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Limpiar las tablas después del test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Autor: Luis Flores
    Descripción: Fixture que proporciona un cliente HTTP de prueba (no autenticado) para FastAPI.
                 Sobrescribe la dependencia de base de datos con la BD de prueba.
    Parámetros:
        db (Session): Sesión de base de datos de prueba.
    Retorna:
        TestClient: Cliente HTTP para hacer peticiones a la API.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_client(db, test_admin):
    """
    Autor: Luis Flores
    Descripción: Fixture de cliente HTTP autenticado como Administrador.
                 Sobrescribe 'get_db' y 'get_current_user'.
    Parámetros:
        db (Session): Sesión de base de datos de prueba.
        test_admin (User): Fixture de usuario administrador.
    Retorna:
        TestClient: Cliente HTTP autenticado como admin.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_current_user():
        return test_admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user_client(db, test_user):
    """
    Autor: Luis Flores
    Descripción: Fixture de cliente HTTP autenticado como Usuario regular.
                 Sobrescribe 'get_db' y 'get_current_user'.
    Parámetros:
        db (Session): Sesión de base de datos de prueba.
        test_user (User): Fixture de usuario regular.
    Retorna:
        TestClient: Cliente HTTP autenticado como usuario.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """
    Autor: Luis Flores
    Descripción: Fixture que crea un usuario de prueba en la base de datos.
    Parámetros:
        db (Session): Sesión de base de datos.
    Retorna:
        User: Usuario de prueba creado.
    """
    user = User(
        cognito_sub="test-user-123",
        email="test@example.com",
        password_hash=hash_password("Test123!"),
        first_name="Test",
        last_name="User",
        gender=Gender.MALE,
        date_of_birth=date(1990, 1, 1),
        auth_type=AuthType.EMAIL,
        role=UserRole.USER,
        account_status=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db):
    """
    Autor: Luis Flores
    Descripción: Fixture que crea un usuario administrador de prueba.
    Parámetros:
        db (Session): Sesión de base de datos.
    Retorna:
        User: Usuario administrador de prueba.
    """
    admin = User(
        cognito_sub="test-admin-456",
        email="admin@example.com",
        password_hash=hash_password("Admin123!"),
        first_name="Admin",
        last_name="User",
        gender=Gender.FEMALE,
        date_of_birth=date(1985, 5, 15),
        auth_type=AuthType.EMAIL,
        role=UserRole.ADMIN,
        account_status=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_product(db):
    """
    Autor: Luis Flores
    Descripción: Fixture que crea un producto de prueba con imagen.
    Parámetros:
        db (Session): Sesión de base de datos.
    Retorna:
        Product: Producto de prueba creado.
    """
    product = Product(
        name="Whey Protein Test",
        description="Proteína de prueba para tests",
        brand="Test Brand",
        category="Proteínas",
        physical_activities=["weightlifting", "crossfit"],
        fitness_objectives=["muscle_gain", "recovery"],
        nutritional_value="24g proteína por servida",
        price=Decimal('899.99'),
        stock=50,
        is_active=True
    )
    db.add(product)
    db.flush()
    
    # Agregar imagen
    image = ProductImage(
        product_id=product.product_id,
        image_path="https://example.com/test-image.jpg",
        is_primary=True
    )
    db.add(image)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def test_cart(db, test_user):
    """
    Autor: Luis Flores
    Descripción: Fixture que crea un carrito de compras de prueba.
    Parámetros:
        db (Session): Sesión de base de datos.
        test_user (User): Usuario de prueba.
    Retorna:
        ShoppingCart: Carrito de compras de prueba.
    """
    cart = ShoppingCart(user_id=test_user.user_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


@pytest.fixture
def mock_cognito_token():
    """
    Autor: Luis Flores
    Descripción: Fixture que proporciona un token JWT mock para pruebas.
    Retorna:
        str: Token JWT de prueba.
    """
    return "mock-jwt-token-for-testing"