from sqlalchemy import DateTime, Boolean, String, Numeric, Integer, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime, UTC
from decimal import Decimal
from app.core.database import Base
from .enum import OrderStatus

class Order(Base):
    __tablename__ = "order"

    # Keys
    order_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("address.address_id", ondelete="RESTRICT"), nullable=False)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payment_method.payment_id", ondelete="RESTRICT"), nullable=False)
    coupon_id: Mapped[Optional[int]] = mapped_column(ForeignKey("coupon.coupon_id", ondelete="SET NULL"), nullable=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subscription.subscription_id", ondelete="SET NULL"), nullable=True)

    # Attributes
    is_subscription: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    order_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    address: Mapped["Address"] = relationship("Address", back_populates="orders")
    payment_method: Mapped["PaymentMethod"] = relationship("PaymentMethod", back_populates="orders")
    coupon: Mapped[Optional["Coupon"]] = relationship("Coupon", back_populates="orders")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="orders")
    user_coupon: Mapped[Optional["UserCoupon"]] = relationship("UserCoupon", back_populates="order", uselist=False)
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="order", cascade="all, delete-orphan")
    point_history: Mapped[Optional["PointHistory"]] = relationship("PointHistory", back_populates="order", uselist=False)

    # Constraints
    __table_args__ = (
        CheckConstraint( # Ensures that if an order is by subscription, it references it
            "(is_subscription = true AND subscription_id IS NOT NULL) OR (is_subscription = false)",
            name="check_subscription_order"
        ),
    )

    def __repr__(self) -> str:
        return f"<Order(order_id={self.order_id}, user_id={self.user_id}, status={self.order_status}, total={self.total_amount})>"
