from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.enum import UserRole, Gender, AuthType


class User(Base):
    __tablename__ = "users"
    
    # ============ IDENTIFICADORES ============
    user_id = Column(Integer, primary_key=True, index=True)
    cognito_sub = Column(String(255), unique=True, nullable=True, index=True)  # Sub de Cognito
    
    # ============ INFORMACIÓN BÁSICA ============
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Null si usa OAuth
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # ============ INFORMACIÓN PERSONAL ============
    gender = Column(Enum(Gender), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    profile_picture = Column(String(500), nullable=True)
    
    # ============ AUTENTICACIÓN ============
    auth_type = Column(Enum(AuthType), default=AuthType.EMAIL, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # ============ ESTADO DE CUENTA ============
    account_status = Column(Boolean, default=True, nullable=False)  # is_active
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # ============ TIMESTAMPS ============
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    fitness_profile = relationship(
        "FitnessProfile", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    addresses = relationship(
        "Address", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    payment_methods = relationship(
        "PaymentMethod", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    shopping_cart = relationship(
        "ShoppingCart", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    orders = relationship(
        "Order", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def full_name(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == UserRole.ADMIN