# Архитектура и паттерны

## Высокоуровневая архитектура

Приложение — **классический монолит** на основе FastAPI с рендерингом HTML на сервере (SSR). Архитектура условно слоистая:

```
┌─────────────────────────────────────────────┐
│  Client (браузер)                           │
│  - vanilla JS editor.js                     │
│  - KaTeX на клиенте                         │
└──────────────┬──────────────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────────────┐
│  FastAPI (ASGI / uvicorn)                   │
│  - app/main.py: lifespan, static mounts     │
│  - app/routers/public.py                    │
│  - app/routers/admin.py                     │
│  - middleware/exception handler             │
├──────────────┬──────────────┬───────────────┤
│  Templates   │  Auth        │  Config       │
│  Jinja2      │  signed      │  pydantic-    │
│              │  cookies     │  settings     │
└──────────────┴──────────────┴───────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  psycopg 3 ConnectionPool                   │
│  - app/database.py                          │
│  - get_db() в FastAPI dependency            │
└──────────────┬──────────────────────────────┘
               │ raw SQL
┌──────────────▼──────────────────────────────┐
│  PostgreSQL                                 │
│  - posts, tags, post_tags, users            │
│  - GIN full-text index, B-tree published    │
└─────────────────────────────────────────────┘
```

Нет явного разделения на «сервисы» или «юз-кейсы»: бизнес-логика находится внутри endpoint-функций роутеров и в модулях `../app/queries`, `../app/slugs.py`, `../app/markdown_render.py`.

## Используемые паттерны проектирования

### Dependency Injection (FastAPI)

Подключение к БД передаётся в endpoint через `Depends(get_db)` (`../app/database.py`, строка 19–26). Это обеспечивает:

- единый пул соединений;
- автоматический `COMMIT`/`ROLLBACK` по выходу из `with pool.connection()`;
- удобство тестирования (можно подменить get_db).

### Repository / Table Data Gateway

Модули `../app/queries/posts.py`, `../app/queries/tags.py`, `../app/queries/users.py` инкапсулируют SQL-запросы к таблицам. Они не содержат бизнес-логики, только CRUD и специфичные выборки. Это упрощает поиск и изменение SQL.

### Active Record-подобные операции

Некоторая бизнес-логика (создание slug, сохранение тегов, рендеринг markdown) выполняется непосредственно в роутерах (`../app/routers/admin.py`), а не в отдельном сервисном слое. Для проекта текущего масштаба это приемлемо, но создаёт сопряжение между HTTP-слоем и доменной логикой.

### Singleton-экземпляры

- `app.config.settings` — один экземпляр настроек.
- `app.database.pool` — один пул соединений.
- `app.templating.templates` — один экземпляр Jinja2 с глобальными переменными и фильтрами.
- `app.markdown_render._md` — один сконфигурированный парсер markdown.

### Template Inheritance

Шаблоны Jinja2 наследуют `base.html`; админ-шаблоны наследуют `admin/base_admin.html`, который в свою очередь наследует `base.html`.

## Схема потока данных (Data Flow)

### Публичная страница поста

```
GET /post/{slug}
  │
  ▼
app/routers/public.py::post_detail(request, slug, db)
  │
  ├── app/queries/posts.py::get_published_by_slug(db, slug)
  │       └── SELECT ... FROM posts WHERE slug = %s AND published
  ├── app/queries/tags.py::list_for_post(db, post_id)
  │       └── SELECT tags JOIN post_tags WHERE post_id = ...
  ├── app/queries/posts.py::get_prev / get_next
  │       └── SELECT slug, title ORDER BY published_at
  │
  ▼
Jinja2 template app/templates/post.html
  │
  ▼
HTML-ответ клиенту (content_html выводится через | safe)
```

### Создание поста в админке

```
POST /admin/posts/new
  │
  ▼
app/routers/admin.py::create_post(...)
  │
  ├── app/slugs.py::unique_slug(db, title)  → проверка уникальности
  ├── app/markdown_render.py::render_markdown(content_md) → HTML
  ├── app/queries/posts.py::create(...)      → INSERT INTO posts
  └── app/routers/admin.py::_save_tags(...)  → get_or_create + post_tags
  │
  ▼
Redirect 303 → /admin
```

### Поиск

```
GET /search?q=...
  │
  ▼
app/routers/public.py::search(...)
  │
  ▼
app/queries/posts.py::search(db, query)
  │
  └── SELECT ... FROM posts CROSS JOIN LATERAL websearch_to_tsquery(...)
      WHERE search_vector @@ q ORDER BY ts_rank(...) DESC
```

## Управление состоянием

### HTTP-состояние

- Состояние аутентификации хранится в подписанной cookie (`session`), подписанной через `itsdangerous.URLSafeTimedSerializer` (`../app/auth.py`). Cookie `HttpOnly; SameSite=Lax`.
- Никакого server-side session storage нет — приложение stateless по отношению к сессиям.

### Кэширование

- **HTML-постов**: поле `posts.content_html` кеширует результат `render_markdown()` при сохранении. Публичные страницы не рендерят markdown на лету.
- **Статика**: добавлен query-параметр `?v={{ static_v }}`, где `static_v` — timestamp запуска сервера (`../app/templating.py`). Это сбрасывает кэш браузера после деплоя.
- **PostgreSQL**: full-text `tsvector` хранится как `GENERATED ALWAYS ... STORED`, что избегает пересчёта при каждом поиске.
- Нет Redis / in-memory cache / CDN-кэширования.

### Управление конфигурацией

Конфигурация централизована в `../app/config.py` через `pydantic_settings.BaseSettings`:

| Переменная | Значение по умолчанию | Назначение |
|------------|----------------------|------------|
| `DATABASE_URL` | `postgresql://diegolonio:diegolonio@localhost:5433/diegolonio` | Подключение к PostgreSQL |
| `SECRET_KEY` | `dev-secret-cambiame` | Подпись сессионных cookie |
| `SESSION_MAX_AGE` | `604800` (7 дней) | Время жизни cookie |
| `MEDIA_DIR` | `media` | Директория для загруженных изображений |
| `BASE_URL` | `https://diegolonio.com` | Абсолютные URL (sitemap, OpenGraph) |

Файл `.env` загружается автоматически в режиме разработки. В продакшене переменные передаются через `../docker-compose.prod.yml` с обязательной валидацией (`${VAR:?...}`).
