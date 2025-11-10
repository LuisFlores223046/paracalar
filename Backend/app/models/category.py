from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from app.core.database import Base

class Category(Base):
    __tablename__ = "category"

    # PK
    category_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relationships
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category(category_id={self.category_id}, name={self.name})>"