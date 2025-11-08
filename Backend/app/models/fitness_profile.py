from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.core.database import Base


class FitnessProfile(Base):
    __tablename__ = "fitness_profiles"
    
    # ============ KEYS ============
    profile_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True
    )
    
    # ============ ATTRIBUTES ============
    fitness_goal: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    activity_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # ============ CONTROL ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    user: Mapped["User"] = relationship("User", back_populates="fitness_profile")
    
    def __repr__(self) -> str:
        return f"<FitnessProfile(profile_id={self.profile_id}, user_id={self.user_id})>"