# AGENTS.md — сводное руководство для AI-агентов по воркспейсу `all-example-blog`

> Точка входа для AI-ассистентов (Koda, Copilot, Claude и др.). Цель файла — чтобы
> агент отвечал на вопросы, **не обходя все файлы подряд**: ниже — карта всех 6
> проектов, их стек, ключевые факты и правила поиска информации.

---

## 1. Устройство воркспейса

- **6 папок с исходным кодом**: `AmiaBlog/`, `diegolonio-dot-com/`,
  `fastapi-htmx-starter/`, `fastAPIuser-suren/`, `HabtNPMFastapiJinjaDemo/`,
  `luovkle.com/`.
- **`my_blog_docs/`** — только Markdown-документация по этим же 6 проектам
  (README, AGENTS, пронумерованные `docs/01…07_*.md`). Исходников там нет.

**Правило навигации по любому проекту (в порядке приоритета):**

1. Этот файл + таблица из раздела 2 — определить проект и контекст.
2. `my_blog_docs/<проект>/AGENTS*` — правила и краткая сводка проекта.
3. `my_blog_docs/<проект>/README*` — назначение и быстрый старт.
4. `my_blog_docs/<проект>/docs/` — детали: `01_project_structure.md` (структура),
   `02_architecture.md` (архитектура), `03_execution_flow.md` (роуты/поток выполнения),
   `04_code_quality.md`, `05_optimization_roadmap.md`, `06+` (специфика).
5. Только если документации не хватает — читать исходники в папке проекта.

Обычно **не нужно** читать исходники: документация покрывает структуру, архитектуру,
роуты и конфигурацию всех проектов.

---

## 2. Карта проектов (краткая шпаргалка)

| # | Папка | Что это | Python | БД | Auth | Особенность |
|---|-------|---------|--------|----|------|-------------|
| 1 | `AmiaBlog/` | Блог-система (Markdown, поиск, i18n, RSS) | 3.11+ | SQLite in-memory (только поиск) | нет | hot-reload постов (Watchdog), `staticify.py` — статический сайт, MDUIv2 |
| 2 | `diegolonio-dot-com/` | Блог + портфолио | 3.14 | PostgreSQL, чистый SQL (psycopg 3) | argon2 + itsdangerous | Без ORM/CMS; markdown-редактор, админ-панель; свои SQL-миграции |
| 3 | `fastapi-htmx-starter/` | Boilerplate-шаблон | 3.12+ | SQLAlchemy 2 async + Alembic | fastapi-users (cookie+JWT) | HTMX + Tailwind, CRUD-пример, CLI `uv run serve/test/lint` |
| 4 | `fastAPIuser-suren/` | Управление пользователями | 3.12+ | PostgreSQL 17 + Redis 8 | fastapi-users (cookie, токены в БД) | Верификация email, сброс пароля, роли, Redis-кэш TTL 60s, вебхуки, SQLAdmin |
| 5 | `HabtNPMFastapiJinjaDemo/` | Демо для статьи | 3.12 | нет (stateless) | нет | Слоистая SSR-архитектура, `create_app()`, Tailwind CDN |
| 6 | `luovkle.com/` | Блог + портфолио | 3.13+ | нет (файлы + in-memory кэш) | нет | Двойной рендеринг HTML/ANSI (`curl https://luovkle.com/p`), Podman + Caddy |

### Быстрая идентификация проекта по ключевым словам

