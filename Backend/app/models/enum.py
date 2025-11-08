from enum import Enum as PyEnum


class UserRole(str, PyEnum):
    """Roles de usuario en el sistema"""
    USER = "user"
    ADMIN = "admin"


class Gender(str, PyEnum):
    """Género del usuario"""
    MALE = "M"
    FEMALE = "F"
    PREFER_NOT_SAY = "prefer_not_say"


class AuthType(str, PyEnum):
    """Tipo de autenticación del usuario"""
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"


class OrderStatus(str, PyEnum):
    """Estados de las órdenes"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"