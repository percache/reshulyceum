from app.core.security import utcnow

from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar_path = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    rating = Column(Integer, default=1000, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_solved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)

    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
