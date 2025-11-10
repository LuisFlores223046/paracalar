from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.core.database import Base

class Address(Base):
    __tablename__ = "address"

    # Keys
    address_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Attributes
    address_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="address")

    def __repr__(self) -> str:
        return f"<Address(address_id={self.address_id}, adress_line1={self.address_line1}, zip_code={self.zip_code})>"
