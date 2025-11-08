from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    payment_method_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    method_type = Column(String(50), nullable=False)  # card, paypal, etc
    last_four = Column(String(4), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    user = relationship("User", back_populates="payment_methods")
    
    def __repr__(self):
        return f"<PaymentMethod {self.method_type}>"