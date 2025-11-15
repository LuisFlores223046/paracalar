# Autor: Luis Flores
# Fecha: 14/11/2025
# Descripción: Archivo de pruebas para el módulo de administración. Incluye pruebas 
#             unitarias, integrales y funcionales para operaciones administrativas.

import pytest
from sqlalchemy.orm import Session
from decimal import Decimal  # <-- IMPORTADO
from app.api.v1.admin.service import AdminProductService
from app.api.v1.admin import schemas
from app.api.v1.products import schemas as product_schemas
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User
from app.api.v1.products.service import ProductService


# ==================== PRUEBAS UNITARIAS ====================

class TestAdminProductServiceUnit:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas unitarias del servicio de administración.
    """
    
    def test_bulk_update_activate_products(self, db: Session):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para activar múltiples productos en lote.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
        """
        # Arrange - Crear productos inactivos
        products = []
        for i in range(3):
            product = Product(
                name=f"Producto Inactivo {i+1}",
                description="Test",
                brand="Test",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00'),  # <-- CORREGIDO
                stock=10,
                is_active=False
            )
            db.add(product)
            products.append(product)
        db.commit()
        
        product_ids = [p.product_id for p in products]
        
        # Act
        action_data = schemas.BulkProductAction(
            product_ids=product_ids,
            action="activate"
        )
        result = AdminProductService.bulk_update_products(db, action_data)
        
        # Assert
        assert result.success == 3
        assert result.failed == 0
        
        # Verificar que se activaron
        for product in products:
            db.refresh(product)
            assert product.is_active is True
    
    def test_bulk_update_deactivate_products(self, db: Session):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para desactivar múltiples productos en lote.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
        """
        # Arrange - Crear productos activos
        products = []
        for i in range(3):
            product = Product(
                name=f"Producto Activo {i+1}",
                description="Test",
                brand="Test",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00'),  # <-- CORREGIDO
                stock=10,
                is_active=True
            )
            db.add(product)
            products.append(product)
        db.commit()
        
        product_ids = [p.product_id for p in products]
        
        # Act
        action_data = schemas.BulkProductAction(
            product_ids=product_ids,
            action="deactivate"
        )
        result = AdminProductService.bulk_update_products(db, action_data)
        
        # Assert
        assert result.success == 3
        assert result.failed == 0
        
        # Verificar que se desactivaron
        for product in products:
            db.refresh(product)
            assert product.is_active is False
    
    def test_bulk_update_delete_products(self, db: Session):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para eliminar múltiples productos en lote.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
        """
        # Arrange
        products = []
        for i in range(3):
            product = Product(
                name=f"Producto a Eliminar {i+1}",
                description="Test",
                brand="Test",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00'),  # <-- CORREGIDO
                stock=10,
                is_active=True
            )
            db.add(product)
            products.append(product)
        db.commit()
        
        product_ids = [p.product_id for p in products]
        
        # Act
        action_data = schemas.BulkProductAction(
            product_ids=product_ids,
            action="delete"
        )
        result = AdminProductService.bulk_update_products(db, action_data)
        
        # Assert
        assert result.success == 3
        assert result.failed == 0
        
        # Verificar que se eliminaron
        for product_id in product_ids:
            deleted = db.query(Product).filter(
                Product.product_id == product_id
            ).first()
            assert deleted is None
    
    def test_bulk_update_partial_failure(self, db: Session):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para manejar fallos parciales en operaciones en lote.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
        """
        # Arrange - Crear solo un producto
        product = Product(
            name="Producto Test",
            description="Test",
            brand="Test",
            category="Test",
            physical_activities=["test"],
            fitness_objectives=["test"],
            nutritional_value="Test",
            price=Decimal('100.00'),  # <-- CORREGIDO
            stock=10,
            is_active=True
        )
        db.add(product)
        db.commit()
        
        # Incluir IDs que no existen
        product_ids = [product.product_id, 9999, 9998]
        
        # Act
        action_data = schemas.BulkProductAction(
            product_ids=product_ids,
            action="activate"
        )
        result = AdminProductService.bulk_update_products(db, action_data)
        
        # Assert
        assert result.success == 1  # Solo el producto existente
        assert result.failed == 2  # Los dos IDs inexistentes
        assert len(result.errors) == 2
    
    def test_bulk_update_empty_list(self, db: Session):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para operación en lote con lista vacía.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
        """
        # Arrange
        action_data = schemas.BulkProductAction(
            product_ids=[],
            action="activate"
        )
        
        # Act
        result = AdminProductService.bulk_update_products(db, action_data)
        
        # Assert
        assert result.success == 0
        assert result.failed == 0
        assert len(result.errors) == 0


# ==================== PRUEBAS DE INTEGRACIÓN ====================

