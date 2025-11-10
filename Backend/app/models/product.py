from sqlalchemy import Integer, String, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
from decimal import Decimal
from app.core.database import Base

class Product(Base):
    __tablename__ = "product"
    
    # Keys
    product_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.category_id", ondelete ="RESTRICT"), nullable=False)

    # Attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    nutritional_value: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    product_images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Product(product_id={self.product_id}, name={self.name})>"