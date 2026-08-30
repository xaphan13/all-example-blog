# AmiaBlog: архитектура и паттерны

## Высокоуровневая архитектура

AmiaBlog — монолитное серверное приложение на FastAPI с тонким слоем презентации и «бессерверным» хранилищем данных. Вся бизнес-логика сосредоточена в `core/`, шаблоны — в `templates/`, а контент — в файловой системе (`data/posts/`, `data/attachments/`). Решение ориентировано на read-heavy нагрузку: посты загружаются в память при старте, поиск выполняется в in-memory SQLite, запросы к файлам постов отсутствуют.

Два режима работы:

1. **Динамический сервер** (`main.py`) — FastAPI отвечает на HTTP-запросы, watchdog отслеживает изменения постов.
2. **Статический генератор** (`staticify.py`) — тот же набор менеджеров используется для записи HTML, RSS и sitemap на диск.

## Используемые паттерны

| Паттерн | Где применяется | Пояснение |
|---|---|---|
| **Singleton / глобальные экземпляры** | `main.py` | `config`, `posts_manager`, `renderer`, `i18n` и др. создаются на уровне модуля и живут до завершения процесса. |
| **Repository** | `core/posts.py` — `PostsManager` | Абстракция над файловым хранилищем постов: загрузка, фильтрация, поиск, сортировка, индекс тегов. |
| **Provider** | `core/rss.py`, `core/sitemap.py`, `core/hljs.py`, `core/i18n.py` | Каждый провайдер отвечает за узкий инфраструктурный аспект (генерация фида, карты сайта, языковые бандлы, переводы). |
| **Template Wrapper** | `core/template.py` — `TemplateRenderer` | Единая точка создания Jinja2-окружения, кэширования и минификации. |
| **Builder / Pipeline** | `staticify.py` — `AmiaBlogStaticGenerator` | Последовательный набор шагов: `load_data` → `init_dist_dir` → `init_static_assets` → `init_attachments` → `render_*` → `write_build_info`. |
| **Observer / Hook** | `core/posts.py` + `core/live_preview.py` | Watchdog наблюдает за файлами; `LivePreviewManager` подписывается через `_post_reload_hook` на события перезагрузки. |
| **Factory** | `core/posts.py` — `parse_post()` | Создание `PostMetadata` + контента из Markdown с поддержкой старого и нового формата frontmatter. |

## Поток данных (Data Flow)

### Динамический запрос

```
HTTP/WS
   │
   ▼
Uvicorn (ASGI)
   │
   ▼
FastAPI Router (main.py)
   │
   ├─► path param / query validation
   │
   ▼
PostsManager / HLJSLanguageManager / I18nProvider
   │
   ├─► чтение из in-memory словаря posts{}
   ├─► поиск в sqlite3 (:memory:)        (для /search)
   ├─► определение языков highlight.js   (для /post/{slug})
   │
   ▼
TemplateRenderer.render_to_plain_text()
   │
   ├─► Jinja2 render + static_params
   ├─► htmlmin.minify()
   │
   ▼
HTMLResponse / Response / FileResponse
```

### Статическая генерация

```
staticify.py
   │
   ▼
load_config() → PostsManager(build_search_index=False)
   │
   ▼
AmiaBlogStaticGenerator.render()
   │
   ├─► копирование static/ → dist/static
   ├─► копирование data/attachments → dist/attachments
   ├─► render_top_layers(): index, posts, tags, friend-links, 404, feed.xml, sitemap.xml
   ├─► render_posts(): post/<slug>.html + post/<slug>.md
   ├─► render_tags(): tag/<tag>.html
   │
   ▼
amiablog_build_info.txt
```

## Управление состоянием, кэшированием и конфигурацией

### Состояние приложения

- **Посты и теги** — `PostsManager.posts: Dict[str, Post]` и `PostsManager.tags: Dict[str, Tag]`. Загружаются один раз при старте и обновляются watchdog.
- **Поисковый индекс** — `sqlite3.connect(":memory:")` внутри `PostsManager`. Пересоздается при каждой загрузке.
- **Подписки live-preview** — `LivePreviewManager.subscriptions: Dict[str, List[WebSocket]]`.
- **Кэш шаблонов** — `TemplateRenderer.templates`. Заполняется лениво, если `disable_cache=False`.

### Конфигурация

- Единственный источник правды — `config.json`. Загружается функцией `load_config()` из `core/models.py` на этапе импорта модулей.
- Валидация Pydantic: невалидный конфиг прерывает запуск.
- Переменные окружения не используются для бизнес-логики; настройка осуществляется исключительно через JSON.
- `disable_template_cache` и `live_preview` — флаги разработки; в production должны быть `false`.

### Кэширование

- Jinja2-кэш шаблонов в `TemplateRenderer`.
- In-memory данные постов и поисковый индекс (фактически read cache всего контента).
- highlight.js-файлы кэшируются на диске в `static/hljs_11.1.1/` после первой загрузки.
- Никаких внешних кэш-серверов (Redis, Memcached) нет.