class TestAdminAPIIntegration:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas de integración de la API de administración.
    """
    
    # --- CORREGIDO: Se usa 'admin_client' y se quita 'client', 'test_admin' y 'patch' ---
    def test_update_product_integration(self, admin_client, db, test_product):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para actualizar producto como admin.
        Parámetros:
            admin_client (TestClient): Cliente HTTP autenticado como admin.
            db (Session): Sesión de base de datos.
            test_product (Product): Producto de prueba.
        """
        # Arrange
        update_data = {
            "price": 799.99,  # JSON puede ser float
            "stock": 75
        }
        
        # Act
        response = admin_client.put(
            f"/api/v1/admin/products/{test_product.product_id}",
            json=update_data
        )
            
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 799.99
        assert data["stock"] == 75

    
    # --- CORREGIDO: Se usa 'admin_client' y se quita 'client', 'test_admin' y 'patch' ---
    def test_delete_product_integration(self, admin_client, db):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para eliminar producto como admin.
        Parámetros:
            admin_client (TestClient): Cliente HTTP autenticado como admin.
            db (Session): Sesión de base de datos.
        """
        # Arrange
        # Crear producto para eliminar
        product = Product(
            name="Producto a Eliminar",
            description="Test",
            brand="Test",
            category="Test",
            physical_activities=["test"],
            fitness_objectives=["test"],
            nutritional_value="Test",
            price=Decimal('100.00'),  # <-- CORREGIDO
            stock=10,
            is_active=True
        )
        db.add(product)
        db.commit()
        
        # Act - Soft delete
        response = admin_client.delete(f"/api/v1/admin/products/{product.product_id}")
            
        # Assert
        assert response.status_code == 204
        
        # Verificar soft delete
        db.refresh(product)
        assert product.is_active is False
    
    # --- CORREGIDO: Se usa 'admin_client' y se quita 'client', 'test_admin' y 'patch' ---
    def test_bulk_action_integration(self, admin_client, db):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para operaciones en lote.
        Parámetros:
            admin_client (TestClient): Cliente HTTP autenticado como admin.
            db (Session): Sesión de base de datos.
        """
        # Arrange
        products = []
        for i in range(3):
            product = Product(
                name=f"Producto Bulk {i+1}",
                description="Test",
                brand="Test",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00'),  # <-- CORREGIDO
                stock=10,
                is_active=False
            )
            db.add(product)
            products.append(product)
        db.commit()
        
        product_ids = [p.product_id for p in products]
        
        bulk_data = {
            "product_ids": product_ids,
            "action": "activate"
        }
        
        # Act
        response = admin_client.post(
            "/api/v1/admin/products/bulk-action",
            json=bulk_data
        )
            
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 3
        assert data["failed"] == 0


# ==================== PRUEBAS FUNCIONALES ====================

