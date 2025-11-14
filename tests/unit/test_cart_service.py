from fastapi import HTTPException
import pytest
from pytest_mock import MockerFixture # Importa mocker

from app.api.v1.cart.service import CartService
from app.api.v1.cart.schemas import CartItemAdd
from app.models.product import Product
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem

def test_add_item_to_cart_insufficient_stock(mocker: MockerFixture):
    """
    Prueba unitaria: No se puede agregar un producto si no hay stock.
    Mockeamos todas las interacciones con la BD.
    """
    # 1. Setup
    mock_db = mocker.MagicMock() # Mock de la sesión de BD
    user_id = 1
    item_data = CartItemAdd(product_id=10, quantity=5)

    # Simular que el producto existe pero tiene stock insuficiente (3)
    mock_product = Product(product_id=10, name="Test Product", stock=3, is_active=True)
    
    # Mockear las llamadas a la BD
    mock_cart = ShoppingCart(cart_id=1, user_id=user_id)
    mocker.patch.object(CartService, 'get_or_create_cart', return_value=mock_cart)
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_product

    # 2. Act & 3. Assert
    with pytest.raises(HTTPException) as exc_info:
        CartService.add_item_to_cart(db=mock_db, user_id=user_id, item_data=item_data)
    
    assert exc_info.value.status_code == 400
    assert "Stock insuficiente" in exc_info.value.detail

def test_add_item_to_cart_updates_quantity(mocker: MockerFixture):
    """
    Prueba unitaria: Si el item ya existe, actualiza la cantidad.
    """
    # 1. Setup
    mock_db = mocker.MagicMock()
    user_id = 1
    item_data = CartItemAdd(product_id=10, quantity=2) # Agregar 2

    # Mockear producto con stock suficiente
    mock_product = Product(product_id=10, name="Test Product", stock=20, is_active=True)
    
    # Mockear un item existente en el carrito con cantidad 3
    existing_item = CartItem(cart_item_id=1, product_id=10, quantity=3)
    
    # Mockear llamadas a la BD
    mock_cart = ShoppingCart(cart_id=1, user_id=user_id)
    mocker.patch.object(CartService, 'get_or_create_cart', return_value=mock_cart)
    
    # La primera llamada a first() es para el producto
    # La segunda es para el existing_item
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_product, 
        existing_item
    ]

    # 2. Act
    result = CartService.add_item_to_cart(db=mock_db, user_id=user_id, item_data=item_data)

    # 3. Assert
    # Debería haber actualizado la cantidad del item existente
    assert result == existing_item
    assert result.quantity == 5 # 3 (existentes) + 2 (nuevos)
    mock_db.commit.assert_called_once() # Asegurarse de que se guardó