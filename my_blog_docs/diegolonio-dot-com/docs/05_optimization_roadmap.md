# Предложения по развитию

## Архитектурные улучшения

### 1. Введение сервисного слоя

Вынести бизнес-логику из роутеров в отдельный слой `app/services/`:

```
app/services/
├── posts.py        # create_post, update_post, publish_post, delete_post
├── tags.py         # assign_tags_to_post
├── auth.py         # authenticate_admin
└── media.py        # cleanup_orphan_media
```

Роутеры должны отвечать только за:
- извлечение данных из request;
- вызов сервиса;
- выбор response (HTML/redirect/JSON).

Это упростит тестирование и позволит переиспользовать логику (например, CLI-скриптами).

### 2. Добавить healthcheck endpoint

```python
# app/routers/public.py
@router.get("/health")
async def health(db=Depends(get_db)):
    db.execute("SELECT 1")
    return {"status": "ok"}
```

Использовать его в `../docker-compose.prod.yml` для проверки готовности app.

### 3. Поддержка async PostgreSQL

Текущий `psycopg_pool.ConnectionPool` синхронный. Для повышения пропускной способности рассмотреть `psycopg[binary]` async API или замену пула на `asyncpg`. Это критично при росте нагрузки, поскольку сейчас каждый request блокирует event loop на время SQL-запроса.

### 4. CSRF-защита

Внедрить CSRF-токены для всех POST-форм админки:

- Генерировать токен при создании сессии и хранить в подписанной cookie или session state.
- Передавать в шаблоны через hidden input.
- Проверять в защищённых POST endpoint.

FastAPI не предоставляет встроенной CSRF-защиты; можно использовать `fastapi-csrf-protect` или реализовать вручную.

### 5. Ограничение размера загружаемых файлов

Добавить в `../app/routers/admin.py`:

```python
from fastapi import UploadFile, File

@router.post("/api/images")
def upload_image(file: UploadFile = File(..., max_length=5 * 1024 * 1024), ...):
    ...
```

Также проверять `file.content_type` и, опционально, читать первые байты для валидации magic numbers.

## Оптимизация производительности

### 6. Кэширование sitemap

`/sitemap.xml` пересчитывается при каждом запросе. Варианты:

- Сохранять в файл `sitemap.xml` при публикации/изменении поста.
- Использовать in-memory кэш с TTL (например, `functools.lru_cache` или Redis).
- Ограничить частоту обновления: sitemap не критичен к актуальности в реальном времени.

### 7. Оптимизация media cleanup

Текущий подход `blob = "\n".join(...)` загружает весь контент в память. Альтернативы:

- Использовать PostgreSQL для поиска используемых URL: `SELECT DISTINCT regexp_matches(...)`.
- Или обходить файлы и проверять каждый по отдельности через `LIKE` запросы с индексом по `content_md`/`cover_image` (хотя GIN для LIKE неэффективен).
- Вынести очистку в фоновую задачу (celery / rq / APScheduler), чтобы не блокировать HTTP-запрос.

### 8. Пагинация в поиске и тегах

Добавить `limit`/`offset` в `app/queries/posts.py::search` и `list_published_by_tag`, а также элементы пагинации в шаблоны `search.html` и `tag.html`.

### 9. Статика и медиа через CDN / reverse proxy

В продакшене настроить Nginx или Cloudflare для раздачи `/static` и `/media`. Сейчас FastAPI отдаёт статику самостоятельно, что неэффективно.

### 10. Подключение пула с retry

```python
# app/database.py
import time

def open_pool_with_retry(pool, retries=10, delay=1.0):
    for _ in range(retries):
        try:
            pool.open()
            return
        except psycopg.OperationalError:
            time.sleep(delay)
    raise
```

Это повысит устойчивость при локальном запуске и в тестах.

## Рефакторинг: приоритетные файлы

