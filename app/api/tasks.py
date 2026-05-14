from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_current_user, get_current_user_optional
from app.database import get_db
from app.models import Attempt, Task, User
from app.schemas.task import TaskCreate, TaskFull, TaskPublic, TaskUpdate
from app.services.difficulty import DIFFICULTY_LEVELS, get_difficulty_bounds

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskPublic])
def list_tasks(
    topic: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    min_difficulty: Optional[int] = Query(None, ge=100),
    max_difficulty: Optional[int] = Query(None, le=3000),
    search: Optional[str] = Query(None, max_length=100),
    solved: Optional[bool] = Query(None, description="true — только решённые, false — нерешённые"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    q = db.query(Task)
    if topic:
        q = q.filter(Task.topic == topic)
    if difficulty_level:
        bounds = get_difficulty_bounds(difficulty_level)
        if not bounds:
            raise HTTPException(status_code=400, detail="Unknown difficulty level")
        q = q.filter(Task.difficulty >= bounds[0], Task.difficulty <= bounds[1])
    if min_difficulty is not None:
        q = q.filter(Task.difficulty >= min_difficulty)
    if max_difficulty is not None:
        q = q.filter(Task.difficulty <= max_difficulty)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Task.title.ilike(like), Task.description.ilike(like)))
    if solved is not None and user is not None:
        solved_ids = (
            db.query(Attempt.task_id)
            .filter(Attempt.user_id == user.id, Attempt.is_correct == True)
            .distinct()
        )
        if solved:
            q = q.filter(Task.id.in_(solved_ids))
        else:
            q = q.filter(~Task.id.in_(solved_ids))
    return q.order_by(Task.difficulty).offset(offset).limit(limit).all()


@router.get("/me/solved-ids", response_model=list[int])
def my_solved_task_ids(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """ID всех решённых пользователем задач."""
    rows = (
        db.query(Attempt.task_id)
        .filter(Attempt.user_id == user.id, Attempt.is_correct == True)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


@router.get("/daily", response_model=TaskPublic)
def daily_task(db: Session = Depends(get_db)):
    """Задача дня — детерминированный выбор по дате."""
    from datetime import date

    count = db.query(Task).count()
    if not count:
        raise HTTPException(status_code=404, detail="No tasks")
    seed = date.today().toordinal()
    idx = seed % count
    return db.query(Task).order_by(Task.id).offset(idx).limit(1).one()


@router.get("/topics", response_model=list[str])
def list_topics(db: Session = Depends(get_db)):
    rows = db.query(Task.topic).distinct().all()
    return sorted({r[0] for r in rows})


@router.get("/difficulty-levels")
def list_difficulty_levels():
    return DIFFICULTY_LEVELS


@router.get("/{task_id}", response_model=TaskPublic)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskFull, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskFull)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
