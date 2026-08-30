# all-example-blog — воркспейс с 6 проектами на FastAPI

Воркспейс состоит из **6 папок с исходным кодом** и одной папки документации
[`my_blog_docs/`](my_blog_docs/) — в ней лежат только Markdown-доки по всем шести
проектам (README, AGENTS, `docs/01…07_*.md`). Исходников в `my_blog_docs/` нет.

Все 6 проектов — серверные веб-приложения на **Python + FastAPI + Jinja2 (SSR)**,
но они решают разные задачи и используют разную инфраструктуру:

| # | Папка | Что это | Python | БД / хранилище | Аутентификация | Ключевая фишка |
|---|-------|---------|--------|----------------|----------------|----------------|
| 1 | [`AmiaBlog/`](AmiaBlog/) | Простая блог-система | 3.11+ | нет (SQLite in-memory только для поиска) | нет | Markdown-посты, i18n, RSS, генерация статического сайта, hot-reload постов |
| 2 | [`diegolonio-dot-com/`](diegolonio-dot-com/) | Персональный блог и портфолио | 3.14 | PostgreSQL, **чистый SQL без ORM** | своя (argon2 + itsdangerous) | «Без ORM, без CMS, без frontend-фреймворков»; встроенный markdown-редактор, админ-панель |
| 3 | [`fastapi-htmx-starter/`](fastapi-htmx-starter/) | Стартовый шаблон (boilerplate) | 3.12+ | SQLAlchemy 2.0 async (SQLite/PostgreSQL) + Alembic | fastapi-users (cookie + JWT) | Production-ready шаблон: auth, CRUD-пример, HTMX + Tailwind, CLI-команды |
| 4 | [`fastAPIuser-suren/`](fastAPIuser-suren/) | Подсистема управления пользователями | 3.12+ | PostgreSQL 17 + Redis 8 | fastapi-users (cookie, токены в БД) | Верификация email, сброс пароля, роли, Redis-кэш, вебхуки, email-рассылка, SQLAdmin |
| 5 | [`HabtNPMFastapiJinjaDemo/`](HabtNPMFastapiJinjaDemo/) | Демо для статьи: FastAPI + Jinja2 + Tailwind | 3.12 | нет (stateless) | нет | Чистая слоистая SSR-архитектура, фабрика `create_app()`, Tailwind через CDN |
| 6 | [`luovkle.com/`](luovkle.com/) | Персональный блог и портфолио | 3.13+ | нет (контент в файлах, in-memory кэш) | нет | SSR без БД; **двойной рендеринг**: HTML для браузера и ANSI-арт для `curl`; Podman + Caddy |

---

## 1. AmiaBlog — простая блог-система

**Назначение:** лёгкий блог с упором на простоту, настраиваемость и скорость.
Контент — Markdown-файлы с YAML frontmatter в `data/posts/`. Рендеринг
Markdown выполняется **на клиенте** (markdown-it в браузере), сервер хранит сырой Markdown.

**Стек и библиотеки:**
- Python 3.11+, FastAPI + Uvicorn, Jinja2 (+ `htmlmin` для минификации HTML)
- Pydantic v2 (валидация `config.json` и метаданных постов)
- MDUI v2.1.4 (Material Design You), Roboto, Material Icons, highlight.js 11.1.1
- SQLite **in-memory** — полнотекстовый поиск (`fullmatch` или токенизатор `jieba-fast`)
- Watchdog — hot-reload постов при изменении файлов (задержка 0.5 с)
- loguru, UV (менеджер пакетов), Black + Pyright (качество кода)

**Структура:** `main.py` (точка входа и все HTTP-маршруты), `core/` (models, posts —
`PostsManager`, template, i18n, hljs, rss, sitemap, live_preview, system, utils),
`staticify.py` (CLI генерации статического сайта), `templates/`, `static/`,
`data/posts/` + `data/attachments/`, `languages/` (en, zh-CN), `config.json`.