| Приоритет | Файл | Обоснование | Предлагаемые изменения |
|-----------|------|-------------|------------------------|
| 1 | `../app/routers/admin.py` | Слишком много ответственностей | Вынести логику в `app/services/`, вынести схемы в `app/schemas/`, добавить CSRF, лимит размера файлов |
| 2 | `../app/media_cleanup.py` | Не масштабируется на большом объёме | Переписать через потоковую обработку или SQL, добавить фоновый запуск |
| 3 | `../app/routers/public.py` | `sitemap.xml` и `home` не кэшированы | Кэш sitemap, пагинация тегов/поиска |
| 4 | `../app/queries/posts.py` | Дублирование `CASE WHEN` для `published_at` | Вынести в хранимую функцию или триггер PostgreSQL |
| 5 | `../app/config.py` | Нет валидации prod-only параметров | Добавить `model_validator` для проверки `SECRET_KEY` в проде |
| 6 | `../scripts/migrate_old_posts.py` | Жёстко зашитый путь | Перенести путь в переменную окружения/аргумент CLI |

## Улучшение DX (Developer Experience)

### 11. Тесты

Внедрить пирамиду тестирования:

- **Unit**: `pytest` для `../app/slugs.py`, `../app/markdown_render.py`, `../app/auth.py`.
- **Integration**: `TestClient` FastAPI с `postgresql` в Docker или `pytest-postgresql`.
- **E2E** (опционально): Playwright для админ-редактора.

Пример структуры:

```
tests/
├── conftest.py
├── unit/
│   ├── test_slugs.py
│   ├── test_markdown_render.py
│   └── test_auth.py
├── integration/
│   ├── test_public_routes.py
│   ├── test_admin_routes.py
│   └── test_database.py
└── fixtures/
    └── sample_post.md
```

### 12. CI/CD

Добавить `.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run pytest
```

### 13. Линтеры и форматёры

Добавить в `../pyproject.toml` dev-зависимости:

```toml
[dependency-groups]
dev = ["ruff", "pytest", "pytest-asyncio", "httpx"]
```

Настроить `ruff` для lint + format и pre-commit hook.

### 14. Локальный запуск

Добавить `Makefile` или скрипты:

```makefile
.PHONY: dev test lint migrate

dev:
	docker compose up -d db
	uv run python migrations/run_migrations.py
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

migrate:
	uv run python migrations/run_migrations.py
```

### 15. Документация для разработчиков

Дополнить `../README.md` разделами:

- «Как запустить локально» (шаги с `uv`, `docker compose`).
- «Как создать администратора» (`uv run python scripts/create_admin.py`).
- «Как писать посты и работать с редактором».
- «Структура проекта» (краткая ссылка на `01_project_structure.md`).
- «Как деплоить» (ссылка на `../docker-compose.prod.yml` и `../scripts/backup_db.sh`).

### 16. Мониторинг и observability

- Добавить базовое логирование (`structlog` или стандартный `logging`) с request ID.
- Экспортировать метрики через `/metrics` (Prometheus) — опционально.
- Настроить алертинг на ошибки backup.

## Итоговая приоритизация

| # | Задача | Влияние | Сложность |
|---|--------|---------|-----------|
| 1 | Тесты + CI/CD | Критическое | Средняя |
| 2 | CSRF-защита | Высокое (безопасность) | Низкая |
| 3 | Сервисный слой + рефакторинг `admin.py` | Высокое | Средняя |
| 4 | Лимит размера и валидация загрузки файлов | Высокое (безопасность) | Низкая |
| 5 | Кэширование sitemap | Среднее | Низкая |
| 6 | Async PostgreSQL | Среднее | Средняя |
| 7 | Пагинация поиска/тегов | Среднее | Низкая |
| 8 | Оптимизация media cleanup | Среднее | Средняя |
| 9 | Healthcheck endpoint | Низкое | Низкая |
| 10 | Nginx/CDN для статики | Низкое при текущей нагрузке | Средняя |
