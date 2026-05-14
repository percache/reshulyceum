# ReshuLyceum

**Платформа подготовки к ЕГЭ по информатике** с автопроверкой, адаптивной сложностью, загрузкой файлов и геймификацией.

> Итоговый проект: WebServer + API. Стек — FastAPI + SQLAlchemy + Jinja2 + SQLite.

## Фишки

- **Адаптивная сложность** — алгоритм ELO подбирает задачи под уровень ученика
- **Геймификация** — опыт (XP), уровни, серии (streaks), 8 достижений
- **Личная аналитика** — по темам, точности, истории попыток
- **JWT-авторизация** с ролями (user / admin)
- **Загрузка файлов** — аватар пользователя в личном кабинете
- **Полноценный REST API** + автогенерируемый Swagger UI на `/docs`
- **Современный тёмный UI** на Jinja2 + Bootstrap + чистом JS

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed_data        # БД + демо-задачи + админ admin/admin123
python run.py                       # → http://127.0.0.1:8000
```

После запуска:
- **/** — главная
- **/tasks** — каталог задач
- **/profile** — личный кабинет (после входа)
- **/leaderboard** — лидерборд
- **/docs** — Swagger UI (Open API)

## Тесты

```bash
pytest -v
```

## Структура

```
app/
├── main.py              # FastAPI приложение
├── config.py            # настройки (Pydantic Settings)
├── database.py          # SQLAlchemy engine + сессии
├── models/              # ORM-модели (User, Task, Attempt, Achievement)
├── schemas/             # Pydantic-схемы запросов/ответов
├── core/
│   ├── security.py      # хэширование паролей, JWT
│   └── deps.py          # FastAPI-зависимости (auth)
├── api/                 # REST-эндпоинты
│   ├── auth.py          # /register, /login, /me
│   ├── tasks.py         # CRUD задач
│   ├── attempts.py      # сдача решения + автопроверка
│   └── stats.py         # статистика, лидерборд, рекомендации
├── services/
│   ├── checker.py       # автопроверка ответа
│   ├── rating.py        # ELO-рейтинг задач/пользователей
│   ├── gamification.py  # XP, уровни, streaks, достижения
│   ├── difficulty.py    # уровни сложности задач
│   └── schema.py        # безопасное обновление SQLite-схемы
├── web/routes.py        # HTML-страницы (Jinja2)
├── templates/           # шаблоны страниц
└── static/              # CSS, JS, загруженные файлы
docs/                    # задание, пояснительная записка, план защиты
scripts/seed_data.py     # сидинг демо-данных
tests/test_api.py        # автотесты
```

## API

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/auth/register` | регистрация |
| POST | `/api/auth/login` | логин (форма OAuth2) → JWT |
| GET  | `/api/auth/me` | текущий пользователь |
| POST | `/api/auth/me/avatar` | загрузить аватар |
| POST | `/api/auth/me/password` | смена пароля |
| GET  | `/api/tasks` | список задач (фильтры: topic, difficulty_level, difficulty, search, solved) |
| GET  | `/api/tasks/topics` | список тем |
| GET  | `/api/tasks/difficulty-levels` | уровни сложности |
| GET  | `/api/tasks/daily` | **задача дня** |
| GET  | `/api/tasks/me/solved-ids` | id решённых мной задач |
| GET  | `/api/tasks/{id}` | задача по id |
| POST | `/api/tasks` | создать (admin) |
| PATCH| `/api/tasks/{id}` | обновить (admin) |
| DELETE| `/api/tasks/{id}` | удалить (admin) |
| POST | `/api/attempts` | сдать решение → автопроверка + XP + достижения |
| GET  | `/api/attempts/me` | мои попытки |
| GET  | `/api/stats/me` | моя статистика |
| GET  | `/api/stats/me/timeline` | XP/решённые по дням |
| GET  | `/api/leaderboard` | топ игроков |
| GET  | `/api/recommend` | рекомендуемые задачи под мой рейтинг |
| GET  | `/api/me/achievements` | мои достижения (`?include_locked=true` — вкл. закрытые) |
| GET  | `/api/health` | health-check |

## Алгоритмы

### ELO-рейтинг (адаптивная сложность)

Пользователь и задача имеют рейтинги (начальный — 1000). После каждой попытки:
- Ожидаемый "результат": `E = 1 / (1 + 10^((R_task - R_user)/400))`
- Дельта: `Δ = K * (actual - E)`, K=32
- Решил сложную → +много рейтинга, задача становится легче
- Не решил лёгкую → -много, задача становится сложнее

### Уровни от XP

`XP_to_level(L) = 100 * (L-1)^1.5` — нелинейный рост.

### Streaks (серии)

Если последняя решённая задача была вчера — `+1` к серии; иначе сброс.

## Безопасность

- Пароли — bcrypt
- JWT с истечением (7 дней)
- Эталонные ответы скрыты в `TaskPublic` (выдаются только после правильного решения)
- Admin-only эндпоинты защищены отдельной зависимостью
- Аватары ограничены форматами JPG, PNG, WEBP и размером 2 МБ

## Соответствие критериям

| Требование | Реализация |
|---|---|
| `requirements.txt` | Все зависимости перечислены в `requirements.txt` |
| Bootstrap или аналог | Подключён Bootstrap, используется вместе с собственным CSS |
| ORM-модели | SQLAlchemy-модели в `app/models` |
| Регистрация и авторизация | JWT-auth в `app/api/auth.py` |
| Загрузка и использование файлов | Загрузка аватара пользователя в `/api/auth/me/avatar` |
| REST API | API доступен на `/docs` |
| Хранение данных | SQLite-база `reshulyceum.db` |
| Хостинг/развёртывание | Есть `Dockerfile` и `docker-compose.yml` |
| Тесты | `pytest -v` |
| Документы | `docs/project_task.md`, `docs/explanatory_note.md`, `docs/presentation_plan.md`, `docs/deployment.md` |

## Что показывать на защите

1. Запустить `seed_data`, открыть `/docs` — показать Swagger UI с группами эндпоинтов
2. На `/` показать SPA-ощущение, регистрация → автовход
3. На `/tasks` нажать **"Рекомендовать мне"** — пояснить ELO
4. Сдать неверный → верный ответ, показать всплывающее достижение
5. Открыть профиль — статистика по темам, прогресс, история
6. Открыть лидерборд
7. Залогиниться как `admin/admin123`, через `/docs` создать задачу через `POST /api/tasks`
8. Показать тесты: `pytest -v`
9. Объяснить структуру слоёв: routes → schemas → services → models
