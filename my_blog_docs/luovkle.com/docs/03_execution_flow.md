# Логика и работа кода

## Жизненный цикл приложения

### 1. Инициализация

```text
app/main.py
    │
    ├── FastAPI(openapi_url=None)
    ├── app.include_router(router)
    ├── app.mount("/static/", StaticFiles(...))
    └── @app.exception_handler(404/500)
```

- OpenAPI отключён (`openapi_url=None`), так как это публичный сайт, а не API.
- Статика монтируется на `/static/` из `app/static/`.

### 2. Lifespan (загрузка контента при старте)

```python
# app/views/routes.py
@asynccontextmanager
async def lifespan(_: FastAPI):
    get_content()
    get_ansi_content()
    yield
```

- `lifespan` привязан к `APIRouter`, который включается в приложение.
- На этапе startup вызываются обе кэшированные фабрики контента; это гарантирует, что первый HTTP-запрос обслуживается из памяти.
- После `yield` выполняется cleanup (в текущей версии пустой).

### 3. Запуск

Локально:

```bash
make local-dev   # uv sync + build CSS/highlight + images + fastapi dev --port 4000 app/main.py
make local-prod  # то же, но fastapi run
```

В контейнере:

```bash
make dev         # podman-compose -f compose.dev.yaml up -d --build
make stage       # podman-compose -f compose.stage.yaml up -d --build
make prod        # podman-compose -f compose.prod.yaml up -d --build
```

Контейнер `runner` запускает:

```text
fastapi run --port 4000 --host 0.0.0.0 --forwarded-allow-ips * app/main.py
```

### 4. Завершение работы

- FastAPI корректно завершает lifespan-контекст при получении сигнала завершения.
- Контейнеры останавливаются через `make {env}-stop`.

## Ключевые бизнес-процессы

### A. Построение HTML-контекста (`app/services/html.py::get_content`)

```text
get_content()
    ├── get_metadata_content()      # content/meta.md → MetadataMD
    ├── get_author_content()        # content/author/index.md → AuthorMD + фото
    ├── get_posts_content()         # content/posts/* → dict[slug, PublishedContent]
    ├── get_projects_content()      # content/projects/* → dict[slug, PublishedContent]
    └── get_homepage_data()         # content/homepage.md + counts/thumbnails
```

Для каждого поста/проекта:

```text
get_content_objects(POSTS_CONTENT_DIR)
    → get_content_context(path)      # определяет index.md и images/
    → _get_published_content(ctx)
        ├── move_image(ctx)          # копирует images/ → app/static/images/<type>/<slug>/
        ├── load_markdown_content()  # YAML-фронтматтер + Markdown-тело
        ├── _parse_markdown(body)    # Markdown → HTML + постобработка
        ├── get_slug() / markdown_content.slug
        ├── get_headers_and_thumbnails(title)  # выбор cover_NNN.png
        ├── estimate_reading_time(body)
        └── get_creation_date() / markdown_content.date
```

### B. Постобработка HTML (`app/services/html.py::_parse_markdown`)

1. `markdown.markdown(body, extensions=["fenced_code", "codehilite"])` — базовый HTML.
2. `BeautifulSoup` навешивает Tailwind-классы на теги (`h1`–`h6`, `blockquote`, `ul`/`ol`, `img`, `pre`, `a`).
3. Локальные `<img src="...">` переписываются в `{{ url_for('static', path='...') }}` — Jinja2-выражение, которое FastAPI разрешит при рендере.
4. Внешние ссылки и пустые `src` игнорируются (`_is_external_url`).
5. Если в HTML есть `<code>`, устанавливается `extras.code = True` для ленивой загрузки `highlight.css`.

### C. Выбор обложки

```text
get_headers_and_thumbnails(title)
    → _get_cover_urls(covers_path, title)
        ├── number_of_covers = len(glob("*.png"))
        ├── cover_number = get_cover_number(len(title), number_of_covers)
        ├── cover_file = "cover_{:03d}.png".format(cover_number)
        └── collect_relative_image_urls(default_path, {avif, webp})
```

Обложка выбирается детерминированно по длине заголовка; наличие `.avif` и `.webp` добавляется как `<source>` в шаблоне `thumbnail.html`.

### D. ANSI-рендеринг (`app/services/ansi.py::get_ansi_content`)

```text
get_ansi_content()
    ├── get_posts_content()
    │   └── _get_post_ansi_content(ctx) → PostANSIContent
    └── get_projects_content()
        └── _get_project_ansi_content(ctx)
            ├── _get_generic_ansi_content(ctx)
            └── _format_ansi_description_lines(description)  # 2 строки по 35 символов
```

