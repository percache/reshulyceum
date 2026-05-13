from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.services.difficulty import get_difficulty_level


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False, index=True)
    difficulty = Column(Integer, default=1000, nullable=False)
    answer = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    xp_reward = Column(Integer, default=10, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    attempts = relationship("Attempt", back_populates="task", cascade="all, delete-orphan")

    @property
    def difficulty_level(self) -> str:
        return str(get_difficulty_level(self.difficulty)["key"])

    @property
    def difficulty_label(self) -> str:
        return str(get_difficulty_level(self.difficulty)["label"])