class TestAdminFunctional:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas funcionales end-to-end de administración.
    """
    
    def test_admin_product_management_workflow(self, db, test_admin):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional del flujo completo de gestión de productos:
                     crear, actualizar, desactivar y reactivar productos.
        Parámetros:
            db (Session): Sesión de base de datos.
            test_admin (User): Usuario administrador.
        """
        from app.api.v1.products.service import ProductService
        
        # Paso 1: Crear nuevo producto
        product_data = product_schemas.ProductCreate(
            name="Producto Admin Test",
            description="Descripción completa",
            brand="Admin Brand",
            category="Test Category",
            physical_activities=["weightlifting", "crossfit"],
            fitness_objectives=["muscle_gain", "strength"],
            nutritional_value="30g proteína",
            price=Decimal('999.99'),  # <-- CORREGIDO
            stock=100,
            product_images=[
                product_schemas.ProductImageCreate(
                    image_path="https://example.com/admin-product.jpg",
                    is_primary=True
                )
            ]
        )
        
        product = ProductService.create_product(db, product_data)
        assert product.product_id is not None
        assert product.is_active is True
        
        # Paso 2: Actualizar información del producto
        update_data = product_schemas.ProductUpdate(
            price=Decimal('899.99'),  # <-- CORREGIDO
            stock=150,
            description="Descripción actualizada por admin"
        )
        updated_product = ProductService.update_product(
            db,
            product.product_id,
            update_data
        )
        assert updated_product.price == Decimal('899.99')  # <-- CORREGIDO
        assert updated_product.stock == 150
        
        # Paso 3: Desactivar producto (soft delete)
        ProductService.delete_product(db, product.product_id)
        db.refresh(product)
        assert product.is_active is False
        
        # Paso 4: Reactivar producto
        reactivate_data = product_schemas.ProductUpdate(is_active=True)
        reactivated = ProductService.update_product(
            db,
            product.product_id,
            reactivate_data
        )
        assert reactivated.is_active is True
        
        print("✅ Prueba funcional de gestión de productos completada")
    
    def test_bulk_operations_workflow(self, db, test_admin):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional de operaciones masivas de administración.
        Parámetros:
            db (Session): Sesión de base de datos.
            test_admin (User): Usuario administrador.
        """
        # Paso 1: Crear múltiples productos
        products = []
        for i in range(5):
            product = Product(
                name=f"Producto Bulk Test {i+1}",
                description=f"Descripción {i+1}",
                brand="Bulk Brand",
                category="Bulk Category",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00') * (i + 1),  # <-- CORREGIDO
                stock=50,
                is_active=True
            )
            db.add(product)
            products.append(product)
        db.commit()
        
        product_ids = [p.product_id for p in products]
        
        # Paso 2: Desactivar todos en lote
        deactivate_action = schemas.BulkProductAction(
            product_ids=product_ids,
            action="deactivate"
        )
        result = AdminProductService.bulk_update_products(db, deactivate_action)
        assert result.success == 5
        
        # Verificar desactivación
        for product in products:
            db.refresh(product)
            assert product.is_active is False
        
        # Paso 3: Reactivar solo algunos
        products_to_activate = product_ids[:3]
        activate_action = schemas.BulkProductAction(
            product_ids=products_to_activate,
            action="activate"
        )
        result = AdminProductService.bulk_update_products(db, activate_action)
        assert result.success == 3
        
        # Verificar estado mixto
        for i, product in enumerate(products):
            db.refresh(product)
            if i < 3:
                assert product.is_active is True
            else:
                assert product.is_active is False
        
        # Paso 4: Eliminar todos
        delete_action = schemas.BulkProductAction(
            product_ids=product_ids,
            action="delete"
        )
        result = AdminProductService.bulk_update_products(db, delete_action)
        assert result.success == 5
        
        # Verificar eliminación
        for product_id in product_ids:
            deleted = db.query(Product).filter(
                Product.product_id == product_id
            ).first()
            assert deleted is None
        
        print("✅ Prueba funcional de operaciones en lote completada")
    
    def test_inventory_management_workflow(self, db, test_admin):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional de gestión de inventario:
                     actualizar stock, detectar productos con bajo stock.
        Parámetros:
            db (Session): Sesión de base de datos.
            test_admin (User): Usuario administrador.
        """
        # Paso 1: Crear productos con diferentes niveles de stock
        low_stock_products = []
        normal_stock_products = []
        
        for i in range(3):
            # Productos con stock bajo
            product = Product(
                name=f"Producto Stock Bajo {i+1}",
                description="Test",
                brand="Test",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00'),  # <-- CORREGIDO
                stock=5,  # Stock bajo
                is_active=True
            )
            db.add(product)
            low_stock_products.append(product)
            
            # Productos con stock normal
            product = Product(
                name=f"Producto Stock Normal {i+1}",
                description="Test",
                brand="Test",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00'),  # <-- CORREGIDO
                stock=50,  # Stock normal
                is_active=True
            )
            db.add(product)
            normal_stock_products.append(product)
        
        db.commit()
        
        # Paso 2: Detectar productos con stock bajo
        from app.api.v1.analytics.service import AnalyticsService
        
        low_stock_list = AnalyticsService.get_low_stock_products(db, threshold=10)
        assert len(low_stock_list) >= 3
        
        # Paso 3: Actualizar stock de productos con stock bajo
        for product in low_stock_products:
            update_data = product_schemas.ProductUpdate(stock=100)
            ProductService.update_product(db, product.product_id, update_data)
        
        # Paso 4: Verificar que ya no aparecen en la lista de stock bajo
        low_stock_list_after = AnalyticsService.get_low_stock_products(db, threshold=10)
        low_stock_ids_after = [p.product_id for p in low_stock_list_after]
        
        for product in low_stock_products:
            assert product.product_id not in low_stock_ids_after
        
        print("Prueba funcional de gestión de inventario completada")
    
    def test_product_activation_deactivation_workflow(self, db):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional de activación/desactivación masiva de productos.
        Parámetros:
            db (Session): Sesión de base de datos.
        """
        # Paso 1: Crear mezcla de productos activos e inactivos
        all_products = []
        
        for i in range(10):
            product = Product(
                name=f"Producto Mixed {i+1}",
                description="Test",
                brand="Test",
                category="Test",
                physical_activities=["test"],
                fitness_objectives=["test"],
                nutritional_value="Test",
                price=Decimal('100.00'),  # <-- CORREGIDO
                stock=50,
                is_active=(i % 2 == 0)  # Alternando activo/inactivo
            )
            db.add(product)
            all_products.append(product)
        db.commit()
        
        # Paso 2: Obtener solo productos inactivos
        inactive_products = [p for p in all_products if not p.is_active]
        inactive_ids = [p.product_id for p in inactive_products]
        assert len(inactive_products) == 5
        
        # Paso 3: Activar todos los inactivos
        activate_action = schemas.BulkProductAction(
            product_ids=inactive_ids,
            action="activate"
        )
        result = AdminProductService.bulk_update_products(db, activate_action)
        assert result.success == 5
        
        # Paso 4: Verificar que todos están activos
        for product in all_products:
            db.refresh(product)
            assert product.is_active is True
        
        # Paso 5: Desactivar la mitad
        half_ids = [p.product_id for p in all_products[:5]]
        deactivate_action = schemas.BulkProductAction(
            product_ids=half_ids,
            action="deactivate"
        )
        result = AdminProductService.bulk_update_products(db, deactivate_action)
        assert result.success == 5
        
        # Paso 6: Contar productos activos e inactivos
        active_count = sum(1 for p in all_products if p.is_active)
        db_active = db.query(Product).filter(
            Product.is_active == True,
            Product.product_id.in_([p.product_id for p in all_products])
        ).count()
        assert db_active == 5
        
        print("Prueba funcional de activación/desactivación completada")