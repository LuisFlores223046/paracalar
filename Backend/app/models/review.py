from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Review(Base):
    tablename = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 estrellas
    review_text = Column(Text, nullable=True)

    #Control
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    #updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    #Relaciones
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    orders = relationship("Order", back_populates="reviews")

    def repr(self):
        return f"<Review product_id={self.product_id} rating={self.rating}>"