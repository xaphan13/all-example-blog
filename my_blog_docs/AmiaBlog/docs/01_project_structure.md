# AmiaBlog: карта проекта

## Назначение

AmiaBlog — это легковесная блоговая система на Python 3.11+, построенная на FastAPI и Material Design You (MDUI v2). Проект ориентирован на простоту развертывания: контент хранится в Markdown-файлах с YAML frontmatter, поиск выполняется в памяти на SQLite, интерфейс рендерится серверными Jinja2-шаблонами, а Markdown превращается в HTML в браузере с помощью `markdown-it`. Поддерживаются динамический режим (Uvicorn/Gunicorn), горячая перезагрузка постов и генерация статического сайта.

## Дерево директорий

```
AmiaBlog/
├── config.json              # единый файл конфигурации
├── main.py                  # точка входа FastAPI и HTTP-маршруты
├── staticify.py             # CLI-генератор статического сайта
├── pyproject.toml           # метаданные и зависимости UV
├── uv.lock                  # lock-файл зависимостей
├── core/                    # прикладная логика
│   ├── __init__.py          # публичные экспорты модулей
│   ├── models.py            # Pydantic-модели и загрузка конфига
│   ├── posts.py             # PostsManager: парсинг, индексы, поиск, watchdog
│   ├── template.py          # TemplateRenderer: Jinja2 + htmlmin
│   ├── i18n.py              # I18nProvider: JSON-переводы
│   ├── hljs.py              # HLJSLanguageManager: бандлы подсветки кода
│   ├── rss.py               # RSSProvider: генерация /feed
│   ├── sitemap.py           # SitemapProvider: генерация /sitemap.xml
│   ├── live_preview.py      # LivePreviewManager: WebSocket-dev-режим
│   ├── system.py            # утилиты версии, коммита и платформы
│   └── utils.py             # проверки миграций
├── templates/               # Jinja2-шаблоны
├── static/                  # статические активы (MDUI, hljs, шрифты, JS)
├── data/
│   ├── posts/               # Markdown-файлы постов
│   └── attachments/         # прикрепленные файлы
├── languages/               # JSON-файлы переводов
├── docs/                    # документация проекта
└── .github/workflows/       # CI: black, pyright
```

## Описание ключевых файлов и модулей

| Путь | Ответственность |
|---|---|
| `main.py` | Создает `FastAPI`, регистрирует маршруты и lifespan, монтирует статику, инициализирует модули уровня приложения. |
| `staticify.py` | Самостоятельный CLI-скрипт (`AmiaBlogStaticGenerator`), который повторно использует ядро для записи HTML-файлов, RSS и sitemap на диск. |
| `config.json` | Единственный источник конфигурации: настройки сайта, язык, поиск, copyright, дружественные ссылки, аналитика. |
| `pyproject.toml` | Метаданные проекта, зависимости и dev-инструменты (Black, Pyright, pre-commit). |
| `uv.lock` | Зафиксированный граф зависимостей, управляемый UV. |
| `core/__init__.py` | Экспортирует публичные классы и функции для `main.py` и `staticify.py`. |
| `core/models.py` | Pydantic-модели: `Config`, `SiteSettings`, `PostMetadata`, `Post`, `Tag`; функция `load_config()` читает и валидирует `config.json`. |
| `core/posts.py` | `PostsManager` — загрузка и парсинг постов, построение индекса тегов, in-memory SQLite-поиск, watchdog-наблюдение за `data/posts/`. |
| `core/template.py` | `TemplateRenderer` — обертка над Jinja2 с кэшем шаблонов и минификацией вывода через `htmlmin`. |
| `core/i18n.py` | `I18nProvider` и `I18nTerm` — загрузка JSON-переводов из `languages/` и доступ к терминам через атрибуты. |
| `core/hljs.py` | `HLJSLanguageManager` — определяет языки в Markdown-блоках кода и скачивает недостающие бандлы highlight.js с CDN. |
| `core/rss.py` | `RSSProvider` — генерирует RSS 2.0 ленту с `content:encoded` и категориями. |
| `core/sitemap.py` | `SitemapProvider` — генерирует `sitemap.xml` для постов, тегов и топ-страниц. |
| `core/live_preview.py` | `LivePreviewManager` — WebSocket-маршрут для разработки; рассылает обновления Markdown при изменении файла. |
| `core/system.py` | Вспомогательные функции: `get_amiablog_version`, `get_commit_hash`, `get_platform_string`. |
| `core/utils.py` | `check_attachment_migration()` — проверяет, что вложения перенесены из `attachments/` в `data/attachments/`. |
| `templates/base.html` | Базовый шаблон: MDUI-навигация, тема, подключение статики, диалог «О сайте». |
| `templates/post.html` | Страница поста; инициирует клиентский рендер `markdown-it` и подключает highlight.js. |
| `templates/search.html` | Форма и результаты поиска. |
| `static/live_preview.js` | Клиент WebSocket для live-preview. |
| `data/posts/*.md` | Источник данных; slug образуется из имени файла. |
| `data/attachments/` | Статические файлы, доступные по `/attachments/<filename>`. |

## Внешние зависимости и их роль

| Зависимость | Роль |
|---|---|
| `fastapi` / `uvicorn` | Веб-фреймворк и ASGI-сервер. FastAPI здесь используется преимущественно как маршрутизатор и инжектор запросов. |
| `jinja2` | Серверный рендеринг HTML-шаблонов. |
| `htmlmin` | Минификация сгенерированного HTML перед отправкой клиенту. |
| `pydantic` | Валидация конфигурации и метаданных постов (Pydantic v2). |
| `pyyaml` | Парсинг YAML-frontmatter в Markdown-файлах. |
| `watchdog` | Файловое наблюдение и горячая перезагрузка постов. |
| `sqlite3` (stdlib) | In-memory поисковый индекс и LIKE-запросы. |
| `jieba-fast` | Сегментация китайского/английского текста для fuzzy-поиска. |
| `httpx` | Скачивание бандлов highlight.js с CDN. |
| `websockets` | Транспорт WebSocket для live-preview. |
| `loguru` | Структурированное логирование. |
| `black`, `pyright`, `pre-commit` (dev) | Форматирование, статическая типизация, pre-commit хуки. |