**Маршруты:** `/`, `/posts`, `/post/{slug}`, `/tag(s)`, `/search`, `/feed` (RSS),
`/sitemap.xml`, `/attachments`, WebSocket `/api/live-preview-ws` (экспериментально, только dev).

**Запуск:** `uv sync` → `uv run uvicorn main:app --host 0.0.0.0 --port 8000`.
Продакшен: Gunicorn + UvicornWorker. Статический сайт: `uv run staticify.py --destination dist/`.

**Конфигурация:** единый файл `config.json` (site_settings, site_language,
search_method, copyright, friend_links, cloudflare_analytics_token и др.).
Аутентификации нет — это публичный read-only блог.

---

## 2. diegolonio-dot-com — персональный блог и портфолио

**Назначение:** минималистичный блог/портфолио с философией «без ORM, без CMS,
без frontend-фреймворков». Все запросы к БД — **чистый SQL** (psycopg 3).
Есть админ-панель и встроенный markdown-редактор.

**Стек и библиотеки:**
- Python 3.14, FastAPI + Uvicorn, Jinja2 (SSR)
- PostgreSQL + чистый SQL (psycopg 3), свои SQL-миграции в `migrations/` (не Alembic)
- markdown-it-py + Pygments (рендеринг Markdown на сервере)
- argon2-cffi (хеширование паролей) + itsdangerous (токены/подписи)

**Структура:** `app/main.py` (lifespan, роутеры, статика), `app/config.py`,
`app/database.py` (пул соединений), `app/routers/public.py` и `app/routers/admin.py`,
`app/queries/` (SQL-запросы), `app/templates/`, `migrations/*.sql` + `run_migrations.py`,
`scripts/create_admin.py`, `projects.yaml`, `media/`, docker-compose (dev и prod).

**Запуск:** `.env` из `.env.example` → `docker-compose up -d` (PostgreSQL) →
`python migrations/run_migrations.py` → `python scripts/create_admin.py` →
`uv run uvicorn app.main:app --reload`. Продакшен: `docker-compose -f docker-compose.prod.yml up -d`.

**Конвенции:** новые SQL-миграции — `migrations/` с именами вида `002_add_index.sql`
(нулевой паддинг, без паддинга), DI через `Depends(get_db)`, комментарии в коде
могут быть на испанском.

---

## 3. fastapi-htmx-starter — стартовый шаблон веб-приложений

**Назначение:** production-ready boilerplate «FastAPI + HTMX + Tailwind»:
динамические интерфейсы без JavaScript-фреймворков, готовая аутентификация
и CRUD-пример (items) для старта нового приложения.

**Стек и библиотеки:**
- Python 3.12+, FastAPI, HTMX, TailwindCSS, Jinja2 (шаблоны `*.jinja2`)
- SQLAlchemy 2.0 (async) + Alembic; БД переключается через `DATABASE_URL` (SQLite/PostgreSQL)
- fastapi-users: cookie-аутентификация с JWT-токеном в cookie `auth` (TTL 3600 с)
- Pydantic Settings (конфиг из окружения), Gzip-middleware, кастомные exception handlers
- Качество: Black, Ruff, MyPy, Flake8, isort, djlint, Pytest (async); CLI: `uv run serve/test/lint/format/check-types`

**Структура:** `app/main.py`, `app/cli.py`, `app/api/` (auth, items, user,
dependencies), `app/core/` (config, database, templates, users), `app/models/`,
`app/schemas/`, `app/services/`, `app/templates/` (base, index, profile, auth/, items/,
partials/), `app/tests/`, `alembic/`.

**Маршруты:** `POST /auth/register`, `POST /auth/cookie/login|logout`,
`GET|PATCH /users/me`, CRUD items (список, поиск, пагинация, инлайн-редактирование через HTMX).

