from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.product import Product
from app.api.deps import get_current_user, require_admin
from tests.conftest import override_get_current_user, override_require_admin
from app.main import app # <-- AÑADIR ESTA LÍNEA

def test_admin_route_forbidden_for_normal_user(
    client: TestClient, 
    db_session: Session, 
    mock_user: User # Usuario normal
):
    """
    Prueba funcional de SEGURIDAD: Un usuario normal no puede
    acceder a rutas de admin.
    """
    # 1. Setup
    # Guardamos el usuario normal en la BD
    db_session.add(mock_user)
    db_session.commit()
    
    # Sobrescribimos get_current_user para que devuelva al usuario normal
    # NO sobrescribimos require_admin, queremos que falle.
    app.dependency_overrides[get_current_user] = override_get_current_user(mock_user)

    # 2. Act
    response = client.post("/api/v1/admin/products/bulk-action", json={
        "product_ids": [1, 2],
        "action": "activate"
    })

    # 3. Assert
    assert response.status_code == 403 # Forbidden
    assert "No tienes permisos" in response.json()["detail"]

    # Limpiar override
    app.dependency_overrides = {}

def test_admin_route_success_for_admin_user(
    client: TestClient, 
    db_session: Session, 
    mock_admin_user: User # Usuario Admin
):
    """
    Prueba funcional: Un admin SÍ puede acceder a la ruta.
    """
    # 1. Setup
    # Crear productos para la prueba
    p1 = Product(name="P1", description="d", brand="b", category="c", nutritional_value="n", price=10, stock=5, is_active=False, physical_activities=[], fitness_objectives=[])
    p2 = Product(name="P2", description="d", brand="b", category="c", nutritional_value="n", price=10, stock=5, is_active=False, physical_activities=[], fitness_objectives=[])
    db_session.add_all([mock_admin_user, p1, p2])
    db_session.flush() # Envía a la BD para obtener IDs

    # Guardamos los IDs ANTES de que los objetos se desconecten
    p1_id = p1.product_id 
    p2_id = p2.product_id

    db_session.commit() # Cierra la transacción

    # Sobrescribimos la dependencia de admin
    app.dependency_overrides[require_admin] = override_require_admin(mock_admin_user)

    # 2. Act
    response = client.post("/api/v1/admin/products/bulk-action", json={
        "product_ids": [p1_id, p2_id], # <-- USA LAS VARIABLES
        "action": "activate" 
})

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == 2
    assert data["failed"] == 0
    
    # Verificar en la BD (consultando de nuevo)
    p1_updated = db_session.get(Product, p1_id) # <-- USA LAS VARIABLES
    p2_updated = db_session.get(Product, p2_id) # <-- USA LAS VARIABLES
    assert p1_updated.is_active == True
    assert p2_updated.is_active == True

    # Limpiar override
    app.dependency_overrides = {}