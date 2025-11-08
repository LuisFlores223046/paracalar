from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class Address(Base):
    __tablename__ = "addresses"
    
    # ============ KEYS ============
    address_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # ============ ATTRIBUTES ============
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # ============ CONTROL ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    
    def __repr__(self) -> str:
        return f"<Address(address_id={self.address_id}, city={self.city}, state={self.state})>"