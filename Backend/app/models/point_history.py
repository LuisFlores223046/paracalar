from sqlalchemy import Integer, Date, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import date
from app.core.database import Base
from .enum import PointEventType

class PointHistory(Base):
    __tablename__ = "point_history"

    point_history_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    loyalty_id: Mapped[int] = mapped_column(ForeignKey("user_loyalty.loyalty_id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("order.order_id", ondelete="SET NULL"), nullable=True)

    points_change: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[PointEventType] = mapped_column(Enum(PointEventType), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)

    user_loyalty: Mapped["UserLoyalty"] = relationship("UserLoyalty", back_populates="point_history")
    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="point_history")

    __table_args__ = (
        CheckConstraint(
            "(event_type = 'earned' AND order_id IS NOT NULL) OR (event_type = 'expired' AND order_id IS NULL)",
            name="check_order_for_event_type"
        ),
    )

    def __repr__(self) -> str:
        return f"<PointHistory(point_history_id={self.point_history_id}, event_type={self.event_type}, points_change={self.points_change})>"