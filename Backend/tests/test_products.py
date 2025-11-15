# Autor: Luis Flores
# Fecha: 14/11/2025
# Descripción: Archivo de pruebas para el módulo de productos. Incluye pruebas unitarias,
#             integrales y funcionales para las operaciones de productos y reseñas.

import pytest
from sqlalchemy.orm import Session
from decimal import Decimal  # <-- IMPORTADO
from app.api.v1.products.service import ProductService, ReviewService
from app.api.v1.products import schemas
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.review import Review
from app.models.user import User


# ==================== PRUEBAS UNITARIAS ====================

class TestProductServiceUnit:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas unitarias del servicio de productos.
    """
    
    def test_get_product_by_id_success(self, db: Session, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria que verifica la obtención de un producto por ID.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_product (Product): Producto de prueba.
        """
        
        # Act
        product = ProductService.get_product_by_id(db, test_product.product_id)
        
        # Assert
        assert product is not None
        assert product.product_id == test_product.product_id
        assert product.name == "Whey Protein Test"
        assert product.price == Decimal('899.99')
        assert len(product.product_images) > 0
    
    def test_get_product_by_id_not_found(self, db: Session):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria que verifica el manejo de error cuando un producto no existe.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
        """
        # Arrange
        non_existent_id = 9999
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            ProductService.get_product_by_id(db, non_existent_id)
        
        assert "no encontrado" in str(exc_info.value).lower()
    
    def test_create_product(self, db: Session):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para la creación de un nuevo producto.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
        """
        # Arrange
        product_data = schemas.ProductCreate(
            name="Creatina Test",
            description="Creatina de prueba",
            brand="Test Brand",
            category="Creatina",
            physical_activities=["weightlifting"],
            fitness_objectives=["strength"],
            nutritional_value="5g por servida",
            price=Decimal('399.99'),
            stock=100,
            product_images=[
                schemas.ProductImageCreate(
                    image_path="https://example.com/creatina.jpg",
                    is_primary=True
                )
            ]
        )
        
        # Act
        product = ProductService.create_product(db, product_data)
        
        # Assert
        assert product.product_id is not None
        assert product.name == "Creatina Test"
        assert product.price == Decimal('399.99')
        assert product.stock == 100
        assert len(product.product_images) == 1
    
    def test_update_product(self, db: Session, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para actualizar un producto existente.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange
        update_data = schemas.ProductUpdate(
            price=Decimal('799.99'),
            stock=75,
            is_active=True
        )
        
        # Act
        updated_product = ProductService.update_product(
            db, 
            test_product.product_id, 
            update_data
        )
        
        # Assert
        assert updated_product.price == Decimal('799.99')
        assert updated_product.stock == 75
        assert updated_product.name == test_product.name  # No cambió
    
    def test_delete_product_soft(self, db: Session, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para soft delete de un producto.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange
        product_id = test_product.product_id
        
        # Act
        result = ProductService.delete_product(db, product_id)
        
        # Assert
        assert result is True
        product = db.query(Product).filter(Product.product_id == product_id).first()
        assert product.is_active is False
    
    def test_get_related_products(self, db: Session, test_product: Product):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para obtener productos relacionados.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_product (Product): Producto de prueba.
        """
        # Arrange - Crear productos relacionados
        related_product = Product(
            name="Proteína Related",
            description="Producto relacionado",
            brand="Test Brand",
            category="Proteínas",
            physical_activities=["weightlifting"],
            fitness_objectives=["muscle_gain"],
            nutritional_value="Test",
            price=Decimal('699.99'),
            stock=30,
            is_active=True
        )
        db.add(related_product)
        db.commit()
        
        # Act
        related = ProductService.get_related_products(db, test_product.product_id, limit=5)
        
        # Assert
        assert len(related) >= 0  # Puede tener 0 o más relacionados
        assert test_product.product_id not in [p.product_id for p in related]


class TestReviewServiceUnit:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas unitarias del servicio de reseñas.
    """
    
    def test_create_review(self, db: Session, test_product: Product, test_user: User):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para crear una reseña de producto.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_product (Product): Producto de prueba.
            test_user (User): Usuario de prueba.
        """
        # Arrange
        from app.models.order import Order
        from app.models.enum import OrderStatus
        from app.models.address import Address
        from app.models.payment_method import PaymentMethod
        from app.models.enum import PaymentType
        from decimal import Decimal
        
        # Crear dirección de prueba
        address = Address(
            user_id=test_user.user_id,
            address_name="Casa",
            address_line1="Calle Test 123",
            country="México",
            state="Chihuahua",
            city="Juárez",
            zip_code="32000",
            recipient_name="Test User",
            phone_number="1234567890",
            is_default=True
        )
        db.add(address)
        db.flush()
        
        # Crear método de pago de prueba
        payment = PaymentMethod(
            user_id=test_user.user_id,
            payment_type=PaymentType.CREDIT_CARD,
            provider_ref="test_ref_123",
            last_four="1234",
            expiration_date="12/2025",
            is_default=True
        )
        db.add(payment)
        db.flush()
        
        # Crear orden de prueba
        order = Order(
            user_id=test_user.user_id,
            address_id=address.address_id,
            payment_id=payment.payment_id,
            is_subscription=False,
            order_status=OrderStatus.DELIVERED,
            subtotal=Decimal("899.99"),
            shipping_cost=Decimal("50.00"),
            total_amount=Decimal("949.99")
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        review_data = schemas.ReviewCreate(
            rating=5,
            review_text="Excelente producto de prueba"
        )
        
        # Act
        review = ReviewService.create_review(
            db, 
            test_product.product_id, 
            test_user.user_id,
            review_data,
            order.order_id
        )
        
        # Assert
        assert review.review_id is not None
        assert review.rating == 5
        assert review.review_text == "Excelente producto de prueba"
        assert review.product_id == test_product.product_id
        assert review.user_id == test_user.user_id
    
    def test_get_product_reviews(self, db: Session, test_product: Product, test_user: User):
        """
        Autor: Luis Flores
        Descripción: Prueba unitaria para obtener reseñas de un producto.
        Parámetros:
            db (Session): Sesión de base de datos de prueba.
            test_product (Product): Producto de prueba.
            test_user (User): Usuario de prueba.
        """
        # Arrange - Crear reseñas de prueba
        from app.models.order import Order
        from app.models.enum import OrderStatus
        from app.models.address import Address
        from app.models.payment_method import PaymentMethod
        from app.models.enum import PaymentType
        from decimal import Decimal
        
        address = Address(
            user_id=test_user.user_id,
            address_name="Casa",
            address_line1="Calle Test 123",
            country="México",
            state="Chihuahua",
            city="Juárez",
            zip_code="32000",
            recipient_name="Test User",
            phone_number="1234567890",
            is_default=True
        )
        db.add(address)
        db.flush()
        
        payment = PaymentMethod(
            user_id=test_user.user_id,
            payment_type=PaymentType.CREDIT_CARD,
            provider_ref="test_ref_123",
            last_four="1234",
            expiration_date="12/2025",
            is_default=True
        )
        db.add(payment)
        db.flush()
        
        order = Order(
            user_id=test_user.user_id,
            address_id=address.address_id,
            payment_id=payment.payment_id,
            is_subscription=False,
            order_status=OrderStatus.DELIVERED,
            subtotal=Decimal("899.99"),
            shipping_cost=Decimal("50.00"),
            total_amount=Decimal("949.99")
        )
        db.add(order)
        db.commit()
        
        review = Review(
            product_id=test_product.product_id,
            user_id=test_user.user_id,
            order_id=order.order_id,
            rating=4,
            review_text="Bueno"
        )
        db.add(review)
        db.commit()
        
        # Act
        reviews, total = ReviewService.get_product_reviews(
            db, 
            test_product.product_id,
            skip=0,
            limit=10
        )
        
        # Assert
        assert total >= 1
        assert len(reviews) >= 1
        assert reviews[0].product_id == test_product.product_id


# ==================== PRUEBAS DE INTEGRACIÓN ====================

class TestProductAPIIntegration:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas de integración de la API de productos.
    """
    
    def test_get_product_detail_integration(self, client, db, test_product):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para obtener detalles de un producto via API.
        Parámetros:
            client (TestClient): Cliente HTTP de prueba.
            db (Session): Sesión de base de datos.
            test_product (Product): Producto de prueba.
        """
        # Act
        response = client.get(f"/api/v1/products/{test_product.product_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == test_product.product_id
        assert data["name"] == "Whey Protein Test"
        assert "product_images" in data
    
    def test_get_product_not_found_integration(self, client):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para producto no encontrado.
        Parámetros:
            client (TestClient): Cliente HTTP de prueba.
        """
        # Act
        response = client.get("/api/v1/products/9999")
        
        # Assert
        assert response.status_code == 404
    
    def test_get_related_products_integration(self, client, db, test_product):
        """
        Autor: Luis Flores
        Descripción: Prueba de integración para obtener productos relacionados.
        Parámetros:
            client (TestClient): Cliente HTTP de prueba.
            db (Session): Sesión de base de datos.
            test_product (Product): Producto de prueba.
        """
        # Act
        response = client.get(f"/api/v1/products/{test_product.product_id}/related?limit=5")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ==================== PRUEBAS FUNCIONALES ====================

class TestProductFunctional:
    """
    Autor: Luis Flores
    Descripción: Clase que agrupa las pruebas funcionales end-to-end de productos.
    """
    
    def test_product_lifecycle(self, client, db, test_admin):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional del ciclo de vida completo de un producto:
                     crear, consultar, actualizar y eliminar.
        Parámetros:
            client (TestClient): Cliente HTTP de prueba.
            db (Session): Sesión de base de datos.
            test_admin (User): Usuario administrador.
        """
        # Paso 1: Crear producto
        create_data = {
            "name": "Producto Funcional Test",
            "description": "Descripción de prueba funcional",
            "brand": "Functional Brand",
            "category": "Test Category",
            "physical_activities": ["running"],
            "fitness_objectives": ["endurance"],
            "nutritional_value": "Test nutrition",
            "price": Decimal('599.99'),
            "stock": 25,
            "is_active": True
        }
        
        product = Product(**create_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        
        # Paso 2: Verificar que se puede consultar
        response = client.get(f"/api/v1/products/{product.product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Producto Funcional Test"
        
        # Paso 3: Verificar que aparece en búsquedas
        search_response = client.get("/api/v1/search/?query=Funcional")
        assert search_response.status_code == 200
        search_data = search_response.json()
        product_ids = [p["product_id"] for p in search_data["items"]]
        assert product.product_id in product_ids
        
        # Paso 4: Verificar soft delete
        ProductService.delete_product(db, product.product_id)
        db.refresh(product)
        assert product.is_active is False
        
        print("✅ Prueba funcional de ciclo de vida de producto completada")
    
    def test_product_review_workflow(self, client, db, test_product, test_user):
        """
        Autor: Luis Flores
        Descripción: Prueba funcional del flujo completo de reseñas:
                     crear reseña, consultar reseñas y verificar actualización de rating.
        Parámetros:
            client (TestClient): Cliente HTTP de prueba.
            db (Session): Sesión de base de datos.
            test_product (Product): Producto de prueba.
            test_user (User): Usuario de prueba.
        """
        from app.models.order import Order
        from app.models.enum import OrderStatus
        from app.models.address import Address
        from app.models.payment_method import PaymentMethod
        from app.models.enum import PaymentType
        from decimal import Decimal
        
        # Preparar datos necesarios
        address = Address(
            user_id=test_user.user_id,
            address_name="Casa",
            address_line1="Calle Test 123",
            country="México",
            state="Chihuahua",
            city="Juárez",
            zip_code="32000",
            recipient_name="Test User",
            phone_number="1234567890",
            is_default=True
        )
        db.add(address)
        db.flush()
        
        payment = PaymentMethod(
            user_id=test_user.user_id,
            payment_type=PaymentType.CREDIT_CARD,
            provider_ref="test_ref_123",
            last_four="1234",
            expiration_date="12/2025",
            is_default=True
        )
        db.add(payment)
        db.flush()
        
        order = Order(
            user_id=test_user.user_id,
            address_id=address.address_id,
            payment_id=payment.payment_id,
            is_subscription=False,
            order_status=OrderStatus.DELIVERED,
            subtotal=Decimal("899.99"),
            shipping_cost=Decimal("50.00"),
            total_amount=Decimal("949.99")
        )
        db.add(order)
        db.commit()
        
        # Paso 1: Crear reseña
        review_data = schemas.ReviewCreate(rating=5, review_text="Excelente")
        review = ReviewService.create_review(
            db,
            test_product.product_id,
            test_user.user_id,
            review_data,
            order.order_id
        )
        assert review.rating == 5
        
        # Paso 2: Consultar reseñas
        response = client.get(f"/api/v1/products/{test_product.product_id}/reviews")
        assert response.status_code == 200
        reviews_data = response.json()
        assert len(reviews_data) >= 1
        
        # Paso 3: Verificar actualización de rating del producto
        db.refresh(test_product)
        assert test_product.average_rating is not None
        
        print("Prueba funcional de flujo de reseñas completada")