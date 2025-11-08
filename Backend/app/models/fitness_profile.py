from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class FitnessProfile(Base):
    __tablename__ = "fitness_profiles"
    
    profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    
    fitness_goal = Column(String(100), nullable=True)
    activity_level = Column(String(50), nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    user = relationship("User", back_populates="fitness_profile")
    
    def __repr__(self):
        return f"<FitnessProfile user_id={self.user_id}>"