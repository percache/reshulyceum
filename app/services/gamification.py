"""XP, уровни, streaks, достижения."""
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models import Achievement, Attempt, User, UserAchievement


def xp_for_level(level: int) -> int:
    """Сколько суммарно XP нужно для достижения данного уровня."""
    return int(100 * (level - 1) ** 1.5)


def level_from_xp(xp: int) -> int:
    level = 1
    while xp_for_level(level + 1) <= xp:
        level += 1
    return level


def update_streak(user: User, now: datetime) -> None:
    today = now.date()
    last = user.last_solved_at.date() if user.last_solved_at else None
    if last == today:
        return
    if last == today - timedelta(days=1):
        user.current_streak += 1
    else:
        user.current_streak = 1
    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.last_solved_at = now


DEFAULT_ACHIEVEMENTS = [
    {"code": "first_blood", "title": "Первое решение", "description": "Решил первую задачу", "icon": "fa-solid fa-flag-checkered"},
    {"code": "solver_10", "title": "Решатель", "description": "Решил 10 задач", "icon": "fa-solid fa-check-double"},
    {"code": "solver_25", "title": "Знаток", "description": "Решил 25 задач", "icon": "fa-solid fa-user-graduate"},
    {"code": "solver_50", "title": "Мастер", "description": "Решил 50 задач", "icon": "fa-solid fa-graduation-cap"},
    {"code": "solver_100", "title": "Сотня", "description": "Решил 100 задач", "icon": "fa-solid fa-crown"},
    {"code": "streak_3", "title": "Три дня подряд", "description": "Серия 3 дня подряд", "icon": "fa-solid fa-fire-flame-curved"},
    {"code": "streak_7", "title": "Неделя подряд", "description": "Серия 7 дней подряд", "icon": "fa-solid fa-calendar-check"},
    {"code": "streak_30", "title": "Месяц подряд", "description": "Серия 30 дней подряд", "icon": "fa-solid fa-calendar-days"},
    {"code": "level_5", "title": "Пятый уровень", "description": "Достиг 5 уровня", "icon": "fa-solid fa-layer-group"},
    {"code": "level_10", "title": "Десятый уровень", "description": "Достиг 10 уровня", "icon": "fa-solid fa-medal"},
    {"code": "level_20", "title": "Двадцатый уровень", "description": "Достиг 20 уровня", "icon": "fa-solid fa-trophy"},
    {"code": "rating_1500", "title": "Рейтинг 1500", "description": "Рейтинг 1500+", "icon": "fa-solid fa-ranking-star"},
    {"code": "rating_2000", "title": "Рейтинг 2000", "description": "Рейтинг 2000+", "icon": "fa-solid fa-gem"},
    {"code": "expert_solver", "title": "Покоритель экспертов", "description": "Решил задачу сложности 1700+", "icon": "fa-solid fa-mountain"},
    {"code": "sharpshooter", "title": "Снайпер", "description": "Точность 90%+ при 20+ попытках", "icon": "fa-solid fa-bullseye"},
    {"code": "polymath", "title": "Эрудит", "description": "Решил задачи по 5 разным темам", "icon": "fa-solid fa-book-bookmark"},
]


def ensure_achievements_seeded(db: Session) -> None:
    existing = {a.code: a for a in db.query(Achievement).all()}
    for a in DEFAULT_ACHIEVEMENTS:
        achievement = existing.get(a["code"])
        if achievement:
            achievement.title = a["title"]
            achievement.description = a["description"]
            achievement.icon = a["icon"]
        else:
            db.add(Achievement(**a))
    db.commit()


def _unlock(db: Session, user: User, code: str) -> Achievement | None:
    ach = db.query(Achievement).filter(Achievement.code == code).first()
    if not ach:
        return None
    exists = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == ach.id)
        .first()
    )
    if exists:
        return None
    db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
    return ach


def check_achievements(db: Session, user: User, last_task=None) -> List[Achievement]:
    """Проверяет и выдаёт новые достижения. Возвращает список новых."""
    from app.models import Task  # local import to avoid cycle

    unlocked: List[Achievement] = []
    solved_q = db.query(Attempt).filter(Attempt.user_id == user.id, Attempt.is_correct == True)
    solved = solved_q.count()
    total_attempts = db.query(Attempt).filter(Attempt.user_id == user.id).count()

    distinct_topics = (
        db.query(Task.topic)
        .join(Attempt, Attempt.task_id == Task.id)
        .filter(Attempt.user_id == user.id, Attempt.is_correct == True)
        .distinct()
        .count()
    )

    checks = []
    if solved >= 1:
        checks.append("first_blood")
    if solved >= 10:
        checks.append("solver_10")
    if solved >= 25:
        checks.append("solver_25")
    if solved >= 50:
        checks.append("solver_50")
    if solved >= 100:
        checks.append("solver_100")
    if user.current_streak >= 3:
        checks.append("streak_3")
    if user.current_streak >= 7:
        checks.append("streak_7")
    if user.current_streak >= 30:
        checks.append("streak_30")
    if user.level >= 5:
        checks.append("level_5")
    if user.level >= 10:
        checks.append("level_10")
    if user.level >= 20:
        checks.append("level_20")
    if user.rating >= 1500:
        checks.append("rating_1500")
    if user.rating >= 2000:
        checks.append("rating_2000")
    if last_task is not None and getattr(last_task, "difficulty", 0) >= 1700:
        checks.append("expert_solver")
    if total_attempts >= 20 and solved / total_attempts >= 0.9:
        checks.append("sharpshooter")
    if distinct_topics >= 5:
        checks.append("polymath")

    for code in checks:
        ach = _unlock(db, user, code)
        if ach:
            unlocked.append(ach)
    return unlocked
