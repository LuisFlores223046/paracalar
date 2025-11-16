from sqlalchemy import String, Boolean, Date, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime, UTC
from typing import Optional, List
from app.core.database import Base
from .enum import UserRole, AuthType, Gender

class User(Base):
    __tablename__ = "user"
    
    # PK
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    auth_type: Mapped[AuthType] = mapped_column(Enum(AuthType), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Null si usa auth externa
    cognito_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False) # Cognito related user
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=True) # Necessary if stripe is used
    first_name:Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    account_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
        
    # Relationships
    fitness_profile: Mapped[Optional["FitnessProfile"]] = relationship("FitnessProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    payment_methods: Mapped[List["PaymentMethod"]] = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    shopping_cart: Mapped[Optional["ShoppingCart"]] = relationship("ShoppingCart", back_populates="user", cascade="all, delete-orphan", uselist=False)
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="user", cascade="all, delete-orphan", uselist=False)
    user_loyalty: Mapped[Optional["UserLoyalty"]] = relationship("UserLoyalty", back_populates="user", cascade="all, delete-orphan", uselist=False)
    user_coupons: Mapped[List["UserCoupon"]] = relationship("UserCoupon", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email={self.email}, name={self.first_name} {self.last_name}>"
