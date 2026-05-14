from app.core.security import utcnow

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_answer = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    xp_gained = Column(Integer, default=0, nullable=False)
    rating_delta = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="attempts")
    task = relationship("Task", back_populates="attempts")
