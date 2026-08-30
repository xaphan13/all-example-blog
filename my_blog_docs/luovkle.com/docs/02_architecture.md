# Архитектура и паттерны

## Высокоуровневая архитектура

Приложение — **монолитный серверно-рендеринговый сайт** (SSR-like) на FastAPI без базы данных. Контент хранится в Markdown-файлах в `content/`, преобразуется в Python-структуры при старте и отдаётся клиентам двумя способами:

- Браузерам — HTML через Jinja2 + Tailwind CSS.
- CLI-клиентам (`curl`, `httpie`, `wget`) — `text/plain` с ANSI-escape-последовательностями.

Инфраструктура состоит из двух сервисов:

- `www` — FastAPI-приложение (`Containerfile`, target `runner`).
- `caddy` — обратный прокси и статический файловый сервер (`caddy/`).

### Диаграмма развёртывания

```text
┌─────────────┐      HTTPS/HTTP      ┌─────────────┐      HTTP       ┌─────────────┐
│   Client    │ ───────────────────▶ │    Caddy    │ ──────────────▶ │  www:4000   │
│ curl/browser│ ◀─────────────────── │  (proxy+fs) │ ◀────────────── │   FastAPI   │
└─────────────┘                      └─────────────┘                 └─────────────┘
                                            │                               │
                                            ▼                               │
                                     /srv/static/* ◀────────────────────────┘
```

В `compose.dev.yaml` Caddy отсутствует, `www` слушает `:4000` напрямую, а `styles` пересобирает CSS в volume. В `stage`/`prod` Caddy терминирует трафик, отдаёт `/static/*` сам и проксирует остальное на `www`.

## Паттерны проектирования

### 1. Dependency Injection (FastAPI)

- `app/views/deps.py::is_cli_client(user_agent)` — зависимость, извлекающая `User-Agent` из заголовка и определяющая формат ответа.
- `APIRouter` подключается в `app/main.py` через `app.include_router(router)`.
- Обработчики ошибок регистрируются на уровне приложения через `@app.exception_handler`.

### 2. Repository / Content Provider

Слой `app/services/` выступает в роли content-provider:

- `app/services/common.py` — низкоуровневое чтение файлов, слаги, даты, копирование изображений.
- `app/services/html.py` — строит HTML-контекст: `metadata`, `author`, `posts`, `projects`, `homepage`.
- `app/services/ansi.py` — строит ANSI-контекст: те же посты/проекты в ANSI-представлении.

Обе реализации используют общие примитивы из `app/services/common.py`.

### 3. Cache-aside / In-Memory Cache

- `app/services/html.py::get_content()` декорирован `@cache` (`functools.cache`).
- `app/services/ansi.py::get_ansi_content()` декорирован `@cache`.
- Кэш заполняется один раз при старте в `lifespan` (`app/views/routes.py::lifespan`).
- Перечитать контент можно только перезапуском процесса.

### 4. Strategy / Content-Type Dispatch

Маршруты `/p`, `/p/{slug}`, `/pr`, `/pr/{slug}` проверяют `cli_client` и выбирают стратегию:

- HTML-ответ через `Jinja2Templates.TemplateResponse`.
- ANSI-ответ через `PlainTextResponse(render_ansi_template(...))`.

### 5. Template Method в обработке Markdown

Общий алгоритм `_get_published_content` / `_get_generic_ansi_content`:

1. Валидировать `index_file`.
2. Скопировать изображения контента через `move_image`.
3. Загрузить YAML-фронтматтер и Markdown-тело.
4. Преобразовать тело (HTML или ANSI).
5. Вычислить производные поля: slug, обложки, время чтения, дата публикации.
6. Вернуть модель `PublishedContent` / `GenericANSIContent`.

### 6. Factory / Builder для ContentContext

- `app/services/common.py::get_content_context(path)` создаёт `ContentContext`, определяя `index_file`, список изображений и `content_type` по родительской директории.

## Схема потока данных (Data Flow)

### Запрос HTML-страницы

```text
1. Client → Caddy :80/:443
2. Caddy /static/* → file_server /srv/static/
3. Caddy /*         → reverse_proxy www:4000
4. FastAPI middleware + router → view-функция (app/views/routes.py)
5. View вызывает get_content() / get_ansi_content()
6. Сервисный слой читает content/ и app/static/images/
7. HTML-ответ рендерится через Jinja2Templates
8. FastAPI возвращает HTMLResponse
```

### Запрос от CLI-клиента

```text
1. Client → Caddy → www:4000
2. is_cli_client(User-Agent) → True
3. View выбирает ANSI-ответ
4. get_ansi_content() возвращает ANSI-контент
5. render_ansi_template(template_name, context) рендерит Jinja2-шаблон с ANSI-кодами
6. PlainTextResponse возвращает text/plain
```

### Жизненный цикл контента

```text
content/posts/my-post/index.md
         │
         ▼
get_content_objects(POSTS_CONTENT_DIR)
         │
         ▼
get_content_context(path) → ContentContext
         │
         ▼
move_image(context) → app/static/images/posts/my-post/*
         │
         ▼
load_markdown_content() → MarkdownContent
         │
         ▼
_parse_markdown() / render_markdown_to_ansi()
         │
         ▼
PublishedContent / PostANSIContent
         │
         ▼
словарь posts[slug] → get_content() / get_ansi_content()
```

## Управление состоянием и кэшированием

### In-memory cache

- `@cache` на `get_content()` и `get_ansi_content()` фиксирует результаты после первого вызова.
- `lifespan` в `app/views/routes.py` делает eager-загрузку при старте, чтобы первый запрос не платил за парсинг.
- Нет инвалидации кэша в рантайме; изменения контента требуют рестарта процесса.

### Статические артефакты

| Артефакт | Источник | Где генерируется |
|----------|----------|------------------|
| `styles.css` | `app/assets/input.css` | `pnpm build:css` / `pnpm dev:css` |
| `highlight.css` | GitHub-dark Pygments theme | `pygmentize -S github-dark -f html -a .codehilite` |
| `.webp`/`.avif` | `app/static/images/**/*.png` | `python -m cli.convert_images` |
| ANSI обложки | `app/static/images/headers/*.png` | `python -m cli.img_to_ansi` |
| Изображения контента | `content/{posts,projects}/<item>/images/*` | `move_image()` при старте приложения |

## Управление конфигурациями

### Пути и константы

- `app/config.py` — централизованные `Path`-константы для контента, статики, ANSI-артов и шаблонов имён файлов.
- `cli/config.py` — дублирует часть путей для CLI-скриптов.

### Переменные окружения

В самом приложении переменные окружения не используются. Конфигурация развёртывания задаётся через:

- `Makefile`:
  - `PORT ?= 4000`
  - `CONTAINER_TOOL ?= podman-compose`
- `compose.*.yaml`:
  - порты, `read_only`, `cap_drop`, `ulimits`, `healthcheck`, volumes.
- `Containerfile`:
  - `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`, `UV_PYTHON_DOWNLOADS=0`, `PATH`.

### Зависимости

- `pyproject.toml` — production и dev-группы (`build`, `dev`).
- `uv.lock` — закреплённые версии Python-зависимостей.
- `package.json` / `pnpm-lock.yaml` — Node/Tailwind.
