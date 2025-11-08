from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ProductImage(Base):
    __tablename__ = "product_images"
    
    image_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Control
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    product = relationship("Product", back_populates="images")
    
    def __repr__(self):
        return f"<ProductImage product_id={self.product_id}>"
