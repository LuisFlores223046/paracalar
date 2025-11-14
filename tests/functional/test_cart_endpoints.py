from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.product import Product
from app.api.deps import get_current_user
from tests.conftest import override_get_current_user # Importamos el helper
from app.main import app # <-- AÑADIR ESTA LÍNEA

def test_add_to_cart_requires_auth(client: TestClient):
    """Prueba funcional: Endpoint /cart/add debe estar protegido."""
    response = client.post("/api/v1/cart/add", json={
        "product_id": 1,
        "quantity": 1
    })
    # Esperamos un 401 (o 403 dependiendo de tu config de Bearer, 
    # pero FastAPI suele dar 401 si no hay token)
    assert response.status_code == 403 

def test_add_to_cart_success(
    client: TestClient, 
    db_session: Session, 
    mock_user: User # Fixture de conftest.py
):
    """
    Prueba funcional: Agregar al carrito exitosamente
    simulando un usuario logueado.
    """
    # 1. Setup
    # Crear producto en BD
    product = Product(
    name="Producto para Carrito", description="Desc", brand="Brand",
    category="Proteínas", nutritional_value="Test", price=100.0, stock=10,
    physical_activities=[], fitness_objectives=[]  # <-- FIX
)
    # Guardar el usuario mock en la BD de prueba para que exista
    db_session.add_all([product, mock_user])
    db_session.commit()
    
    # Sobrescribir la dependencia de autenticación
    app.dependency_overrides[get_current_user] = override_get_current_user(mock_user)

    # 2. Act
    response = client.post("/api/v1/cart/add", json={
        "product_id": product.product_id,
        "quantity": 3
    })

    # 3. Assert
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == product.product_id
    assert data["quantity"] == 3
    assert data["product"]["name"] == "Producto para Carrito"

    # Limpiar override
    app.dependency_overrides = {}