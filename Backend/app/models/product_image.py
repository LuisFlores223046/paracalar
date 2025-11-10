from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ProductImage(Base):
    __tablename__ = "product_image"

    # Keys
    image_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id", ondelete="CASCADE"), nullable=False, index=True)

    # Attributes
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="product_images")

    def __repr__(self) -> str:
        return f"<ProductImage(image_id={self.image_id}, product_id={self.product_id})>"
    