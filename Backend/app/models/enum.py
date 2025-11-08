from enum import Enum


class UserRole(str, Enum):
    """Roles de usuario en el sistema"""
    USER = "user"
    ADMIN = "admin"


class Gender(str, Enum):
    """Género del usuario"""
    MALE = "M"
    FEMALE = "F"
    PREFER_NOT_SAY = "prefer_not_say"


class AuthType(str, Enum):
    """Tipo de autenticación del usuario"""
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"


class OrderStatus(str, Enum):
    """Estados de las órdenes"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
