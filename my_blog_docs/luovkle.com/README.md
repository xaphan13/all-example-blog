<div align="center">
  <h1>⚗️ luovkle.com</h1>
  <p><i>Software blog made with ❤️ by a software engineer</i></p>
</div>

---

- **URL**: <a href="https://luovkle.com" target="_blank">luovkle.com</a>
- **Source Code**: <a href="https://github.com/luovkle/luovkle.com" target="_blank">https://github.com/luovkle/luovkle.com</a>

---

## 🧐 Что это такое

`luovkle.com` — персональный блог и портфолио разработчика. Это **монолитный серверно-рендеринговый сайт (SSR-like) на FastAPI без базы данных**: весь контент хранится в Markdown-файлах в директории `content/`, индексируется из файловой системы при старте приложения и кэшируется в памяти.

Главная особенность — **двойной формат ответа** в зависимости от клиента:

| Клиент | Формат | Технологии |
|--------|--------|------------|
| Браузер | `text/html` | Python `markdown` + `BeautifulSoup` + Jinja2 + Tailwind CSS |
| CLI (`curl`, `httpie`, `wget`) | `text/plain` | Python `rich` (Markdown → ANSI) + Jinja2 ANSI-шаблоны |

Попробуйте: `curl https://luovkle.com/p` — и вы увидите блог прямо в терминале. 🖥️

## ✨ Возможности

- 📝 Статьи (`/p`) и проекты (`/pr`) на Markdown с YAML-фронтматтером
- 🎨 Серверный рендеринг HTML через Jinja2 + Tailwind CSS
- 🖥️ ANSI-арт версии страниц для CLI-клиентов (определяется по `User-Agent`)
- 🖼️ Автоматическая конвертация изображений в WebP/AVIF и генерация ANSI-артов обложек
- 🔍 SEO/OpenGraph/Twitter-метаданные из `content/meta.md`
- ⚡ In-memory кэш контента: eager-загрузка при старте, нулевые затраты на парсинг при запросах
- 🔒 Hardened-контейнеры: read-only rootfs, `cap_drop: ALL`, `no-new-privileges`, nonroot-пользователь
- 🚢 Caddy как reverse proxy: TLS, сжатие, раздача статики, очистка заголовков `Server`/`Via`

## 📌 Requirements

Make sure you have the following tools installed:

- 🐳 <a href="https://podman.io/" target="_blank">**Podman**</a> - Container engine.
- 🚢 <a href="https://docs.podman.io/en/latest/markdown/podman-compose.1.html" target="_blank">**podman-compose**</a> - Compose-compatible tool for Podman.
- 🛠️ <a href="https://www.gnu.org/software/make/" target="_blank">**GNU Make**</a> - Command runner used by this project.
- 🌱 <a href="https://git-scm.com/" target="_blank">**Git**</a> - Version control system.

Для локальной разработки без контейнеров дополнительно:

- 🐍 **Python 3.13+**
- 📦 <a href="https://docs.astral.sh/uv/" target="_blank">**uv**</a> - Python dependency manager.
- 🎁 <a href="https://pnpm.io/" target="_blank">**pnpm**</a> - Node.js package manager.

## 🚀 Run it locally

Running this project locally is as simple as cloning the repository and starting the Podman containers.

> **Note:** Docker compatibility is currently in progress.

### Clone the repository

```bash
git clone git@github.com:luovkle/luovkle.com.git
cd luovkle.com
```

### Run the containers

To start the containers, run the `make` command followed by the name of the environment you want to use.

Currently, the available environments are `dev`, `stage`, and `prod`:

| Среда | Запуск | Остановка | Особенности |
|-------|--------|-----------|-------------|
| `dev` | `make dev` | `make dev-stop` | Hot-reload приложения и CSS, Caddy на `:80`, `www` на `:4000` |
| `stage` | `make stage` | `make stage-stop` | Продакшн-сборка, hardened-контейнеры, Caddy reverse proxy |
| `prod` | `make prod` | `make prod-stop` | Использует предварительно собранные образы `localhost/luovklecom_*` |

> **Note:** Before starting any environment, make sure the required ports are available: `dev` uses ports `80` and `4000`, while `stage` and `prod` use ports `80` and `443`.

For example, to start the staging environment:

```bash
make stage
```

Once the containers are running, open `http://localhost` in your browser.

### Локальная разработка без контейнеров

```bash
make setup      # uv sync + pnpm install + pre-commit хуки
make local-dev  # сборка всех артефактов + fastapi dev (hot-reload) на :4000
```

После этого сервер доступен на `http://localhost:4000` (порт переопределяется: `make local-dev PORT=8000`).

Подробнее — в [docs/local-development.md](docs/local-development.md).

## 🗂️ Структура проекта

