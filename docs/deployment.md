# Развёртывание и хостинг

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed_data
python run.py
```

Приложение будет доступно по адресу `http://127.0.0.1:8000`.

## Docker Compose

```bash
docker compose up --build
```

Приложение будет доступно по адресу `http://127.0.0.1:8000`.

## Подготовка к хостингу

Для хостинга можно использовать Render, Railway, VPS или другой сервис, который поддерживает Docker или Python-приложения.

Переменные окружения:
- `DATABASE_URL` — адрес базы данных. Для SQLite в Docker используется `sqlite:////data/reshulyceum.db`.
- `SECRET_KEY` — секретный ключ JWT. На хостинге нужно заменить на длинную случайную строку.

Команда запуска без Docker:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Что приложить при сдаче
- Ссылку на git-репозиторий.
- Ссылку на запущенное приложение, если преподаватель требует публичный хостинг.
- Пояснительную записку из `docs/explanatory_note.md`.
- План презентации из `docs/presentation_plan.md`.
- Задание проекта из `docs/project_task.md`.
