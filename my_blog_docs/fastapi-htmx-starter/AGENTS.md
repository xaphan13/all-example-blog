# AGENTS.md — Правила работы с кодовой базой

> Этот файл предназначен для ИИ-ассистентов (агентов), работающих с данным репозиторием.
> **Важно: подробная документация проекта уже существует в папке [`docs/`](docs/) — обязательно изучите её перед внесением изменений.** Этот файл содержит сводку и правила, а не замену документации.

---

## 1. Что это за проект

`fastapi-htmx-starter` — стартовый шаблон (boilerplate) для сервер-сайд рендерящихся веб-приложений на стеке:

| Технология | Роль |
|---|---|
| **FastAPI** (>=0.115) | Веб-фреймворк: маршрутизация, DI, middleware |
| **HTMX 2.x** | Частичные обновления UI без JavaScript-фреймворков |
| **Jinja2** | Сервер-сайд рендеринг HTML (шаблоны в `app/templates/`) |
| **TailwindCSS** | Стили (Play CDN — не для production) |
| **SQLAlchemy 2.0 (async)** | ORM; драйверы `aiosqlite` (default) / `asyncpg` |
| **Alembic** | Миграции БД (async-режим) |
| **fastapi-users** | Аутентификация: cookie + JWT, регистрация, UserManager |
| **Pydantic Settings** | Конфигурация через `.env` |

Архитектура — **слоистый монолит с SSR**: маршруты (`app/api/`) → модели/схемы (`app/models/`, `app/schemas/`) → БД. Бизнес-логика находится **в route-хендлерах**; `app/services/` существует, но пуст (зарезервирован).

Python **3.12+**, пакетный менеджер — **uv**.

---

## 2. Обязательный порядок действий для агента

1. **Прочитать документацию** перед любыми изменениями — в `docs/` уже всё описано:

   | Файл | Содержимое |
   |---|---|
   | [`docs/01_project_structure.md`](docs/01_project_structure.md) | Карта проекта: дерево файлов, все зависимости и их роли |
   | [`docs/02_architecture.md`](docs/02_architecture.md) | Архитектура, паттерны (DI, Strategy, Template Inheritance), поток данных, конфигурация |
   | [`docs/03_execution_flow.md`](docs/03_execution_flow.md) | Жизненный цикл приложения, бизнес-процессы, **полная таблица роутов**, обработка ошибок |
   | [`docs/04_code_quality.md`](docs/04_code_quality.md) | Оценка качества, технический долг, аудит безопасности |
   | [`docs/05_optimization_roadmap.md`](docs/05_optimization_roadmap.md) | Приоритизированный план рефакторинга и улучшений |
   | [`docs/06_alembic.md`](docs/06_alembic.md) | Миграции: конфигурация, команды, рабочий процесс |
   | [`docs/07_frontend.md`](docs/07_frontend.md) | Фронтенд: шаблоны, HTMX-карта, стили, JS, найденные проблемы |

2. **Не дублировать документацию**: если после изменений описание в `docs/` устарело — обновить соответствующий файл `docs/`, а не создавать новые.

3. **Следовать существующему стилю кода** (см. раздел 5).

---

## 3. Ключевые факты о структуре

```
app/
├── main.py            # Точка входа: FastAPI(), lifespan, роутеры, exception handler, GZip
├── cli.py             # CLI: serve, test, lint, format, check-types (subprocess)
├── api/               # Route handlers
│   ├── auth.py        # Страницы login/register, POST /register, POST /logout
│   ├── items.py       # CRUD Item: list (search+pagination), create, edit, update, delete, cancel
│   ├── user.py        # GET /profile, PATCH /profile/email, PATCH /profile/password
│   └── dependencies.py# is_htmx(request); NB: get_db здесь — мёртвый код, реальный в core/database.py
├── core/              # Инфраструктура
│   ├── config.py      # Settings: DATABASE_URL, SECRET_KEY (runtime-default!)
│   ├── database.py    # async engine, AsyncSessionLocal, Base, get_db(), init_db()
│   ├── templates.py   # Jinja2Templates("app/templates")
│   └── users.py       # fastapi-users: CookieTransport, JWTStrategy, auth_backend
├── models/            # SQLAlchemy: user.py (User + UserManager), item.py (Item)
├── schemas/           # Pydantic v2: user.py, item.py
├── services/          # ПУСТО — зарезервировано
├── static/css/        # custom.css
├── templates/         # base.jinja2, index.jinja2, profile.jinja2, auth/, items/ (partials _table, _item_row, _edit_form), partials/
└── tests/             # conftest.py, test_main.py (4 smoke-теста)
alembic/               # env.py (async), versions/ — ПУСТА, миграций нет
```

