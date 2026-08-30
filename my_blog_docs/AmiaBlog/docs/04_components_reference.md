# AmiaBlog: справочник по компонентам

## `core/models.py`

- `SiteSettings`: `title`, `description`, `keywords`, `site_url`, `color_scheme`, `theme`, `hljs_languages`.
- `Config`: `site_settings`, `site_language`, `copyright`, `search_method`, `cloudflare_analytics_token`, `friend_links`, `icp`, `disable_template_cache`, `live_preview`.
- `PostMetadata`: `title`, `date`, `last_modified`, `tags`, `description`, `published`, `author`, `keywords`.
- `Post`: `metadata`, `content` (чистый Markdown), `original_content` (файл целиком), `slug`.
- `Tag`: `name`, `count`.
- `load_config(filename="config.json")`: читает JSON, валидирует, приводит `site_url` к trailing slash.

## `core/posts.py`

### `parse_post(filename, content)`

Поддерживает:
- стандартный YAML frontmatter между `---`;
- legacy-формат без открывающих `---` (выводит warning).

### `PostsManager`

| Метод / атрибут | Назначение |
|---|---|
| `posts: Dict[str, Post]` | Все опубликованные посты по slug. |
| `tags: Dict[str, Tag]` | Индекс тегов. |
| `search_index: sqlite3.Connection` | In-memory БД для поиска. |
| `load_posts(build_search_index=True)` | Полная перезагрузка контента. |
| `search(keyword)` | Поиск по индексу (`fullmatch` или `jieba`). |
| `recent_posts(n=5)` | Последние `n` постов по `modified_desc`. |
| `order_by(posts, key)` | Сортировка по date/modified. |
| `get_posts_by_tag(tag, limit=None)` | Фильтр постов по тегу. |
| `list_tags(order_by="default")` | Список тегов; `post_count` — по убыванию count. |
| `_start_watchdog()` / `stop_watchdog()` | Управление файловым наблюдением. |

## `core/template.py`

- `TemplateRenderer.env` — Jinja2-окружение с `FileSystemLoader("templates")` и `select_autoescape()`.
- `urlencode` filter — `urllib.parse.quote(s, safe="")`.
- `render_to_plain_text(template_name, **context)` — рендер + минификация.
- `render(template_name, status_code=200, **context)` — обертка в `HTMLResponse`.
- `render_static(destination, template_name, **context)` — запись в файл.

## `core/i18n.py`

- `I18nTerm` — обертка над строкой перевода с поддержкой `.format()` и `Markup.format()` для безопасного экранирования.
- `I18nProvider` — загружает `languages/{language}.json`; доступ к терминам через `i18n.key`.

## `core/hljs.py`

- `download()` — проверяет `static/hljs_11.1.1/`, скачивает недостающие `.min.js` с `cdn.jsdelivr.net`.
- `get_markdown_languages(markdown_text)` — парсит строки, начинающиеся с ` ```<lang>`, возвращает список языков.

## `core/rss.py`

- `generate_rss(limit=None, is_static=False)` — формирует XML с `atom:link`, `lastBuildDate`, `content:encoded` (сырой Markdown в CDATA), категориями-тегами.
- В статическом режиме ссылки на посты получают суффикс `.html`.

## `core/sitemap.py`

- `generate_sitemap()` — строит `urlset` для `/`, `/posts`, `/tags`, `/search` (только динамика), `/friend-links`, каждого поста и каждого тега.
- `is_static` добавляет `.html` к URL.

## `core/live_preview.py`

- `LivePreviewManager` подменяет `posts_manager._post_reload_hook`.
- `router(websocket)` — принимает `ping`/`subscribe`.
- `_post_reload_hook(slug, before, after)`:
  - если изменилась метаданная — отправляет `{"type":"refresh"}` (страница перезагружается);
  - иначе — отправляет `{"type":"update", "markdown": ...}`.

## `core/system.py`

- `get_amiablog_version()` — парсит `version` из `pyproject.toml`.
- `get_commit_hash(length=7)` — вызывает `git rev-parse HEAD` через `os.popen()`.
- `get_platform_string()` — `os-arch` для build_info.

## `core/utils.py`

- `check_attachment_migration()` — `sys.exit(1)`, если существует `attachments/`, но отсутствует `data/attachments/`.

## Шаблоны

Наследование: все шаблоны расширяют `base.html`.

Блоки `base.html`:
- `meta_description`, `meta_keywords`
- `head_extra`
- `title`
- `content`
- `copyright`
- `extra_scripts`

Флаг `is_static` передается через `static_params` в `staticify.py` и используется для переключения URL:
- динамика: `/feed`, `/post/{slug}`, `/tags`
- статика: `/feed.xml`, `/post/{slug}.html`, `/tags.html`

## Схема поискового индекса SQLite

```sql
CREATE TABLE posts (
  id INTEGER PRIMARY KEY,
  slug TEXT,
  title TEXT,
  tags TEXT,
  content TEXT,
  keywords TEXT
);
```

Все текстовые поля индексируются в нижнем регистре. Запросы используют `LIKE ?` с подстановочными `%`.
