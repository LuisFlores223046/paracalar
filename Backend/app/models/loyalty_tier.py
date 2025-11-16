from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from decimal import Decimal
from app.core.database import Base

class LoyaltyTier(Base):
    __tablename__ = "loyalty_tier"

    # PK
    tier_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes
    tier_level: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    min_points_required: Mapped[int] = mapped_column(Integer, nullable=False)
    points_multiplier: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    free_shipping_threshold: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monthly_coupons_count: Mapped[int] = mapped_column(Integer, nullable=False)
    coupon_discount_percentage: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    user_loyalties: Mapped[List["UserLoyalty"]] = relationship("UserLoyalty", back_populates="loyalty_tier")

    def __repr__(self) -> str:
        return f"<LoyaltyTier(tier_id={self.tier_id}, tier_level={self.tier_level})>"
