from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
from datetime import datetime
from app.core.database import Base


class ShoppingCart(Base):
    __tablename__ = "shopping_carts"
    
    # ============ KEYS ============
    cart_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True
    )
    
    # ============ CONTROL ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    user: Mapped["User"] = relationship("User", back_populates="shopping_cart")
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem", 
        back_populates="cart", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ShoppingCart(cart_id={self.cart_id}, user_id={self.user_id})>"