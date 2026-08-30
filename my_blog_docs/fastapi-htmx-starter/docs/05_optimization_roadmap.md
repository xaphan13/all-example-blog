# 05 — Предложения по развитию

## Архитектурные улучшения

### 1. Выделение сервисного слоя

**Проблема:** Бизнес-логика resides в route-хендлерах; `app/services/` пуст. Route-хендлеры в `app/api/items.py` содержат ~350 строк с дублированием.

**Решение:** Создать `app/services/item_service.py` и `app/services/user_service.py`:

```
app/api/items.py (thin controller)
  → app/services/item_service.py (business logic, DB operations)
    → app/models/item.py (ORM)
```

Сервисы принимают `AsyncSession` и `User` как параметры, возвращают доменные объекты. Route-хендлеры занимаются только HTTP-слоем (парсинг запроса, выбор шаблона).

**Приоритет:** 🔴 Высокий — основное архитектурное улучшение.

### 2. Устранение дублирования пагинации

**Проблема:** `app/api/items.py` — логика пагинации (query, count, context) дублируется 3 раза.

**Решение:** Вынести в `app/services/pagination.py`:

```python
async def paginate(
    db: AsyncSession,
    query: Select,
    page: int,
    per_page: int,
) -> PaginationContext:
    total = await db.execute(select(func.count()).select_from(query.subquery()))
    items = await db.execute(query.offset(...).limit(...))
    return PaginationContext(items=..., total=..., pages=..., ...)
```

**Приоритет:** 🔴 Высокий.

### 3. Единый механизм управления схемой

**Проблема:** `init_db()` (`Base.metadata.create_all`) и Alembic работают параллельно; `alembic/versions/` пуст.

**Решение:**
- Удалить `init_db()` из `lifespan` (или оставить только для тестов)
- Сгенерировать первую миграцию: `alembic revision --autogenerate -m "Initial"`
- В production: `alembic upgrade head` перед запуском (уже в CI)

**Приоритет:** 🟡 Средний.

### 4. Добавление middleware-слоя

**Проблема:** Нет CORS, CSRF, rate limiting, request logging.

**Решение:** Добавить в `app/main.py`:
- `CORSMiddleware` (если планируется API-потребление)
- CSRF-middleware (для HTMX POST/PUT/DELETE) — например, `starlette-csrf` или кастомный token в header
- Rate limiting — `slowapi` или `fastapi-limiter`
- Structured logging middleware (request_id, timing)

**Приоритет:** 🔴 Высокий (CSRF — security-critical).

---

## Оптимизация производительности

### 1. `selectinload` для N+1

**Файл:** `app/api/user.py:31` — уже использует `selectinload(User.items)`. ✅

**Но:** `list_items` в `app/api/items.py:33` выполняет 2 запроса (SELECT + COUNT) на каждый вызов. Для оптимизации можно использовать `select(func.count()).where(...)` вместо `subquery()` — избегает materialization подзапроса.

### 2. Отсутствие `order_by`

**Файл:** `app/api/items.py:33`

Без `order_by` пагинация недетерминирована. Добавить `.order_by(Item.id.desc())` (или `created_at` при наличии) — это также позволяет БД использовать index.

### 3. TailwindCSS CDN → локальная сборка

**Файл:** `app/templates/base.jinja2:14`

`<script src="https://cdn.tailwindcss.com">` — Play CDN загружает ~3.5MB JS и компилирует стили в браузере. Для production:
- Установить `tailwindcss` через npm/standalone CLI
- Собрать `app/static/css/tailwind.css` (purge unused classes → ~10-50KB)
- Убрать CDN-скрипт

**Приоритет:** 🟡 Средний (влияет на load time и availability).

### 4. Кэширование статических шаблонов

`Jinja2Templates` по умолчанию включает `auto_reload=True` в dev. В production следует отключить (`auto_reload=False`) для кэширования скомпилированных шаблонов.

### 5. Connection pool tuning

**Файл:** `app/core/database.py:17`

`create_async_engine` использует default pool settings. Для PostgreSQL в production:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

---

## Рефакторинг — первоочередные файлы

