from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.product import Product

def test_get_product_detail_not_found(client: TestClient):
    """Prueba funcional: Obtener un producto que no existe debe dar 404."""
    # 1. Setup (ninguno, BD vacía)
    
    # 2. Act
    response = client.get("/api/v1/products/9999")
    
    # 3. Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Producto con ID 9999 no encontrado"

def test_get_product_detail_success(client: TestClient, db_session: Session):
    """Prueba funcional: Obtener un producto que sí existe."""
    # 1. Setup - Crear producto en la BD de prueba
    product = Product(
    name="Producto Funcional", description="Desc", brand="Brand",
    category="Proteínas", nutritional_value="Test", price=100.0, stock=10,
    physical_activities=[], fitness_objectives=[]  # <-- FIX
)
    db_session.add(product)
    db_session.commit()

    # 2. Act
    response = client.get(f"/api/v1/products/{product.product_id}")
    
    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Producto Funcional"
    assert data["product_id"] == product.product_id