**Запуск:** `uv venv` → `uv pip install -e .` → `cp .env.example .env` (+ SECRET_KEY) →
`alembic upgrade head` → `uv run serve` (http://localhost:8000).

---

## 4. fastAPIuser-suren — подсистема управления пользователями

**Назначение:** полноценная подсистема пользователей: регистрация, cookie-аутентификация
(токены хранятся в PostgreSQL — Database-стратегия), верификация email (двухфазная),
сброс пароля, роли user/superuser, кэш Redis, HTML-страницы, email-уведомления,
исходящие вебхуки, админ-панель SQLAdmin.

**Стек и библиотеки:**
- Python 3.12+, FastAPI, Starlette, Pydantic v2, pydantic-settings (префикс `APP_CONFIG__`, вложенность через `__`)
- PostgreSQL 17 (asyncpg) + SQLAlchemy 2 (async) + Alembic
- fastapi-users[sqlalchemy] (Cookie-транспорт + Database-стратегия)
- Redis 8 + fastapi-cache2 (кэш списка пользователей, TTL 60 с, инвалидация при регистрации)
- Jinja2 + Bootstrap 5 (HTML), aiosmtplib (email, Maildev в dev), aiohttp (вебхуки)
- SQLAdmin (`/admin`), ORJSONResponse, Uvicorn (dev) / Gunicorn + UvicornWorker (prod)
- ruff + black (line-length 120)

**Структура:** рабочая директория приложения — `fastapi-application/`:
`main.py` (`main_app`), `create_fastapi_app.py` (фабрика: lifespan, middleware, admin, docs),
`core/` (config, модели, схемы, auth), `api/` (роутеры `/api/v1`, DI, webhooks),
`views/` (HTML), `middlewares/` (CORS, X-Process-Time, логирование, счётчик запросов),
`admin/`, `mailing/`, `utils/`, `actions/` (CLI `create_superuser`), `alembic/`, `templates/`.
Корень: `docker-compose.yml` (PostgreSQL 17 :5432, Redis 8 :6379, Maildev :8080/:1025).

**Маршруты:** `/api/v1/auth/*` (register, login, logout, request-verify-token, verify,
forgot-password, reset-password), `/api/v1/users*`, `/api/v1/service/stats`,
`/home/`, `/verify-email/`, `/admin`, `/docs`, `/redoc`.

**Запуск:** `docker compose up -d` → `cp .env.template .env` (обязательны
`APP_CONFIG__DB__URL`, `APP_CONFIG__ACCESS_TOKEN__RESET_PASSWORD_TOKEN_SECRET`,
`APP_CONFIG__ACCESS_TOKEN__VERIFICATION_TOKEN_SECRET`) →
`uv run alembic upgrade head` → `uv run python -m actions.create_superuser` →
`uv run python main.py` (dev) или `./run` (prod, gunicorn).

---

## 5. HabtNPMFastapiJinjaDemo — демо FastAPI + Jinja2 + Tailwind

**Назначение:** минимальное учебное/demo-приложение для статьи. Цель — показать
чистую масштабируемую SSR-архитектуру, а не функционал. Полностью stateless:
без БД, кэша и аутентификации.

**Стек и библиотеки:**
- Python 3.12, FastAPI 0.137, Uvicorn 0.49 (`[standard]`: uvloop, httptools, watchfiles)
- Jinja2 3.1.6, pydantic-settings 2.14 (конфиг из `.env`), python-multipart
- Tailwind CSS через CDN (без npm-сборки)

**Структура:** `main.py` (фабрика `create_app()` + запуск uvicorn), `router.py`
(агрегатор всех под-роутеров), `core/config.py` (Settings: APP_NAME, DEBUG, HOST,
PORT, STATIC_DIR, TEMPLATES_DIR), `core/templating.py` (единый Jinja2Templates),
`routers/pages.py` (HTML `/`, `/about`), `routers/api.py` (JSON `/api/ping`),
`static/`, `templates/` (base.html, partials/, pages/), `requirements.txt`, Dockerfile + compose.yaml.

**Архитектурные решения:** фабрика приложения; единая точка подключения роутеров;
разделение pages/api; инфраструктура в `core/`; шаблоны через наследование и партиалы;
современная сигнатура `TemplateResponse(request, ...)`.

**Запуск:** `pip install -r requirements.txt` → `python3 main.py` (http://127.0.0.1:8000).
Docker: `docker network create internal` → `docker compose up --build`
(порты наружу не пробрасываются, контейнер доступен как `app:8000` в сети `internal`).

---

## 6. luovkle.com — блог и портфолио с двойным рендерингом

**Назначение:** персональный блог/портфолио — монолитный SSR-сайт **без базы данных**.
Контент — Markdown с YAML frontmatter в `content/` (posts, projects, author),
индексируется из файловой системы при старте и кэшируется в памяти (инвалидация —
только рестартом процесса). Главная особенность — **двойной формат ответа** по
`User-Agent`: браузер получает `text/html` (markdown + BeautifulSoup + Jinja2 + Tailwind),
CLI-клиенты (`curl`, `httpie`) — `text/plain` ANSI-арт (rich + Jinja2 ANSI-шаблоны).
Проверка: `curl https://luovkle.com/p`.

**Стек и библиотеки:**
- Python 3.13+, FastAPI, Jinja2, Pydantic (схемы контента), Tailwind CSS (сборка через pnpm)
- markdown, BeautifulSoup (HTML), rich (ANSI), WebP/AVIF-конвертация изображений
- Podman + podman-compose, Caddy (reverse proxy: TLS, сжатие, статика, очистка заголовков), GNU Make
- Hardened-контейнеры: read-only rootfs, `cap_drop: ALL`, `no-new-privileges`, nonroot
- Качество: ruff, djlint, ty, pre-commit; uv + pnpm

**Структура:** `app/main.py`, `app/config.py`, `app/schemas.py`, `app/services/`
(загрузка и конвертация контента в html/ansi), `app/views/`, `app/templates/`,
`app/assets/input.css` + `app/static/`, `cli/` (утилиты изображений/ANSI),
`content/` (author, posts/<slug>/index.md + images/, projects/), `caddy/`,
`scripts/` (format.sh, lint.sh), `Containerfile`, `compose.{dev,stage,prod}.yaml`, `Makefile`.

**Маршруты:** `/`, `/p`, `/p/{slug}`, `/pr`, `/pr/{slug}`, `/author`, `HEAD /health` (204).

**Запуск:** контейнерно — `make dev|stage|prod` (и `make *-stop`); без контейнеров —
`make setup` → `make local-dev` (:4000). Полезное: `make local-styles`, `make images-optimize`,
`make images-ansi`, `make format`, `make lint`.

---

## Папка my_blog_docs — документация

Содержит **только Markdown-документацию** по всем 6 проектам (исходников нет):
в каждой подпапке — `README*`, `AGENTS*` и пронумерованные файлы `docs/`:

| Файл | Содержание |
|---|---|
| `01_project_structure.md` | Дерево директорий, роль файлов, зависимости |
| `02_architecture.md` | Архитектура, слои, паттерны, поток данных, конфигурация |
| `03_execution_flow.md` | Жизненный цикл, бизнес-процессы, таблица роутов, middleware |
| `04_code_quality.md` | Качество кода, технический долг, безопасность |
| `05_optimization_roadmap.md` | Дорожная карта улучшений |
| `06+` | Специфика проекта (Alembic, фронтенд, деплой, рендеринг Markdown и т.п.) |

Отличия по именам файлов есть только в `AmiaBlog/` — см. `my_blog_docs/AmiaBlog/AGENTS.ru.md`.

**AI-агентам:** начните с корневого [`AGENTS.md`](AGENTS.md) — там правила навигации.
