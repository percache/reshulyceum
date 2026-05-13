from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    avatar_path: Optional[str] = None
    is_admin: bool
    xp: int
    level: int
    rating: int
    current_streak: int
    longest_streak: int
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    xp: int
    level: int
    rating: int
