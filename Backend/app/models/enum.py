from enum import Enum

class UserRole(str, Enum):
    """User role enum"""
    ADMIN = "admin"
    USER = "user"

class AuthType(str, Enum):
    """Authentication type enum"""
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"

class Gender(str, Enum):
    """Gender enum"""
    MALE = "M"
    FEMALE = "F"
    PREFER_NOT_SAY = "prefer_not_say"

class PaymentType(str, Enum):
    """Payment method type enum"""
    PAYPAL = "paypal"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"

class SubscriptionStatus(str, Enum):
    """Subscription status enum"""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class OrderStatus(str, Enum):
    """Order status enum"""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PointEventType(str, Enum):
    """Point history event type enum"""
    EARNED = "earned"
    EXPIRED = "expired"