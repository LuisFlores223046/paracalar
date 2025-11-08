from app.core.database import Base
from app.models.user import User
from app.models.fitness_profile import FitnessProfile  # ← AGREGAR
from app.models.address import Address  # ← AGREGAR
from app.models.payment_method import PaymentMethod  # ← AGREGAR
from app.models.notification import Notification  # ← AGREGAR
from app.models.product import Product
from app.models.category import Category
from app.models.product_image import ProductImage
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.review import Review
from app.models.order_item import OrderItem
from app.models.order import Order

__all__ = [
    "Base",
    "User",
    "FitnessProfile",  # ← AGREGAR
    "Address",  # ← AGREGAR
    "PaymentMethod",  # ← AGREGAR
    "Notification",  # ← AGREGAR
    "Product",
    "Category",
    "ProductImage",
    "ShoppingCart",
    "CartItem",
    "Review",
    "OrderItem",
    "Order",
]