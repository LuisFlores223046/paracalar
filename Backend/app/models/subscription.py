from sqlalchemy import Date, Boolean, Numeric, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import date
from decimal import Decimal
from app.core.database import Base
from .enum import SubscriptionStatus


class Subscription(Base):
    __tablename__ = "subscription"

    # Keys
    subscription_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), unique=True, nullable=False ,index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("fitness_profile.profile_id", ondelete="CASCADE"), unique=True, nullable=False)

    # Attributes
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")
    fitness_profile: Mapped["FitnessProfile"] = relationship("FitnessProfile", back_populates="subscription")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="subscription")

    def __repr__(self) -> str:
        return f"<Subscription(subscription_id={self.subscription_id}, user_id={self.user_id}, status={self.subscription_status})>"
