from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class ProductImage(Base):
    __tablename__ = "product_images"
    
    # ============ KEYS ============
    image_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.product_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # ============ ATTRIBUTES ============
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # ============ CONTROL ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    product: Mapped["Product"] = relationship("Product", back_populates="images")
    
    def __repr__(self) -> str:
        return f"<ProductImage(image_id={self.image_id}, product_id={self.product_id})>"