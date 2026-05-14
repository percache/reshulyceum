import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import attempts, auth, stats, tasks
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.gamification import ensure_achievements_seeded
from app.services.schema import ensure_schema_updates
from app.web import routes as web_routes

# Импорт моделей нужен для создания таблиц
from app import models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
log = logging.getLogger("reshulyceum")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    db = SessionLocal()
    try:
        ensure_achievements_seeded(db)
    finally:
        db.close()
    log.info("%s started", settings.app_name)
    yield
    log.info("%s stopped", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=(
        "Платформа подготовки к ЕГЭ по информатике: задачи, автопроверка, "
        "адаптивный ELO-рейтинг, XP и достижения."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(attempts.router)
app.include_router(stats.router)
app.include_router(web_routes.router)


@app.get("/api/health", tags=["misc"])
def health():
    return {"status": "ok", "app": settings.app_name, "version": app.version}


@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api") or request.url.path.startswith("/static"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    return templates.TemplateResponse(request, "404.html", status_code=404)
