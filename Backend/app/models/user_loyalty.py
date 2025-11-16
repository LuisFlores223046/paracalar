from sqlalchemy import Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import date
from app.core.database import Base

class UserLoyalty(Base):
    __tablename__ = "user_loyalty"

    # Keys
    loyalty_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    tier_id: Mapped[int] = mapped_column(ForeignKey("loyalty_tier.tier_id", ondelete="RESTRICT"), nullable=False)

    # Attributes
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Current available points - can be reset
    points_expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    tier_achieved_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_points_update: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_loyalty")
    loyalty_tier: Mapped["LoyaltyTier"] = relationship("LoyaltyTier", back_populates="user_loyalties")
    point_history: Mapped[List["PointHistory"]] = relationship("PointHistory", back_populates="user_loyalty", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<UserLoyalty(loyalty_id={self.loyalty_id}, user_id={self.user_id}, total_points={self.total_points})>"
