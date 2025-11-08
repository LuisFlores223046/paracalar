from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from datetime import datetime
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"
    
    # ============ KEYS ============
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # ============ ATTRIBUTES ============
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # ============ CONTROL ============
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")
    
    def __repr__(self) -> str:
        return f"<Category(category_id={self.category_id}, name={self.name})>"