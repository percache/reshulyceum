from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AttemptCreate(BaseModel):
    task_id: int
    answer: str = Field(min_length=1, max_length=500)


class AttemptResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    is_correct: bool
    xp_gained: int
    rating_delta: int
    submitted_answer: str
    created_at: datetime
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    unlocked_achievements: List[str] = []


class AttemptHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    is_correct: bool
    xp_gained: int
    created_at: datetime


class UserStats(BaseModel):
    total_attempts: int
    solved_count: int
    accuracy: float
    by_topic: dict
