from sqlalchemy.orm import Session
from app.api.v1.products.service import ReviewService
from app.api.v1.products.schemas import ReviewCreate
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.models.enum import UserRole, AuthType, Gender, PaymentType, OrderStatus
from datetime import date
from decimal import Decimal

# --- Importaciones añadidas para crear la Orden ---
from app.models.order import Order
from app.models.address import Address 
from app.models.payment_method import PaymentMethod
# -------------------------------------------------


def test_review_service_updates_product_rating(db_session: Session):
    """
    Prueba de integración: Crear una reseña debe actualizar 
    automáticamente el 'average_rating' del producto.
    """
    # 1. Setup
    user = User(
        cognito_sub="review-user", email="review@test.com", 
        first_name="Rev", last_name="Test", role=UserRole.USER,
        gender=Gender.MALE, date_of_birth=date(1990, 1, 1),
        auth_type=AuthType.EMAIL, account_status=True
    )
    product = Product(
        name="Producto para reseña", description="Desc", brand="Brand",
        category="Proteínas", nutritional_value="Test", price=100.0, stock=10,
        average_rating=None, # Inicia en None
        # --- FIX 1: Añadir campos NOT NULL ---
        physical_activities=[], 
        fitness_objectives=[]
    )
    db_session.add_all([user, product])
    db_session.commit() # Commit para obtener IDs de usuario y producto

    # --- FIX 2: Crear dependencias para la Orden ---
    address = Address(
        user_id=user.user_id, address_line1="Test St 123", country="Test", 
        state="Test", city="Test", zip_code="12345", 
        recipient_name="Test", phone_number="12345"
    )
    payment = PaymentMethod(
        user_id=user.user_id, payment_type=PaymentType.CREDIT_CARD, 
        provider_ref="test_ref", last_four="1234"
    )
    db_session.add_all([address, payment])
    db_session.commit() # Commit para obtener IDs de dirección y pago

    # Crear Orden falsa
    order = Order(
        user_id=user.user_id, address_id=address.address_id, 
        payment_id=payment.payment_id, subtotal=Decimal(100), 
        shipping_cost=Decimal(10), total_amount=Decimal(110)
    )
    db_session.add(order)
    db_session.commit() # Commit para obtener ID de la orden
    # --- Fin de la creación de dependencias ---


    # --- FIX 3: Pasar el order_id al schema ---
    review_data_1 = ReviewCreate(rating=5, review_text="Excelente", order_id=order.order_id)
    review_data_2 = ReviewCreate(rating=3, review_text="Meh", order_id=order.order_id)

    # 2. Act
    # Crear la primera reseña (rating 5)
    # --- FIX 4: Pasar el order_id al servicio ---
    ReviewService.create_review(
        db=db_session,
        product_id=product.product_id,
        user_id=user.user_id,
        review_data=review_data_1,
        order_id=order.order_id
    )
    
    # Recargar el producto desde la BD para ver el cambio
    db_session.refresh(product)
    assert product.average_rating == Decimal('5.0')
    
    # Crear una segunda reseña (rating 3) por otro usuario (simulado)
    user_2 = User(
        cognito_sub="review-user-2", email="review2@test.com", 
        first_name="Rev2", last_name="Test2", role=UserRole.USER,
        gender=Gender.MALE, date_of_birth=date(1990, 1, 1),
        auth_type=AuthType.EMAIL, account_status=True
    )
    db_session.add(user_2)
    db_session.commit()
    
    # --- FIX 4 (Repetido): Pasar el order_id al servicio ---
    ReviewService.create_review(
        db=db_session,
        product_id=product.product_id,
        user_id=user_2.user_id,
        review_data=review_data_2,
        order_id=order.order_id
    )

    # 3. Assert
    # Recargar el producto de nuevo
    db_session.refresh(product)
    
    # El promedio de (5 + 3) / 2 es 4.0
    assert product.average_rating == Decimal('4.0')