from sqlalchemy import String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from app.core.database import Base
from .enum import PaymentType

class PaymentMethod(Base):    
    __tablename__ = "payment_method"

    # Keys
    payment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Attributes
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    provider_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    last_four: Mapped[str] = mapped_column(String(4), nullable=True) 
    expiration_date: Mapped[str] = mapped_column(String(7), nullable=True)  # Format: MM/YYYY
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payment_methods")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="payment_method")
    subscriptions: Mapped[List["Subscription"]] = relationship("Subscription", back_populates="payment_method")

    def __repr__(self) -> str:
        return f"<PaymentMethod(payment_id={self.payment_id}, type={self.payment_type}, provider_ref={self.provider_ref})>"
