from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.core.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    # ============ KEYS ============
    payment_method_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # ============ ATTRIBUTES ============
    method_type: Mapped[str] = mapped_column(String(50), nullable=False)  # card, paypal, etc
    last_four: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # ============ CONTROL ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    user: Mapped["User"] = relationship("User", back_populates="payment_methods")
    
    def __repr__(self) -> str:
        return f"<PaymentMethod(payment_method_id={self.payment_method_id}, method_type={self.method_type})>"