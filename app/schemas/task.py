from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str
    topic: str = Field(min_length=2, max_length=100)
    difficulty: int = Field(default=1000, ge=100, le=3000)
    xp_reward: int = Field(default=10, ge=1, le=1000)
    explanation: Optional[str] = None


class TaskCreate(TaskBase):
    answer: str = Field(min_length=1, max_length=500)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[int] = None
    xp_reward: Optional[int] = None
    explanation: Optional[str] = None
    answer: Optional[str] = None


class TaskPublic(BaseModel):
    """Task fields visible to students — without `answer`."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    topic: str
    difficulty: int
    difficulty_level: str
    difficulty_label: str
    xp_reward: int
    created_at: datetime


class TaskFull(TaskPublic):
    answer: str
    explanation: Optional[str] = None
