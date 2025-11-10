from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, UTC
from typing import List
from app.core.database import Base

class ShoppingCart(Base):
    __tablename__ = "shopping_cart"
    
    # Keys
    cart_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Attributes
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC)) # Changed from utcnow to .now(UTC) because its deprecated
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="shopping_cart")
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="shopping_cart", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ShoppingCart(cart_id={self.cart_id}, user_id={self.user_id})>"