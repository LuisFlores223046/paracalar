from sqlalchemy.orm import Session
from app.api.v1.cart.service import CartService
from app.api.v1.cart.schemas import CartItemAdd
from app.models.user import User
from app.models.product import Product
from app.models.cart_item import CartItem
from app.models.enum import UserRole, AuthType, Gender
from datetime import date

def test_cart_service_integration(db_session: Session):
    """
    Prueba de integración: Agrega un item al carrito y verifica que
    se haya creado correctamente en la BD de prueba.
    """
    # 1. Setup - Crear datos reales en la BD de prueba
    # Usamos db_session que viene de conftest.py
    
    # Crear usuario
    user = User(
        cognito_sub="integration-user", email="int@test.com", 
        first_name="Int", last_name="Test", role=UserRole.USER,
        gender=Gender.MALE, date_of_birth=date(1990, 1, 1),
        auth_type=AuthType.EMAIL, account_status=True
    )
    db_session.add(user)
    
    # Crear producto
    product = Product(
    name="Producto de Integración", description="Desc", brand="Brand",
    category="Proteínas", nutritional_value="Test", price=100.0, stock=10,
    physical_activities=[], fitness_objectives=[]  # <-- FIX
)
    db_session.add(product)
    db_session.commit() # Guardar el usuario y producto para obtener sus IDs

    item_data = CartItemAdd(product_id=product.product_id, quantity=2)

    # 2. Act
    # Llamar al servicio con la sesión de BD real (de prueba)
    CartService.add_item_to_cart(db=db_session, user_id=user.user_id, item_data=item_data)
    
    # 3. Assert
    # Verificar directamente en la BD
    cart_item = db_session.query(CartItem).filter(
        CartItem.product_id == product.product_id
    ).first()
    
    assert cart_item is not None
    assert cart_item.quantity == 2
    assert cart_item.shopping_cart.user_id == user.user_id