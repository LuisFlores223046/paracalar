from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import date
from app.core.database import Base

class UserCoupon(Base):
    __tablename__ = "user_coupon"

    # Keys
    user_coupon_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, index=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupon.coupon_id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("order.order_id", ondelete="SET NULL"), nullable=True, unique=True)

    # Attributes
    used_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_coupons")
    coupon: Mapped["Coupon"] = relationship("Coupon", back_populates="user_coupons")
    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="user_coupon")

    def __repr__(self) -> str:
        return f"<UserCoupon(user_coupon_id={self.user_coupon_id}, user_id={self.user_id}, used={self.used_date is not None})>"
