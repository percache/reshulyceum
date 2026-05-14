from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import utcnow
from app.database import get_db
from app.models import Attempt, Task, User
from app.schemas.attempt import AttemptCreate, AttemptHistoryItem, AttemptResult
from app.services.checker import check_answer
from app.services.gamification import (
    check_achievements,
    level_from_xp,
    update_streak,
)
from app.services.rating import update_ratings

router = APIRouter(prefix="/api/attempts", tags=["attempts"])


@router.post("", response_model=AttemptResult, status_code=201)
def submit_attempt(
    payload: AttemptCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    is_correct = check_answer(payload.answer, task.answer)

    already_solved = (
        db.query(Attempt)
        .filter(
            Attempt.user_id == user.id,
            Attempt.task_id == task.id,
            Attempt.is_correct == True,
        )
        .first()
        is not None
    )

    xp_gained = 0
    rating_delta_val = 0

    if is_correct and not already_solved:
        xp_gained = task.xp_reward
        new_user_rating, new_task_rating = update_ratings(user.rating, task.difficulty, True)
        rating_delta_val = new_user_rating - user.rating
        user.rating = new_user_rating
        task.difficulty = new_task_rating
        user.xp += xp_gained
        user.level = level_from_xp(user.xp)
        update_streak(user, utcnow())
    elif not is_correct:
        new_user_rating, new_task_rating = update_ratings(user.rating, task.difficulty, False)
        rating_delta_val = new_user_rating - user.rating
        user.rating = new_user_rating
        task.difficulty = new_task_rating

    attempt = Attempt(
        user_id=user.id,
        task_id=task.id,
        submitted_answer=payload.answer,
        is_correct=is_correct,
        xp_gained=xp_gained,
        rating_delta=rating_delta_val,
    )
    db.add(attempt)
    db.flush()

    unlocked = check_achievements(db, user, last_task=task) if is_correct else []

    db.commit()
    db.refresh(attempt)

    return AttemptResult(
        id=attempt.id,
        task_id=task.id,
        is_correct=is_correct,
        xp_gained=xp_gained,
        rating_delta=rating_delta_val,
        submitted_answer=payload.answer,
        created_at=attempt.created_at,
        correct_answer=task.answer if is_correct else None,
        explanation=task.explanation if is_correct else None,
        unlocked_achievements=[a.title for a in unlocked],
    )


@router.get("/me", response_model=list[AttemptHistoryItem])
def my_attempts(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Attempt)
        .filter(Attempt.user_id == user.id)
        .order_by(Attempt.created_at.desc())
        .limit(limit)
        .all()
    )
