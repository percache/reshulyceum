DIFFICULTY_LEVELS = [
    {"key": "very_easy", "label": "Очень легко", "min": 100, "max": 499},
    {"key": "easy", "label": "Легко", "min": 500, "max": 899},
    {"key": "medium", "label": "Средне", "min": 900, "max": 1299},
    {"key": "hard", "label": "Сложно", "min": 1300, "max": 1699},
    {"key": "expert", "label": "Очень сложно", "min": 1700, "max": 3000},
]


def get_difficulty_level(difficulty: int) -> dict[str, int | str]:
    for level in DIFFICULTY_LEVELS:
        if level["min"] <= difficulty <= level["max"]:
            return level
    return DIFFICULTY_LEVELS[-1]


def get_difficulty_bounds(level_key: str) -> tuple[int, int] | None:
    for level in DIFFICULTY_LEVELS:
        if level["key"] == level_key:
            return int(level["min"]), int(level["max"])
    return None