| Упомянуто в запросе | Проект |
|---|---|
| MDUIv2, jieba, watchdog, staticify, RSS, sitemap, i18n, config.json, live-preview | **AmiaBlog** |
| «без ORM», чистый SQL, psycopg, argon2, itsdangerous, migrations/*.sql, diegolonio | **diegolonio-dot-com** |
| HTMX, Tailwind, boilerplate/шаблон, items CRUD, alembic + jinja2-шаблоны, `uv run serve` | **fastapi-htmx-starter** |
| fastapi-users, верификация email, сброс пароля, Redis-кэш, вебхуки, SQLAdmin, Maildev, `/api/v1` | **fastAPIuser-suren** |
| Tailwind CDN, `create_app()`, `/api/ping`, pydantic-settings, учебное демо | **HabtNPMFastapiJinjaDemo** |
| ANSI-арт, curl, rich, content/ Markdown, Caddy, Podman, make, WebP/AVIF | **luovkle.com** |

---

## 3. Ключевые технические факты по проектам

### 3.1 AmiaBlog
- Точка входа `main.py` (все маршруты), логика в `core/` (`PostsManager` в `core/posts.py` —
  посты, теги, поиск, watchdog), `staticify.py` — генерация статики.
- Конфиг — единый `config.json` (валидация Pydantic): `site_settings`, `site_language`,
  `search_method` (`fullmatch` | `jieba`), `live_preview` и др.
- Markdown рендерится **на клиенте** (markdown-it в браузере); сервер хранит сырой Markdown.
- Посты: `data/posts/*.md` (slug = имя файла), вложения `data/attachments/` → `/attachments`.
- Маршруты: `/`, `/posts`, `/post/{slug}`, `/tag(s)`, `/search`, `/feed`, `/sitemap.xml`,
  WS `/api/live-preview-ws` (только dev).
- Качество: Black + Pyright (pre-commit, CI). Тестов нет. Аутентификации нет.
- Запуск: `uv sync` → `uv run uvicorn main:app --port 8000`.

### 3.2 diegolonio-dot-com
- `app/main.py` (lifespan), `app/routers/public.py` + `app/routers/admin.py`,
  `app/queries/` — чистый SQL, `app/database.py` — пул psycopg 3.
- Миграции — **свои SQL-файлы** в `migrations/` (`run_migrations.py`), НЕ Alembic;
  имена вида `002_add_index.sql`.
- Markdown на сервере: markdown-it-py + Pygments. Пароли: argon2-cffi; токены: itsdangerous.
- Запуск: `.env` → `docker-compose up -d` → `python migrations/run_migrations.py` →
  `python scripts/create_admin.py` → `uv run uvicorn app.main:app --reload`.
- Комментарии в коде могут быть на испанском. Философия: без ORM, без CMS, без frontend-фреймворков.

### 3.3 fastapi-htmx-starter
- Слои: `app/api/` (роуты) → `app/services/` (логика) → `app/models/` (SQLAlchemy) +
  `app/schemas/` (Pydantic); конфиг `app/core/config.py` (Pydantic Settings, `SECRET_KEY`, `DATABASE_URL`).
- fastapi-users: cookie `auth` с JWT (TTL 3600 с); роуты `/auth/register`,
  `/auth/cookie/login|logout`, `/users/me`; CRUD-пример items.
- Миграции Alembic (`alembic revision --autogenerate`, `alembic upgrade head`).
- CLI: `uv run serve|test|lint|format|check-types`. Шаблоны `*.jinja2`, HTMX partials в `templates/partials/`.

### 3.4 fastAPIuser-suren
- Рабочая директория — `fastapi-application/` (не корень репозитория!).
- `main.py` (`main_app`), фабрика `create_fastapi_app.py`; `api/` — роутеры `/api/v1`,
  `views/` — HTML, `middlewares/`, `admin/` (SQLAdmin), `mailing/` (aiosmtplib), `actions/` (CLI).
- Конфиг: pydantic-settings, префикс `APP_CONFIG__`, вложенность через `__`
  (например `APP_CONFIG__DB__URL`).
- Auth: fastapi-users, Cookie-транспорт + Database-стратегия (токены в PostgreSQL);
  роли `current_active_user` / `current_active_superuser`.
- Кэш: Redis через fastapi-cache2, TTL 60 с, инвалидация при регистрации.
- Инфраструктура (docker compose): PostgreSQL 17 :5432, Redis 8 :6379, Maildev :8080/:1025.
- Запуск: `uv run alembic upgrade head` → `uv run python -m actions.create_superuser` →
  `uv run python main.py` (dev) / `./run` (gunicorn, prod). ruff + black, line-length 120.

### 3.5 HabtNPMFastapiJinjaDemo
- Stateless: без БД, кэша, auth. Только `/`, `/about` (HTML) и `/api/ping` (JSON).
- `main.py` — фабрика `create_app()`; `router.py` — агрегатор роутеров;
  `core/config.py` (Settings: APP_NAME, DEBUG, HOST, PORT, STATIC_DIR, TEMPLATES_DIR);
  `core/templating.py` — единый Jinja2Templates.
- Tailwind через CDN; современная сигнатура `TemplateResponse(request, ...)`.
- Запуск: `pip install -r requirements.txt` → `python3 main.py`. Docker — сеть `internal`, без проброса портов.

### 3.6 luovkle.com
- Без БД: контент `content/{posts,projects,author}/<slug>/index.md` + YAML frontmatter;
  eager-загрузка при старте, in-memory кэш, инвалидация только рестартом.
- Двойной рендеринг по User-Agent: браузер → HTML (markdown + BeautifulSoup + Jinja2 + Tailwind),
  CLI → ANSI (rich + ANSI-шаблоны Jinja2).
- Маршруты: `/`, `/p`, `/p/{slug}`, `/pr`, `/pr/{slug}`, `/author`, `HEAD /health` (204).
- Инфраструктура: Podman + Caddy (TLS, сжатие, статика), Make-цели `dev|stage|prod`;
  локально без контейнеров: `make setup` → `make local-dev` (:4000).
- Tailwind собирается через pnpm (`app/assets/input.css` → `app/static/`).
- CLI-утилиты в `cli/`: конвертация изображений (WebP/AVIF), генерация ANSI-артов.
- Качество: ruff, djlint, ty, pre-commit (`make format`, `make lint`).

---

## 4. Правила работы с запросами

1. **Определи проект.** Если назван — работай только с его папкой и его доками.
   Если не назван — определи по ключевым словам из таблицы раздела 2.
2. **Один проект — один контекст.** Не смешивай факты разных проектов
   (например, Alembic есть в `fastapi-htmx-starter` и `fastAPIuser-suren`,
   но в `diegolonio-dot-com` миграции — чистый SQL, а в `AmiaBlog`, `HabtNPMFastapiJinjaDemo`
   и `luovkle.com` БД нет вообще).
3. **Сравнительные вопросы** («как в моих проектах делается X») — отвечай по таблице
   раздела 2 и разделу 3, явно указывая проект для каждого факта.
4. **Порядок чтения:** этот файл → `my_blog_docs/<проект>/AGENTS*` → README → `docs/`
   → исходники (только при необходимости).
5. **Не выдумывай.** Если документация не покрывает вопрос — скажи об этом и укажи,
   какой файл стоит посмотреть в исходниках или какую доку дополнить.
6. **Язык ответов — русский** (вся документация воркспейса на русском).

### Типовые сценарии

| Запрос | Действие |
|---|---|
| «Как устроен проект X?» | Раздел 3 этого файла + `X/README*` + `X/docs/01–02` |
| «Где роут/эндпоинт Z?» | `my_blog_docs/<проект>/docs/03_execution_flow.md` |
| «Сравни проекты по Y» | `docs/02_architecture.md` релевантных проектов + раздел 3 |
| «Добавь фичу в проект X» | Сначала конвенции из `my_blog_docs/<проект>/AGENTS*`, потом исходники |
| «Составь план улучшений» | `docs/05_optimization_roadmap.md` + `docs/04_code_quality.md` |

---

## 5. Что допустимо и что нет

**Допустимо:**
- читать любые файлы исходников и документации;
- создавать/редактировать Markdown-документацию по запросу;
- вносить изменения в исходники конкретного проекта, следуя его конвенциям
  (стиль, форматтеры, line-length — см. раздел 3 и AGENTS проекта).

**Недопустимо:**
- принимать `my_blog_docs/` за исходники (там только документация);
- выдумывать факты о коде, которых нет в документации;
- переносить паттерны одного проекта в другой без явного запроса
  (например, добавлять ORM в `diegolonio-dot-com` или БД в stateless-проекты);
- мутировать git (commit/push/reset/rebase) без явного подтверждения пользователя.
