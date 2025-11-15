# Autor: Luis Flores
# Fecha: 14/11/2025
# Descripción: Archivo de pruebas para el módulo de carrito de compras. Incluye pruebas 
#             unitarias, integrales y funcionales para operaciones del carrito.

import pytest
from sqlalchemy.orm import Session
from decimal import Decimal  # <-- IMPORTADO
from app.api.v1.cart.service import CartService
from app.api.v1.cart import schemas
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User


# ==================== PRUEBAS UNITARIAS ====================

class TestCartServiceUnit:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas unitarias del servicio de carrito.
    """
    
    def test_get_or_create_cart_existing(self, db: Session, test_cart: ShoppingCart):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria que verifica la obtención de un carrito existente.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
        """
        # Arrange
        user_id = test_cart.user_id
        
        # Act
        cart = CartService.get_or_create_cart(db, user_id)
        
        # Assert
        assert cart is not None
        assert cart.cart_id == test_cart.cart_id
        assert cart.user_id == user_id
    
    def test_get_or_create_cart_new(self, db: Session, test_user: User):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria que verifica la creación de un nuevo carrito.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_user (User): Usuario de prueba.
        """
        # Arrange - Usuario sin carrito
        
        # Act
        cart = CartService.get_or_create_cart(db, test_user.user_id)
        
        # Assert
        assert cart is not None
        assert cart.user_id == test_user.user_id
        assert cart.cart_id is not None
    
    def test_add_item_to_cart_new_item(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para agregar un nuevo item al carrito.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        
        # Act
        cart_item = CartService.add_item_to_cart(
            db, 
            test_cart.user_id, 
            item_data
        )
        
        # Assert
        assert cart_item is not None
        assert cart_item.product_id == test_product.product_id
        assert cart_item.quantity == 2
        assert cart_item.cart_id == test_cart.cart_id
    
    def test_add_item_to_cart_existing_item(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para agregar cantidad a un item existente.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Primero agregar item
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        first_item = CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Act - Agregar más cantidad del mismo producto
        second_item = CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Assert
        assert second_item.cart_item_id == first_item.cart_item_id
        assert second_item.quantity == 4  # 2 + 2
    
    def test_add_item_insufficient_stock(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para validar error por stock insuficiente.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=test_product.stock + 10  # Más de lo disponible
        )
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        assert "stock insuficiente" in str(exc_info.value).lower()
    
    def test_update_cart_item(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para actualizar la cantidad de un item.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Agregar item primero
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        cart_item = CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Act
        update_data = schemas.CartItemUpdate(quantity=5)
        updated_item = CartService.update_cart_item(
            db,
            test_cart.user_id,
            cart_item.cart_item_id,
            update_data
        )
        
        # Assert
        assert updated_item.quantity == 5
        assert updated_item.cart_item_id == cart_item.cart_item_id
    
    def test_remove_item_from_cart(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para eliminar un item del carrito.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Agregar item
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        cart_item = CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Act
        result = CartService.remove_item_from_cart(
            db,
            test_cart.user_id,
            cart_item.cart_item_id
        )
        
        # Assert
        assert result is True
        deleted_item = db.query(CartItem).filter(
            CartItem.cart_item_id == cart_item.cart_item_id
        ).first()
        assert deleted_item is None
    
    def test_clear_cart(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para vaciar el carrito completo.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Agregar items
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Act
        result = CartService.clear_cart(db, test_cart.user_id)
        
        # Assert
        assert result is True
        items = db.query(CartItem).filter(
            CartItem.cart_id == test_cart.cart_id
        ).all()
        assert len(items) == 0
    
    def test_get_cart_summary(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para obtener resumen del carrito.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Agregar items
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=3
        )
        CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Act
        summary = CartService.get_cart_summary(db, test_cart.user_id)
        
        # Assert
        assert "total_items" in summary
        assert "total_price" in summary
        assert summary["total_items"] == 3
        assert summary["total_price"] > 0
    
    def test_validate_cart_stock_success(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para validar stock suficiente en el carrito.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Act
        validation = CartService.validate_cart_stock(db, test_cart.user_id)
        
        # Assert
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
    
    def test_validate_cart_stock_insufficient(self, db: Session, test_cart: ShoppingCart, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para detectar stock insuficiente.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Agregar item con cantidad válida
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        cart_item = CartService.add_item_to_cart(db, test_cart.user_id, item_data)
        
        # Reducir stock del producto manualmente
        test_product.stock = 1
        db.commit()
        
        # Act
        validation = CartService.validate_cart_stock(db, test_cart.user_id)
        
        # Assert
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0
        assert validation["issues"][0]["issue"] == "Stock insuficiente"


# ==================== PRUEBAS DE INTEGRACIÓN ====================

class TestCartAPIIntegration:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas de integración de la API de carrito.
    """
    
    # --- CORREGIDO: Se usa 'user_client' y se quita 'client', 'test_user' y 'patch' ---
    def test_get_cart_integration(self, user_client, db, test_user, test_cart):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para obtener carrito via API.
        Parámetros:
            user_client (TestClient): Cliente HTTP autenticado.
            db (Session): Sesión de base de datos.
            test_user (User): Usuario de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
        """
        # Act
        response = user_client.get("/api/v1/cart/")
            
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "cart_id" in data
        assert "items" in data
        assert data["user_id"] == test_user.user_id
    
    # --- CORREGIDO: Se usa 'user_client' y se quita 'client', 'test_user' y 'patch' ---
    def test_add_to_cart_integration(self, user_client, db, test_product):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para agregar item al carrito.
        Parámetros:
            user_client (TestClient): Cliente HTTP autenticado.
            db (Session): Sesión de base de datos.
            test_product (Product): Producto de prueba.
        """
        # Arrange
        item_data = {
            "product_id": test_product.product_id,
            "quantity": 2
        }
        
        # Act
        response = user_client.post("/api/v1/cart/add", json=item_data)
            
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == test_product.product_id
        assert data["quantity"] == 2
    
    # --- CORREGIDO: Se usa 'user_client' y se quita 'client', 'test_user' y 'patch' ---
    def test_get_cart_summary_integration(self, user_client, db, test_user, test_cart, test_product):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para obtener resumen del carrito.
        Parámetros:
            user_client (TestClient): Cliente HTTP autenticado.
            db (Session): Sesión de base de datos.
            test_user (User): Usuario de prueba.
            test_cart (ShoppingCart): Carrito de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Agregar item
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        CartService.add_item_to_cart(db, test_user.user_id, item_data)
        
        # Act
        response = user_client.get("/api/v1/cart/summary")
            
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "total_price" in data
        assert data["total_items"] == 2


