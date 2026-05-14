from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import utcnow
from app.database import get_db
from app.models import Attempt, Task, User, UserAchievement, Achievement
from app.schemas.attempt import UserStats
from app.schemas.task import TaskPublic
from app.schemas.user import LeaderboardEntry

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats/me", response_model=UserStats)
def my_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total = db.query(Attempt).filter(Attempt.user_id == user.id).count()
    solved = (
        db.query(Attempt.task_id)
        .filter(Attempt.user_id == user.id, Attempt.is_correct == True)
        .distinct()
        .count()
    )
    accuracy = (solved / total * 100) if total else 0.0

    by_topic_rows = (
        db.query(Task.topic, func.count(Attempt.id))
        .join(Attempt, Attempt.task_id == Task.id)
        .filter(Attempt.user_id == user.id, Attempt.is_correct == True)
        .group_by(Task.topic)
        .all()
    )
    by_topic = {topic: count for topic, count in by_topic_rows}

    return UserStats(
        total_attempts=total,
        solved_count=solved,
        accuracy=round(accuracy, 1),
        by_topic=by_topic,
    )


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(User).order_by(User.xp.desc()).limit(limit).all()


@router.get("/recommend", response_model=list[TaskPublic])
def recommend(
    limit: int = 5,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Подбирает задачи под рейтинг пользователя, исключая уже решённые."""
    solved_ids = (
        db.query(Attempt.task_id)
        .filter(Attempt.user_id == user.id, Attempt.is_correct == True)
        .distinct()
    )
    target = user.rating
    candidates = (
        db.query(Task)
        .filter(~Task.id.in_(solved_ids))
        .all()
    )
    candidates.sort(key=lambda t: abs(t.difficulty - target))
    return candidates[:limit]


@router.get("/stats/me/timeline")
def my_timeline(days: int = 14, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """XP и кол-во решённых задач по дням за последние N дней."""
    since = utcnow() - timedelta(days=days - 1)
    attempts = (
        db.query(Attempt)
        .filter(Attempt.user_id == user.id, Attempt.created_at >= since)
        .all()
    )
    buckets: dict[str, dict] = {}
    for i in range(days):
        d = (since + timedelta(days=i)).date().isoformat()
        buckets[d] = {"xp": 0, "solved": 0, "attempts": 0}
    for a in attempts:
        d = a.created_at.date().isoformat()
        if d not in buckets:
            continue
        buckets[d]["xp"] += a.xp_gained
        buckets[d]["attempts"] += 1
        if a.is_correct:
            buckets[d]["solved"] += 1
    return [
        {"date": d, **vals} for d, vals in buckets.items()
    ]


@router.get("/me/achievements")
def my_achievements(
    include_locked: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    unlocked_map = {
        ua.achievement_id: ua.unlocked_at
        for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    }
    if include_locked:
        all_ach = db.query(Achievement).order_by(Achievement.id).all()
        return [
            {
                "code": a.code,
                "title": a.title,
                "description": a.description,
                "icon": a.icon,
                "unlocked_at": unlocked_map.get(a.id),
                "unlocked": a.id in unlocked_map,
            }
            for a in all_ach
        ]

    rows = (
        db.query(Achievement, UserAchievement.unlocked_at)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .filter(UserAchievement.user_id == user.id)
        .order_by(UserAchievement.unlocked_at.desc())
        .all()
    )
    return [
        {
            "code": a.code,
            "title": a.title,
            "description": a.description,
            "icon": a.icon,
            "unlocked_at": dt,
            "unlocked": True,
        }
        for a, dt in rows
    ]
