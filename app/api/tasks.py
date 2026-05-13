from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_current_user
from app.database import get_db
from app.models import Task, User
from app.schemas.task import TaskCreate, TaskFull, TaskPublic, TaskUpdate
from app.services.difficulty import DIFFICULTY_LEVELS, get_difficulty_bounds

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskPublic])
def list_tasks(
    topic: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    min_difficulty: Optional[int] = Query(None, ge=100),
    max_difficulty: Optional[int] = Query(None, le=3000),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
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
    return q.order_by(Task.difficulty).offset(offset).limit(limit).all()


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
