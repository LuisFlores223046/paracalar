from sqlalchemy import Integer, String, Boolean, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from datetime import date, datetime
from app.core.database import Base
from app.models.enum import UserRole, Gender, AuthType


class User(Base):
    __tablename__ = "users"
    
    # ============ IDENTIFICADORES ============
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    cognito_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    
    # ============ INFORMACIÓN BÁSICA ============
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # ============ INFORMACIÓN PERSONAL ============
    gender: Mapped[Optional[Gender]] = mapped_column(SQLEnum(Gender), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # ============ AUTENTICACIÓN ============
    auth_type: Mapped[AuthType] = mapped_column(SQLEnum(AuthType), default=AuthType.EMAIL, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # ============ ESTADO DE CUENTA ============
    account_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # ============ TIMESTAMPS ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    fitness_profile: Mapped[Optional["FitnessProfile"]] = relationship(
        "FitnessProfile", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    addresses: Mapped[List["Address"]] = relationship(
        "Address", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    payment_methods: Mapped[List["PaymentMethod"]] = relationship(
        "PaymentMethod", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    shopping_cart: Mapped[Optional["ShoppingCart"]] = relationship(
        "ShoppingCart", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email={self.email})>"
    
    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador"""
        return self.role == UserRole.ADMIN