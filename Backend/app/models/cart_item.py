from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, UTC
from app.core.database import Base

class CartItem(Base):
    __tablename__ = "cart_item"

    # Keys
    cart_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("shopping_cart.cart_id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id", ondelete="CASCADE"), nullable=False)

    # Attributes
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # Relationships
    shopping_cart: Mapped["ShoppingCart"] = relationship("ShoppingCart", back_populates="cart_items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")

    def __repr__(self) -> str:
        return f"<CartItem(cart_item_id={self.cart_item_id}, product_id={self.product_id}, quantity={self.quantity})>"
