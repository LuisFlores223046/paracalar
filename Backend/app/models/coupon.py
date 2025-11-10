from sqlalchemy import String, Numeric, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from datetime import date
from decimal import Decimal
from app.core.database import Base

class Coupon(Base):
    __tablename__ = "coupon"

    # PK
    coupon_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes
    coupon_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    user_coupons: Mapped[List["UserCoupon"]] = relationship("UserCoupon", back_populates="coupon", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="coupon")

    def __repr__(self) -> str:
        return f"<Coupon(coupon_id={self.coupon_id}, code={self.coupon_code}, discount={self.discount_value})>"
