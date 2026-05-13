from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, User

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    total_tasks = db.query(Task).count()
    total_users = db.query(User).count()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "total_tasks": total_tasks, "total_users": total_users},
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request, db: Session = Depends(get_db)):
    topics = sorted({t[0] for t in db.query(Task.topic).distinct().all()})
    return templates.TemplateResponse("tasks.html", {"request": request, "topics": topics})


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
def task_page(request: Request, task_id: int):
    return templates.TemplateResponse("task.html", {"request": request, "task_id": task_id})


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@router.get("/leaderboard", response_class=HTMLResponse)
def leaderboard_page(request: Request):
    return templates.TemplateResponse("leaderboard.html", {"request": request})


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
