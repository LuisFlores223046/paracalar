from sqlalchemy import Integer, String, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from datetime import datetime
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    
    # ============ KEYS ============
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("categories.category_id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # ============ ATTRIBUTES ============
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # ============ CAMPOS PARA FILTRADO ============
    fitness_objective: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    physical_activity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # ============ SEO Y METADATOS ============
    sku: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # ============ CONTROL ============
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage", 
        back_populates="product", 
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", 
        back_populates="product", 
        cascade="all, delete-orphan"
    )
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")
    
    def __repr__(self) -> str:
        return f"<Product(product_id={self.product_id}, name={self.name})>"