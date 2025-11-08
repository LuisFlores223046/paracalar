from sqlalchemy import Integer, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    # ============ KEYS ============
    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.product_id", ondelete="CASCADE"), 
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # ============ ATTRIBUTES ============
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 estrellas
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ============ CONTROL ============
    date_created: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ============ RELACIONES ============
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review(review_id={self.review_id}, product_id={self.product_id}, rating={self.rating})>"