# ==================== PRUEBAS FUNCIONALES ====================

class TestCartFunctional:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas funcionales end-to-end del carrito.
    """
    
    # --- CORREGIDO: Se quita 'client' (no usado) y se arregla 'Decimal' ---
    def test_cart_shopping_flow(self, db, test_user, test_product):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional del flujo completo de compra:
                     agregar items, actualizar cantidades, validar stock y finalizar.
        Parámetros:
            db (Session): Sesión de base de datos.
            test_user (User): Usuario de prueba.
            test_product (Product): Producto de prueba.
        """
        # Paso 1: Obtener carrito vacío
        cart = CartService.get_or_create_cart(db, test_user.user_id)
        assert len(cart.cart_items) == 0
        
        # Paso 2: Agregar producto al carrito
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=2
        )
        cart_item = CartService.add_item_to_cart(db, test_user.user_id, item_data)
        assert cart_item.quantity == 2
        
        # Paso 3: Actualizar cantidad
        update_data = schemas.CartItemUpdate(quantity=3)
        updated_item = CartService.update_cart_item(
            db,
            test_user.user_id,
            cart_item.cart_item_id,
            update_data
        )
        assert updated_item.quantity == 3
        
        # Paso 4: Obtener resumen
        summary = CartService.get_cart_summary(db, test_user.user_id)
        assert summary["total_items"] == 3
        
        # --- CORREGIDO: Cálculo y aserción con Decimal ---
        expected_price = test_product.price * Decimal('3')
        assert abs(summary["total_price"] - expected_price) < Decimal('0.01')
        
        # Paso 5: Validar stock
        validation = CartService.validate_cart_stock(db, test_user.user_id)
        assert validation["valid"] is True
        
        # Paso 6: Limpiar carrito
        CartService.clear_cart(db, test_user.user_id)
        summary_after = CartService.get_cart_summary(db, test_user.user_id)
        assert summary_after["total_items"] == 0
        
        print("✅ Prueba funcional de flujo de compra completada")
    
    def test_cart_multi_product_management(self, db, test_user):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional para gestionar múltiples productos en el carrito.
        Parámetros:
            db (Session): Sesión de base de datos.
            test_user (User): Usuario de prueba.
        """
        # Paso 1: Crear múltiples productos
        products = []
        for i in range(3):
            product = Product(
                name=f"Producto {i+1}",
                description=f"Descripción {i+1}",
                brand="Test Brand",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00') * (i + 1),  # <-- CORREGIDO
                stock=20,
                is_active=True
            )
            db.add(product)
            products.append(product)
        db.commit()
        
        # Paso 2: Agregar todos los productos al carrito
        cart = CartService.get_or_create_cart(db, test_user.user_id)
        for product in products:
            item_data = schemas.CartItemAdd(
                product_id=product.product_id,
                quantity=2
            )
            CartService.add_item_to_cart(db, test_user.user_id, item_data)
        
        # Paso 3: Verificar que todos están en el carrito
        db.refresh(cart)
        assert len(cart.cart_items) == 3
        
        # Paso 4: Eliminar un producto específico
        first_item = cart.cart_items[0]
        CartService.remove_item_from_cart(
            db,
            test_user.user_id,
            first_item.cart_item_id
        )
        
        # Paso 5: Verificar que queden 2 productos
        db.refresh(cart)
        assert len(cart.cart_items) == 2
        
        # Paso 6: Obtener resumen final
        summary = CartService.get_cart_summary(db, test_user.user_id)
        assert summary["total_items"] == 4  # 2 productos x 2 unidades
        
        print("✅ Prueba funcional de gestión multi-producto completada")
    
    def test_cart_stock_validation_workflow(self, db, test_user, test_product):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional del flujo de validación de stock.
        Parámetros:
            db (Session): Sesión de base de datos.
            test_user (User): Usuario de prueba.
            test_product (Product): Producto de prueba.
        """
        # Paso 1: Agregar producto con stock disponible
        item_data = schemas.CartItemAdd(
            product_id=test_product.product_id,
            quantity=10
        )
        CartService.add_item_to_cart(db, test_user.user_id, item_data)
        
        # Paso 2: Validar - debería pasar
        validation = CartService.validate_cart_stock(db, test_user.user_id)
        assert validation["valid"] is True
        
        # Paso 3: Reducir el stock del producto
        original_stock = test_product.stock
        test_product.stock = 5  # Menos de lo que está en el carrito
        db.commit()
        
        # Paso 4: Validar nuevamente - debería fallar
        validation = CartService.validate_cart_stock(db, test_user.user_id)
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0
        
        # Paso 5: Ajustar cantidad en el carrito
        cart = CartService.get_cart(db, test_user.user_id)
        cart_item = cart.cart_items[0]
        update_data = schemas.CartItemUpdate(quantity=3)
        CartService.update_cart_item(
            db,
            test_user.user_id,
            cart_item.cart_item_id,
            update_data
        )
        
        # Paso 6: Validar nuevamente - debería pasar
        validation = CartService.validate_cart_stock(db, test_user.user_id)
        assert validation["valid"] is True
        
        # Restaurar stock original
        test_product.stock = original_stock
        db.commit()
        
        print("✅ Prueba funcional de validación de stock completada")