- Markdown рендерится в ANSI через `rich.console.Console` с `record=True` и `force_terminal=True`.
- Обложки читаются из `app/ansi/images/headers/` и `app/ansi/images/thumbnails/`.
- Шаблоны ANSI находятся в `app/views/utils.py` и рендерятся через `jinja2.Template`.

## Роутинг и middleware

### Маршруты (`app/views/routes.py`)

| Метод | Путь | Назначение |
|-------|------|------------|
| `GET` | `/` | Главная страница (`homepage.html`) |
| `GET` | `/p` | Список статей; ANSI для CLI |
| `GET` | `/p/{slug}` | Детальная страница статьи; ANSI для CLI |
| `GET` | `/pr` | Список проектов; ANSI для CLI |
| `GET` | `/pr/{slug}` | Детальная страница проекта; ANSI для CLI |
| `GET` | `/author` | Страница автора |
| `HEAD` | `/health` | Healthcheck, `204 No Content` |

### Диспетчеризация по User-Agent

```python
# app/views/deps.py
def is_cli_client(user_agent: Annotated[str | None, Header()]) -> bool:
    return bool(user_agent) and is_cli_client_by_user_agent(user_agent)

# app/views/utils.py
CLI_USER_AGENT_PATTERN = re.compile(r"\b(?:curl|httpie|wget)/[^\s]+\b", re.IGNORECASE)
```

- `curl/8.0.0`, `HTTPie/3.0.0`, `Wget/1.21` → `cli_client=True`.
- Для CLI `/p` и `/pr` возвращают `PlainTextResponse` с ANSI-артом.
- Для CLI детальные страницы (`post_ansi_detail`, `project_ansi_detail`) рендерят шаблоны `post_template` / `project_template`.

### Middleware / обработчики исключений

```python
# app/main.py
@app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_exception_handler(request: Request, _: Exception):
    return internal_exception(request, status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, _: Exception):
    return not_found_exception(request, status.HTTP_404_NOT_FOUND)
```

- `internal_exception` и `not_found_exception` определены в `app/views/routes.py`.
- Декоратор `cli_user_wrapper` перехватывает CLI-запросы и возвращает ANSI-шаблон `not_found_template` / `unexpected_error_template`.
- Для браузеров рендерятся `500.html` / `404.html`.

### Caddy-роутинг

```caddy
# caddy/Caddyfile
handle_path /static/* {
    root * /srv/static/
    file_server browse
}
reverse_proxy www:4000
```

- Статика отдаётся Caddy напрямую.
- Всё остальное проксируется на FastAPI.
- Локальный контейнер заменяет `luovkle.com` на `http://localhost`.

## Обработка ошибок и логирование

### Обработка ошибок

| Источник | Механизм | Поведение |
|----------|----------|-----------|
| Отсутствующий slug | `raise HTTPException(404)` в `post_html_detail` / `project_html_detail` | Браузер → `404.html`; CLI → `not_found_template` |
| Неизвестный путь | FastAPI `HTTPException(404)` | Перехватывается глобальным обработчиком |
| Внутреннее исключение | FastAPI `HTTPException(500)` или непойманное исключение | Браузер → `500.html`; CLI → `unexpected_error_template` |
| Ошибки файлов | `FileNotFoundError`, `NotADirectoryError`, `ValueError` в `app/services/common.py` | Поднимаются в runtime; при старте могут привести к падению lifespan |

### Логирование

- Прямого конфигурирования логирования в коде нет.
- FastAPI/Uvicorn используют стандартные логгеры `uvicorn.access` и `uvicorn.error`.
- `Makefile` и `Containerfile` не переопределяют формат логов.

### Валидация контента

- Pydantic-модели в `app/schemas.py` валидируют YAML-фронтматтер.
- `MetadataMD` требует обязательных SEO/Social-полей.
- `PostMD`/`ProjectMD` наследуют `ContentMD` и добавляют свои поля.
- Невалидный frontmatter вызовет `ValidationError` при старте.

## Примечания по безопасности

- В `compose.stage.yaml`/`compose.prod.yaml` сервис `www` запущен с `read_only: true`, `cap_drop: [ALL]`, `no-new-privileges:true`, ограниченными `ulimits`.
- Caddy удаляет заголовки `Server` и `Via` (`header /* { -Server -Via }`).
- В HTML постобработка использует только имя файла из `src` (`Path(img_src_str).name`), чтобы избежать path traversal.