| # | Файл | Обоснование | Объём работ |
|---|---|---|---|
| 1 | `app/api/items.py` | Дублирование пагинации (~150 строк копипасты), нет `order_by`, бизнес-логика в routes. Вынести в `item_service.py` + `pagination.py` | 🔴 Крупный |
| 2 | `app/api/user.py` | Inline HTML с XSS, `dict[str, Any]` вместо Pydantic-схем. Перенести HTML в шаблоны, создать `UserEmailUpdate`/`UserPasswordUpdate` схемы | 🔴 Крупный |
| 3 | `app/core/config.py` | `SECRET_KEY` runtime-default. Сделать обязательным (raise если не задан в production) | 🟢 Небольшой |
| 4 | `app/core/database.py` | Убрать `init_db()` из lifespan (или ограничить тестами), добавить `engine.dispose()` в shutdown, настроить pool | 🟡 Средний |
| 5 | `app/api/dependencies.py` | Удалить мёртвый `get_db`, оставить только `is_htmx` | 🟢 Небольшой |
| 6 | `app/templates/partials/auth_links.jinja2` | Починить `url_for("auth_logout_redirect")` → `url_for("auth_logout")` | 🟢 Небольшой |
| 7 | `app/models/user.py` | `datetime.utcnow()` → `datetime.now(timezone.utc)`; `List` → `list` | 🟢 Небольшой |
| 8 | `app/core/users.py` | Добавить `Secure=True` в cookie transport (production) | 🟢 Небольшой |
| 9 | `app/templates/base.jinja2` | Убрать CDN, добавить SRI или локальные ассеты | 🟡 Средний |

---

## Рекомендации по DX (Developer Experience)

### Тестирование

**Текущее состояние:** 4 smoke-теста в `app/tests/test_main.py`. Coverage настроен, но реальное покрытие минимально.

**Рекомендации:**
1. **Тесты auth-флоу:** регистрация → login → защищённый роут → logout
2. **Тесты CRUD Items:** create → list → edit → update → delete (с проверкой owner isolation)
3. **Тесты пагинации:** граничные случаи (page > total_pages, empty search, per_page=100)
4. **Тесты profile:** update email (уникальность), update password (валидация, неверный current_password)
5. **Фикстуры:** создать `user` fixture, `authenticated_client` fixture, `item` factory
6. **Integration:** добавить тест с реальной PostgreSQL (через testcontainers или CI service)
7. **Покрытие:** установить минимальный порог (например, 80% в `pyproject.toml`)

### CI/CD

**Текущее состояние:** `ci.yml` — 4 job (test, lint, type-check, security). Хорошая структура.

**Рекомендации:**
1. **Bandit:** сейчас `|| true` — сканер не фейлит pipeline. Убрать `|| true` или установить порог
2. **Coverage gate:** добавить `--cov-fail-under=80` к pytest
3. **PostgreSQL service:** раскомментировать `services.postgres` в CI для интеграционных тестов
4. **Docker build:** добавить Dockerfile в репозиторий (в README есть пример, но файла нет)
5. **Deploy stage:** добавить job для деплоя (например, на Railway/Render)
6. **Dependabot/Renovate:** автоматическое обновление зависимостей

### Локальный запуск

**Текущее состояние:** `uv run serve` → `uvicorn --reload`. CLI-обёртки в `app/cli.py` через `subprocess.run`.

**Рекомендации:**
1. **Makefile или `task` runner:** вместо Python CLI-обёрток — нативные команды
2. **Docker Compose:** для локального PostgreSQL + Redis (если добавится кэш)
3. **`.env.example`:** дополнить всеми переменными (CORS_ORIGINS, cookie secure flag, etc.)
4. **Seed script:** CLI-команда `seed` для создания тестовых пользователей и items
5. **`uvicorn` direct:** убрать `subprocess.run` в `cli.py` — запускать `uvicorn.run()` напрямую (или использовать `app.main:app` напрямую)

### Документация

1. **API docs:** FastAPI автоматически генерирует `/docs`, но HTMX-роуты (HTML-ответы) плохо документированы. Добавить описания в `@router` decorators
2. **ARCHITECTURE.md:** зафиксировать архитектурные решения (этот набор файлов — хороший старт)
3. **CONTRIBUTING.md:** дополнить инструкциями по локальному запуску и тестированию
