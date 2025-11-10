from sqlalchemy import Integer, String, Text, Numeric, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, UTC
from app.core.database import Base

class Product(Base):
    __tablename__ = "product"
    
    # Keys
    product_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100)) # Changed to attribute
    physical_activities: Mapped[list] = mapped_column(JSON) # Added - For filtering
    fitness_objectives: Mapped[list] = mapped_column(JSON) # Added - For filtering
    nutritional_value: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(2, 1), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Relationships
    product_images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Product(product_id={self.product_id}, name={self.name})>"