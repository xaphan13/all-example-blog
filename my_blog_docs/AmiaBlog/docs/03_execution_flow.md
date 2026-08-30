# AmiaBlog: логика и работа кода

## Жизненный цикл приложения

### 1. Импорт модулей (до старта event loop)

В `main.py` на глобальном уровне выполняется:

1. `check_attachment_migration()` — проверяет наличие устаревшей директории `attachments/` и завершает процесс, если требуется миграция.
2. `config = load_config()` — чтение и валидация `config.json`.
3. Создание менеджеров:
   - `hljs_manager` — загружает/скачивает бандлы языков подсветки.
   - `posts_manager` — загружает опубликованные посты, строит индексы, запускает watchdog.
   - `i18n` — загружает языковой файл.
   - `renderer` — инициализирует Jinja2-окружение с `static_params`.
   - `rss_provider`, `sitemap_provider` — готовые генераторы.
   - `live_preview_manager` — создается только при `config.live_preview=True`.

### 2. Запуск сервера

```python
app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
```

- `/static` и `/attachments` монтируются как `StaticFiles`.
- Lifespan `yield`-ит управление приложению. К этому моменту все менеджеры уже инициализированы.

### 3. Обработка запросов

Каждый маршрут:
- валидирует параметры (FastAPI / Pydantic),
- обращается к `posts_manager` (или к `config`),
- формирует контекст шаблона,
- возвращает `HTMLResponse` через `renderer.render()`.

### 4. Завершение работы

Lifespan-контекст завершается:

```python
logger.info("Shutting down PostsManager watchdog")
posts_manager.stop_watchdog()
if live_preview_manager:
    live_preview_manager.running = False
```

Watchdog-корректно останавливается через `observer.stop()` / `observer.join()`.

## Ключевые бизнес-процессы

### Загрузка постов

Реализована в `PostsManager.load_posts()` (`core/posts.py`):

1. Сохраняет текущее состояние `posts` (если задан `_post_reload_hook`).
2. Очищает `self.posts`, `self.tags`, закрывает in-memory SQLite.
3. Сканирует `self.posts_dir` (по умолчанию `data/posts/`).
4. Для каждого `.md`:
   - `parse_post(filename, content)` — парсит YAML frontmatter или legacy-формат.
   - `PostMetadata.model_validate(metadata)` — валидация.
   - Если `published=False`, пост пропускается.
   - slug = имя файла без расширения.
   - Создается `Post(metadata, content, original_content, slug)`.
5. `_build_tag_index()` — подсчитывает количество постов по каждому тегу.
6. `_build_search_index()` — заполняет in-memory SQLite таблицу `posts`.
7. Если задан hook, вызывает `_post_reload_hook(slug, before, after)` для каждого загруженного поста.

### Поиск

Реализован в `PostsManager.search()`:

- `fullmatch`: один `LIKE ?` по `slug`, `title`, `tags`, `keywords` с подстрокой запроса.
- `jieba`: запрос сегментируется на токены; для каждого токена выполняется LIKE; совпадения суммируются по `slug`, результаты сортируются по score.

Маршрут `/search` (`main.py`) дополнительно:
- проверяет `order`, запрещает `relevance` при `fullmatch`,
- валидирует длину запроса 1–50 символов,
- замеряет время выполнения и передает его в шаблон.

### Рендеринг поста

Маршрут `/post/{slug}`:

1. Ищет пост в `posts_manager.posts`.
2. Если не найден — `error.html` с 404.
3. Определяет языки блоков кода через `hljs_manager.get_markdown_languages(post.content)`.
4. Фильтрует доступные языки по `hljs_manager.available_languages`.
5. `renderer.render("post.html", post=post, hljs_languages=available_languages)`.
6. В `post.html` браузер выполняет `markdown-it` + `markdownitFootnote`, рендерит содержимое из `<pre id="post-content">`.

### Горячая перезагрузка

1. `PostsManager._start_watchdog()` создает `Observer()` и регистрирует `PostsFileHandler`.
2. `PostsFileHandler.on_any_event()` реагирует только на `.md` в `data/posts/`.
3. События дебаунсятся через `threading.Timer` на `DEBOUNCE_INTERVAL = 0.5` сек.
4. По истечении таймера вызывается `_do_reload()` → `posts_manager.load_posts()`.

### Статическая генерация

`AmiaBlogStaticGenerator.render()` (`staticify.py`):

1. `load_data()` — конфиг, менеджеры (поиск отключен: `build_search_index=False`).
2. `init_dist_dir()` — удаляет/создает директорию назначения.
3. `init_static_assets()` — копирует `static/` и favicon.
4. `init_attachments()` — копирует `data/attachments`.
5. `render_top_layers()` — RSS, sitemap, index, posts, tags, friend-links, 404.
6. `render_posts()` — HTML и Markdown для каждого поста.
7. `render_tags()` — HTML для каждого тега.
8. `write_build_info()` — текстовый файл с метаданными сборки.

## Роутинг и middleware

### Маршруты FastAPI

| Маршрут | Метод | Описание |
|---|---|---|
| `/` | GET | Главная страница с последними 5 постами. |
| `/feed` | GET | RSS 2.0. |
| `/sitemap.xml` | GET | XML-карта сайта. |
| `/post/{slug}` | GET | HTML-страница поста. |
| `/post/{slug}.md` | GET | Исходный Markdown поста. |
| `/posts` | GET | Список всех постов с сортировкой (`?order=`). |
| `/tag/{tag}` | GET | Посты по тегу. |
| `/tags` | GET | Облако/список тегов. |
| `/search` | GET | Форма и результаты поиска. |
| `/friend-links` | GET | Страница дружественных ссылок. |
| `/api/health` | GET | Health-check JSON. |
| `/api/live-preview-ws` | WS | WebSocket live-preview (только если `config.live_preview=True`). |
| `/static/*` | — | Статические файлы. |
| `/attachments/*` | — | Вложения. |

### Middleware

Пользовательских middleware не регистрируется. Защита от XSS частично обеспечена `select_autoescape()` Jinja2 и `markupsafe.escape` в RSS. Markdown рендерится на клиенте и не санитизируется сервером.

## Обработка ошибок и логирование

### Логирование

- Используется `loguru`.
- Все ключевые операции (загрузка постов, построение индексов, поиск, скачивание бандлов, перезагрузка) логируют время выполнения.
- Уровень `logger.warning` используется для устаревшего формата frontmatter, отсутствующего `site_url` и live-preview.

### Обработка ошибок

- **Невалидный конфиг** — Pydantic `ValidationError` на этапе импорта, процесс не стартует.
- **Отсутствие директории постов** — `FileNotFoundError` или явный `sys.exit(1)` с сообщением о миграции.
- **Ошибка парсинга поста** — пост игнорируется, ошибка логируется (`logger.error`), остальные посты загружаются.
- **404 пост/тег/страница** — возвращается `error.html` с соответствующим HTTP-статусом через `renderer.render(..., status_code=404)`.
- **Некорректный поиск** — 400 с сообщением из i18n.
- **Live-preview** — ошибки подписки отправляются клиенту по WebSocket; отключения обрабатываются через `WebSocketDisconnect`.
