"""Простая ELO-подобная система для адаптивной сложности."""

K_FACTOR = 32


def expected_score(user_rating: int, task_rating: int) -> float:
    return 1.0 / (1.0 + 10 ** ((task_rating - user_rating) / 400))


def update_ratings(user_rating: int, task_rating: int, won: bool) -> tuple[int, int]:
    """Возвращает (new_user_rating, new_task_rating)."""
    expected = expected_score(user_rating, task_rating)
    actual = 1.0 if won else 0.0
    user_delta = round(K_FACTOR * (actual - expected))
    task_delta = -user_delta
    return user_rating + user_delta, task_rating + task_delta


def rating_delta(user_rating: int, task_rating: int, won: bool) -> int:
    new_user, _ = update_ratings(user_rating, task_rating, won)
    return new_user - user_rating