```text
.
├── app/                  # FastAPI-приложение
│   ├── main.py           # Точка входа: приложение, роутер, статика, обработчики ошибок
│   ├── config.py         # Пути к контенту, статике, ANSI-артам
│   ├── schemas.py        # Pydantic-модели (метаданные, посты, проекты)
│   ├── services/         # Сервисный слой: загрузка и преобразование контента (html/ansi)
│   ├── views/            # Маршруты, зависимости, ANSI-шаблоны
│   ├── templates/        # Jinja2-шаблоны
│   ├── assets/input.css  # Входной файл Tailwind
│   └── static/           # Сгенерированные CSS и изображения
├── cli/                  # CLI-утилиты: конвертация изображений, генерация ANSI-артов
├── content/              # Источник контента (Markdown + YAML-фронтматтер)
│   ├── author/           # Данные автора
│   ├── posts/            # Статьи: <slug>/index.md + images/
│   └── projects/         # Проекты: <slug>/index.md + images/
├── caddy/                # Конфигурация Caddy (Caddyfile, Containerfile'ы)
├── scripts/              # format.sh / lint.sh
├── docs/                 # 📚 Подробная документация по проекту (см. ниже)
├── Containerfile         # Многостадийная сборка приложения
├── compose.{dev,stage,prod}.yaml
└── Makefile
```

## 🛣️ Маршруты

| Метод | Путь | Назначение |
|-------|------|------------|
| `GET` | `/` | Главная страница |
| `GET` | `/p` | Список статей (ANSI для CLI) |
| `GET` | `/p/{slug}` | Статья (ANSI для CLI) |
| `GET` | `/pr` | Список проектов (ANSI для CLI) |
| `GET` | `/pr/{slug}` | Проект (ANSI для CLI) |
| `GET` | `/author` | Страница автора |
| `HEAD` | `/health` | Healthcheck, `204 No Content` |

## ✍️ Как добавить статью или проект

1. Создайте директорию `content/posts/<my-slug>/` или `content/projects/<my-slug>/`.
2. Добавьте `index.md` с YAML-фронтматтером (для постов обязательно `title`; для проектов — `title`) и Markdown-телом:

   ```markdown
   ---
   title: "Моя статья"
   description: "Краткое описание"
   topic: "python"
   ---

   Текст статьи...
   ```

3. При необходимости добавьте изображения в `<dir>/images/`.
4. Перезапустите приложение (`make dev-stop && make dev`) — кэш контента in-memory инвалидируется только рестартом процесса.

## 🔧 Полезные Make-цели

| Команда | Назначение |
|---------|-----------|
| `make setup` | Установка окружения (uv, pnpm, pre-commit) |
| `make local-dev` / `make local-prod` | Запуск сервера без контейнеров |
| `make local-styles` | Watcher Tailwind CSS |
| `make images-optimize` | PNG/JPEG → WebP/AVIF |
| `make images-ansi` | PNG-обложки → ANSI-арт |
| `make format` | Форматирование (ruff, djlint) |
| `make lint` | Линтинг (ty, ruff, djlint) |
| `make check` | Pre-commit хуки на всех файлах |
| `make clean` / `make fclean` / `make re` | Очистка артефактов / окружения / полный ресет |

## 📚 Документация

Подробная документация по проекту находится в директории [`docs/`](docs/) — настоятельно рекомендуется к прочтению перед внесением изменений:

| Документ | Содержание |
|----------|-----------|
| [01_project_structure.md](docs/01_project_structure.md) | Карта проекта: дерево директорий, роли зависимостей, генерируемые артефакты |
| [02_architecture.md](docs/02_architecture.md) | Архитектура, паттерны проектирования, поток данных, кэширование |
| [03_execution_flow.md](docs/03_execution_flow.md) | Жизненный цикл приложения, роутинг, обработка ошибок, безопасность |
| [04_data_model_and_content.md](docs/04_data_model_and_content.md) | Pydantic-модели, формат Markdown-контента и фронтматтера |
| [05_deployment_and_operations.md](docs/05_deployment_and_operations.md) | Среды развёртывания, многостадийная сборка, операционные процедуры |
| [05_markdown_rendering_report.md](docs/05_markdown_rendering_report.md) | Отчёт: как рендерится Markdown (сервер vs клиент) |
| [06_memory_analysis_and_optimization.md](docs/06_memory_analysis_and_optimization.md) | Анализ потребления памяти и варианты оптимизации |
| [local-development.md](docs/local-development.md) | Локальная разработка без контейнеров, разбор Makefile и stamp-механики |

## 📄 License

The content of this project is licensed under the <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank">Creative Commons Attribution 4.0 International License</a>, while the source code used to build, format, and display that content is licensed under the <a href="https://opensource.org/license/mit/" target="_blank">MIT License</a>.
