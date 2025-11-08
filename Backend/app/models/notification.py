from sqlalchemy import Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    
    # ============ KEYS ============
    notification_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # ============ ATTRIBUTES ============
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # ============ CONTROL ============
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # ============ RELACIONES ============
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    
    def __repr__(self) -> str:
        return f"<Notification(notification_id={self.notification_id}, title={self.title})>"