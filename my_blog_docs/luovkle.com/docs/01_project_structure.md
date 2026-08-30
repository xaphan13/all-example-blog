# Карта проекта

## Назначение

`luovkle.com` — персональный блог и портфолио разработчика. Приложение отображает статьи (`revelations`) и проекты, хранящиеся в виде Markdown-файлов в директории `content/`, в сгенерированном HTML для браузеров и ANSI-арт для CLI-клиентов (`curl`, `httpie`, `wget`).

Репозиторий объединяет Python/FastAPI-бэкенд, сборку CSS через Tailwind, многостадийную контейнеризацию и вспомогательные CLI-скрипты для обработки изображений. Содержимое статично и не требует базы данных: контент индексируется из файловой системы при старте и кэшируется в памяти.

## Дерево директорий и ключевые файлы

```text
.
├── app/                          # Исходный код FastAPI-приложения
│   ├── main.py                   # Точка входа: создание FastAPI, роутер, статика, обработчики исключений
│   ├── config.py                 # Пути к контенту, статике, ANSI-артам и шаблоны имён файлов
│   ├── schemas.py                # Pydantic-модели: метаданные, посты, проекты, URL обложек, ANSI-контент
│   ├── types.py                  # TypedDict для внутренних словарей (TemplateArgsDict, ANSIContent и др.)
│   ├── services/                 # Сервисный слой: загрузка и преобразование контента
│   │   ├── common.py             # Утилиты: чтение Markdown/YAML, копирование изображений, слаги, время чтения
│   │   ├── html.py               # Построение HTML-контекста: парсинг Markdown, обогащение HTML, выбор обложек
│   │   └── ansi.py               # Построение ANSI-контекста: рендер Markdown в ANSI-арт, обёртки текста
│   ├── views/                    # Слой представлений FastAPI
│   │   ├── routes.py             # Маршруты, lifespan, HTML/ANSI-ответы, обработчики ошибок
│   │   ├── deps.py               # Зависимость FastAPI: определение CLI-клиента по User-Agent
│   │   └── utils.py              # Шаблоны ANSI-вывода и рендер Jinja2 в PlainTextResponse
│   ├── templates/                # Jinja2-шаблоны
│   │   ├── layout/base.html      # Базовый макет страницы, SEO-метатеги, подключение стилей
│   │   ├── includes/             # Переиспользуемые макросы (meta, thumbnail)
│   │   ├── homepage.html         # Главная страница
│   │   ├── post_list.html        # Список статей
│   │   ├── post_detail.html      # Детальная страница статьи
│   │   ├── project_list.html     # Список проектов
│   │   ├── project_detail.html   # Детальная страница проекта
│   │   ├── author.html           # Страница автора
│   │   ├── 404.html              # Страница не найдена
│   │   └── 500.html              # Страница внутренней ошибки
│   ├── assets/input.css          # Входной файл Tailwind (`@import "tailwindcss"`)
│   └── static/                   # Статические активы
│       ├── icons/                # Favicon
│       └── images/               # Обложки, thumbnails, изображения контента
├── cli/                          # Вспомогательные CLI-утилиты
│   ├── config.py                 # Пути для CLI-скриптов
│   ├── common.py                 # Утилиты: поиск изображений, пути вывода, пул потоков
│   ├── convert_images.py         # Конвертация PNG/JPEG в WebP/AVIF
│   └── img_to_ansi.py            # Генерация ANSI-артов из обложек
├── content/                      # Источник контента
│   ├── author/index.md           # Данные автора
│   ├── author/picture.jpeg       # Фото автора
│   ├── homepage.md               # Описания секций главной
│   ├── meta.md                   # SEO/Social Media метаданные сайта
│   ├── posts/                    # Статьи (поддиректории с index.md + images/)
│   └── projects/                 # Проекты (поддиректории с index.md + images/)
├── caddy/                        # Конфигурация Caddy
│   ├── Caddyfile                 # Маршрутизация HTTPS и статики
│   ├── Containerfile.local       # Локальный Caddy-контейнер с http://localhost
│   └── Containerfile.prod        # Продовский Caddy-контейнер
├── scripts/
│   ├── format.sh                 # Запуск ruff, djlint --reformat
│   └── lint.sh                   # Запуск ty, ruff, djlint check/lint
├── Containerfile                 # Многостадийная сборка приложения
├── compose.dev.yaml              # Dev-окружение с hot-reload CSS и приложения
├── compose.stage.yaml            # Stage-окружение, hardened
├── compose.prod.yaml             # Prod-окружение с предварительно собранным образом
├── Makefile                      # Цели для запуска окружений, локальной разработки, обработки изображений
├── pyproject.toml                # Python-зависимости и инструменты
├── package.json                  # Tailwind-скрипты и devDependencies
└── pnpm-workspace.yaml           # pnpm: разрешение сборки @parcel/watcher
```

## Внешние зависимости и их роль

| Зависимость | Роль в проекте |
|-------------|----------------|
| `FastAPI` (`fastapi[standard-no-fastapi-cloud-cli]`) | Веб-фреймворк: роутинг, зависимости, lifespan, статика, HTTP-исключения. Запуск через `fastapi dev`/`run`. |
| `pydantic` | Валидация схем в `app/schemas.py`, сериализация метаданных, OpenGraph/Twitter. |
| `markdown` | Преобразование Markdown-тел в HTML с расширениями `fenced_code` и `codehilite`. |
| `Pygments` | Подсветка синтаксиса в блоках кода; генерация `highlight.css` через `pygmentize`. |
| `beautifulsoup4` | Постобработка HTML из Markdown: перезапись `src` изображений, навешивание Tailwind-классов, поиск `<code>`. |
| `PyYAML` | Парсинг YAML-фронтматтера в Markdown-файлах (`load_generic_markdown_content`). |
| `rich` | Рендеринг Markdown в ANSI-арт для CLI-клиентов (`render_markdown_to_ansi`). |
| `Pillow` | Конвертация изображений в WebP/AVIF и ресайз для ANSI-генерации. |
| `Tailwind CSS` / `@tailwindcss/cli` | Генерация `app/static/css/styles.css` из `app/assets/input.css`. |
| `Caddy` | Обратный прокси и раздача статики в stage/prod; TLS, сжатие, заголовки безопасности. |
| `Podman` / `podman-compose` | Среда контейнеризации и оркестрации, используемая в `Makefile` и compose-файлах. |

## Исключённые из репозитория артефакты

- `app/static/css/styles.css`, `app/static/css/highlight.css` — генерируются при сборке.
- `app/static/images/author/`, `app/static/images/posts/`, `app/static/images/projects/` — копируются/генерируются из `content/`.
- `app/static/**/*.webp`, `app/static/**/*.avif` — производные форматы.
- `app/ansi/` — ANSI-арт обложек.
- `.venv/`, `node_modules/`, `.cache/` — локальные окружения.
