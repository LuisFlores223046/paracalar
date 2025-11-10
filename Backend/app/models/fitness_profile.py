from sqlalchemy import Date, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import date
from app.core.database import Base

class FitnessProfile(Base):
    __tablename__ = "fitness_profile"

    # Keys
    profile_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Attributes
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="fitness_profile")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="fitness_profile", uselist=False)

    def __repr__(self) -> str:
        return f"<FitnessProfile(profile_id={self.profile_id}, user_id={self.user_id})>"
    