from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import attempts, auth, stats, tasks
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.gamification import ensure_achievements_seeded
from app.services.schema import ensure_schema_updates
from app.web import routes as web_routes

# Импорт моделей нужен для создания таблиц
from app import models  # noqa: F401

Base.metadata.create_all(bind=engine)
ensure_schema_updates()

app = FastAPI(
    title=settings.app_name,
    description="Платформа подготовки к ЕГЭ по информатике: задачи, автопроверка, рейтинг, геймификация.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(attempts.router)
app.include_router(stats.router)
app.include_router(web_routes.router)


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        ensure_achievements_seeded(db)
    finally:
        db.close()


@app.get("/api/health", tags=["misc"])
def health():
    return {"status": "ok", "app": settings.app_name}
