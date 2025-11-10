from sqlalchemy import Integer, ForeignKey, Numeric, Text, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date
from typing import Optional
from decimal import Decimal
from app.core.database import Base

class Review(Base):
    __tablename__ = "review"

    # Keys
    review_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.order_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    # Attributes
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)  # 1-5 star rating including halves
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_updated: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    order: Mapped["Order"] = relationship("Order", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review(review_id={self.review_id}, product_id={self.product_id}, rating={self.rating})>"