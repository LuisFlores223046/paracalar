from app.core.database import Base

# Importar enums primero
from app.models.enum import UserRole, Gender, AuthType, OrderStatus

# Importar modelos en orden de dependencias
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.review import Review
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.fitness_profile import FitnessProfile
from app.models.address import Address
from app.models.payment_method import PaymentMethod
from app.models.notification import Notification

__all__ = [
    "Base",
    # Enums
    "UserRole",
    "Gender",
    "AuthType",
    "OrderStatus",
    # Modelos
    "User",
    "Category",
    "Product",
    "ProductImage",
    "ShoppingCart",
    "CartItem",
    "Review",
    "Order",
    "OrderItem",
    "FitnessProfile",
    "Address",
    "PaymentMethod",
    "Notification",
]