Полное дерево с пояснениями: [`docs/01_project_structure.md`](docs/01_project_structure.md).

---

## 4. Команды

```bash
uv run serve          # dev-сервер с hot reload (http://localhost:8000)
uv run test           # тесты (pytest, asyncio_mode=auto)
uv run lint           # ruff
uv run format         # black + isort
uv run check-types    # mypy

# Миграции (детали: docs/06_alembic.md)
alembic revision --autogenerate -m "..."
alembic upgrade head
alembic downgrade -1
```

Установка: `uv venv && source .venv/bin/activate && uv pip install -e .`
Конфигурация: `cp .env.example .env` (обязательно задать `SECRET_KEY`, иначе он генерируется заново при каждом старте и все сессии инвалидируются).

---

## 5. Правила и конвенции

### Стиль кода

- Python 3.12+: union-типы через `str | None`, generics через `list[...]` (НЕ `Optional`/`List` из `typing` — в коде есть несогласованные места, новые не создавать).
- SQLAlchemy 2.0 стиль: `Mapped[...]` / `mapped_column`, `select()` вместо legacy `Query`.
- Async-first: весь DB-слой асинхронный (`AsyncSession`, `await db.execute(...)`).
- Форматирование: `black` (line-length=88), `isort` (profile=black), `ruff`, `mypy`. Pre-commit hooks настроены (`.pre-commit-config.yaml`).
- Шаблоны Jinja2: линтятся `djlint` (profile=jinja, indent=2).

### Архитектурные правила

- **Роуты возвращают HTML**: HTMX-запросы (`HX-Request: true`) получают partial-шаблон, обычные — полную страницу. Проверка через зависимость `is_htmx()` (`app/api/dependencies.py`).
- **Аутентификация**: защищённые роуты используют `current_user(active=True)` из `app/core/users.py`. Все запросы к `Item` фильтруются по `owner_id == user.id` — не нарушать owner isolation.
- **Схема БД**: модели меняются в `app/models/`, затем генерируется миграция Alembic. NB: `init_db()` (`create_all`) дублирует Alembic — это известный техдолг (см. `docs/04_code_quality.md`).
- **DI**: сессии БД через `get_db()` из `app/core/database.py`, конфигурация через `settings` из `app/core/config.py`.

### Известные проблемы (не воспроизводить в новом коде)

Подробный список с указанием файлов — в [`docs/04_code_quality.md`](docs/04_code_quality.md). Кратко:

- ❌ Inline HTML через f-strings в route-хендлерах (`app/api/user.py`) — XSS-риск; рендерить через Jinja2-шаблоны.
- ❌ `dict[str, Any]` в теле запроса вместо Pydantic-схем (`app/api/user.py`).
- ❌ Копипаста логики пагинации в `app/api/items.py` (3 раза) — при рефакторинге выносить в `app/services/pagination.py`.
- ❌ `datetime.utcnow()` — deprecated; использовать `datetime.now(timezone.utc)`.
- ❌ Отсутствие CSRF-защиты и `Secure`-флага у cookie — известные уязвимости, план исправления в `docs/05_optimization_roadmap.md`.

### Приоритеты развития

Перед крупными изменениями сверяйтесь с [`docs/05_optimization_roadmap.md`](docs/05_optimization_roadmap.md): выделение сервисного слоя, устранение дублирования пагинации, CSRF-middleware, отказ от `create_all` в пользу Alembic. Новой код должен двигать проект в эту сторону, а не усугублять техдолг.

---

## 6. Тестирование и проверка

- Тесты: `app/tests/` — pytest + pytest-asyncio (asyncio_mode=auto), httpx `AsyncClient` + `ASGITransport`. Fixtures в `conftest.py` (test engine, override_get_db).
- Перед завершением задачи запускать: `uv run test`, `uv run lint`, `uv run check-types`.
- CI (`.github/workflows/ci.yml`): test, lint, type-check, security (bandit), build — изменения не должны ломать пайплайн.

---

## 7. Ограничения для агента

- Не коммитить и не пушить без явного запроса пользователя.
- Не создавать файлы вне структуры проекта и не менять конфигурацию линтеров без необходимости.
- Не добавлять новые зависимости без обоснования; предпочтительно использовать уже установленные (список — в `docs/01_project_structure.md`).
- Минимальные изменения: не переписывать работающий код без задачи.
