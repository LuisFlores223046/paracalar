from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"
    
    # ============ KEYS ============
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("orders.order_id", ondelete="CASCADE"), 
        nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.product_id", ondelete="RESTRICT"), 
        nullable=False
    )
    
    # ============ ATTRIBUTES ============
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)  # Precio al momento de la compra
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    
    # ============ RELACIONES ============
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")
    
    def __repr__(self) -> str:
        return f"<OrderItem(order_item_id={self.order_item_id}, order_id={self.order_id}, product_id={self.product_id})>"