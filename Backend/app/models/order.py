from sqlalchemy import Integer, String, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from datetime import datetime
from app.core.database import Base
from app.models.enum import OrderStatus


class Order(Base):
    __tablename__ = "orders"
    
    # ============ KEYS ============
    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # ============ INFORMACIÓN DE LA ORDEN ============
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    tax: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    discount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # ============ INFORMACIÓN DE ENVÍO ============
    shipping_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # ============ CONTROL ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # ============ RELACIONES ============
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="order", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Order(order_id={self.order_id}, status={self.status})>"