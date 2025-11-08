from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    
    # ============ KEYS ============
    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    cart_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("shopping_carts.cart_id", ondelete="CASCADE"), 
        nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.product_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # ============ ATTRIBUTES ============
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # ============ CONTROL ============
    added_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    cart: Mapped["ShoppingCart"] = relationship("ShoppingCart", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")
    
    def __repr__(self) -> str:
        return f"<CartItem(item_id={self.item_id}, product_id={self.product_id}, quantity={self.quantity})>"